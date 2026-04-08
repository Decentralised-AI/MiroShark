"""
Thread-local trace context for correlating events across call stacks.

Usage:
    TraceContext.set(simulation_id="sim_abc", round_num=5, agent_id=3)
    # ... deep in the call stack, llm_client reads this automatically:
    sim_id = TraceContext.get("simulation_id")
    TraceContext.clear()
"""

import threading
import uuid

_context = threading.local()


class TraceContext:
    """Thread-local storage for correlation fields."""

    @staticmethod
    def set(**kwargs):
        """Set one or more context fields (simulation_id, round_num, agent_id, agent_name, platform, trace_id)."""
        for k, v in kwargs.items():
            setattr(_context, k, v)

    @staticmethod
    def get(key, default=None):
        """Read a context field."""
        return getattr(_context, key, default)

    @staticmethod
    def get_all():
        """Return all context fields as a dict."""
        return {k: v for k, v in _context.__dict__.items() if not k.startswith('_')}

    @staticmethod
    def new_trace():
        """Generate and set a new trace_id, returning it."""
        trace_id = f"trc_{uuid.uuid4().hex[:12]}"
        _context.trace_id = trace_id
        return trace_id

    @staticmethod
    def clear():
        """Remove all context fields."""
        _context.__dict__.clear()
