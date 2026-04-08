"""
Public Share Permalink API

POST /api/share/<simulation_id>  — create a share token for a simulation
GET  /api/share/<token>          — fetch public simulation data by token
"""

import os
import json
import secrets
import string
import sqlite3
from datetime import datetime
from flask import jsonify

from . import share_bp
from ..config import Config
from ..services.simulation_manager import SimulationManager
from ..services.simulation_runner import SimulationRunner
from ..utils.logger import get_logger

logger = get_logger('miroshark.api.share')

# Global shares index: token → {simulation_id, created_at, view_count}
SHARES_FILE = os.path.join(Config.UPLOAD_FOLDER, 'shares.json')
_TOKEN_LENGTH = 8
_TOKEN_ALPHABET = string.ascii_letters + string.digits


def _load_shares() -> dict:
    if not os.path.exists(SHARES_FILE):
        return {}
    try:
        with open(SHARES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_shares(shares: dict) -> None:
    os.makedirs(os.path.dirname(SHARES_FILE), exist_ok=True)
    with open(SHARES_FILE, 'w', encoding='utf-8') as f:
        json.dump(shares, f, indent=2, ensure_ascii=False)


def _generate_token() -> str:
    return ''.join(secrets.choice(_TOKEN_ALPHABET) for _ in range(_TOKEN_LENGTH))


@share_bp.route('/<simulation_id>', methods=['POST'])
def create_share(simulation_id: str):
    """
    Create a public share link for a simulation.

    If the simulation already has a share token, the existing token is returned.

    Returns:
        {
            "success": true,
            "data": { "token": "abc123XY", "share_url": "/share/abc123XY", "reused": false }
        }
    """
    try:
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if not state:
            return jsonify({"success": False, "error": f"Simulation not found: {simulation_id}"}), 404

        shares = _load_shares()

        # Reuse existing token for this simulation if one exists
        for token, meta in shares.items():
            if meta.get("simulation_id") == simulation_id:
                return jsonify({
                    "success": True,
                    "data": {
                        "token": token,
                        "share_url": f"/share/{token}",
                        "reused": True
                    }
                })

        # Generate a unique token
        token = _generate_token()
        while token in shares:
            token = _generate_token()

        shares[token] = {
            "simulation_id": simulation_id,
            "created_at": datetime.utcnow().isoformat(),
            "view_count": 0
        }
        _save_shares(shares)

        logger.info(f"Share token created: {token} → {simulation_id}")

        return jsonify({
            "success": True,
            "data": {
                "token": token,
                "share_url": f"/share/{token}",
                "reused": False
            }
        })

    except Exception as e:
        logger.error(f"Failed to create share: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@share_bp.route('/<token>', methods=['GET'])
def get_share(token: str):
    """
    Fetch public simulation data for a share token.

    Returns public-safe simulation outputs — no agent persona details.

    Returns:
        {
            "success": true,
            "data": {
                "token": "abc123XY",
                "simulation_id": "sim_abc123",
                "simulation_requirement": "Scenario description...",
                "agent_count": 50,
                "total_rounds": 24,
                "current_round": 24,
                "status": "completed",
                "created_at": "...",
                "share_created_at": "...",
                "view_count": 5,
                "timeline": [...],
                "influence": [...],
                "markets": [...]
            }
        }
    """
    try:
        shares = _load_shares()
        meta = shares.get(token)
        if not meta:
            return jsonify({"success": False, "error": "Share link not found"}), 404

        simulation_id = meta["simulation_id"]

        # Increment view count
        meta["view_count"] = meta.get("view_count", 0) + 1
        _save_shares(shares)

        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if not state:
            return jsonify({"success": False, "error": "Simulation no longer exists"}), 404

        # Scenario description from simulation config
        sim_config = manager.get_simulation_config(simulation_id)
        simulation_requirement = ""
        total_rounds_configured = 0
        if sim_config:
            simulation_requirement = sim_config.get("simulation_requirement", "")
            time_cfg = sim_config.get("time_config", {})
            total_rounds_configured = int(
                time_cfg.get("total_simulation_hours", 0) * 60
                / max(time_cfg.get("minutes_per_round", 60), 1)
            )

        # Run state (rounds completed)
        run_state = SimulationRunner.get_run_state(simulation_id)
        current_round = run_state.current_round if run_state else 0
        total_rounds = (
            run_state.total_rounds
            if run_state and run_state.total_rounds > 0
            else total_rounds_configured
        )

        # Timeline — first 50 rounds
        try:
            timeline = SimulationRunner.get_timeline(simulation_id)[:50]
        except Exception:
            timeline = []

        # Influence leaderboard — top 5 agents
        try:
            from .simulation import _compute_influence_ranked
            influence = _compute_influence_ranked(simulation_id, top_n=5)
        except Exception:
            influence = []

        # Polymarket prices
        markets = []
        try:
            sim_dir = os.path.join(Config.WONDERWALL_SIMULATION_DATA_DIR, simulation_id)
            db_path = os.path.join(sim_dir, 'polymarket', 'polymarket.db')
            if os.path.exists(db_path):
                con = sqlite3.connect(db_path)
                cur = con.cursor()
                tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if 'price_history' in tables:
                    rows = cur.execute(
                        "SELECT round_num, market_id, price_yes FROM price_history ORDER BY round_num, market_id"
                    ).fetchall()
                    markets = [{"round_num": rn, "market_id": mid, "price_yes": py} for rn, mid, py in rows]
                elif 'market' in tables:
                    rows = cur.execute("SELECT id, reserve_yes, reserve_no FROM market").fetchall()
                    for mid, ry, rn_reserve in rows:
                        total_liq = (ry or 0) + (rn_reserve or 0)
                        price_yes = (rn_reserve / total_liq) if total_liq > 0 else 0.5
                        markets.append({"market_id": mid, "price_yes": round(price_yes, 4), "round_num": None})
                con.close()
        except Exception:
            pass

        return jsonify({
            "success": True,
            "data": {
                "token": token,
                "simulation_id": simulation_id,
                "simulation_requirement": simulation_requirement,
                "agent_count": state.profiles_count,
                "total_rounds": total_rounds,
                "current_round": current_round,
                "status": state.status.value,
                "created_at": state.created_at,
                "share_created_at": meta["created_at"],
                "view_count": meta["view_count"],
                "timeline": timeline,
                "influence": influence,
                "markets": markets
            }
        })

    except Exception as e:
        logger.error(f"Failed to fetch share {token}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
