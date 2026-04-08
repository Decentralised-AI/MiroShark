<template>
  <div class="share-page">
    <!-- Header -->
    <header class="share-header">
      <div class="brand" @click="router.push('/')">MIROSHARK</div>
      <div class="header-tag">SHARED SIMULATION</div>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="state-panel">
      <span class="loading-spinner"></span>
      <span class="state-text">Loading simulation...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="state-panel">
      <span class="error-icon">◇</span>
      <span class="state-text">{{ error }}</span>
      <button class="cta-btn" @click="router.push('/')">← Back to MiroShark</button>
    </div>

    <!-- Share Content -->
    <main v-else-if="data" class="share-content">
      <!-- Sim ID + meta strip -->
      <div class="sim-meta-strip">
        <span class="sim-id">{{ formatSimId(data.simulation_id) }}</span>
        <span class="sim-status" :class="data.status">● {{ data.status }}</span>
        <span class="sim-agents">{{ data.agent_count }} agents</span>
        <span class="sim-rounds">{{ data.current_round }}/{{ data.total_rounds }} rounds</span>
        <span class="sim-views">{{ data.view_count }} views</span>
      </div>

      <!-- Scenario Title -->
      <div class="scenario-card">
        <div class="card-label">SCENARIO</div>
        <p class="scenario-text">{{ data.simulation_requirement || 'No scenario description.' }}</p>
      </div>

      <!-- Stats Row -->
      <div class="stats-row">
        <div class="stat-box">
          <span class="stat-value">{{ data.agent_count }}</span>
          <span class="stat-label">AI AGENTS</span>
        </div>
        <div class="stat-box">
          <span class="stat-value">{{ data.current_round }}</span>
          <span class="stat-label">ROUNDS RUN</span>
        </div>
        <div class="stat-box">
          <span class="stat-value">{{ totalActions }}</span>
          <span class="stat-label">TOTAL EVENTS</span>
        </div>
        <div class="stat-box" v-if="data.markets && data.markets.length > 0">
          <span class="stat-value">{{ formatPrice(data.markets[0].price_yes) }}</span>
          <span class="stat-label">MARKET YES</span>
        </div>
      </div>

      <!-- Activity Chart -->
      <div v-if="data.timeline && data.timeline.length > 0" class="section-card">
        <div class="section-label">ROUND ACTIVITY</div>
        <div class="activity-chart">
          <div
            v-for="round in chartRounds"
            :key="round.round_num"
            class="chart-bar-col"
            :title="`Round ${round.round_num}: ${round.total_actions} events`"
          >
            <div
              class="chart-bar"
              :style="{ height: round.barHeight + '%' }"
            ></div>
          </div>
        </div>
        <div class="chart-axis">
          <span>Round 1</span>
          <span>Round {{ data.timeline.length }}</span>
        </div>
      </div>

      <!-- Influence Leaderboard -->
      <div v-if="data.influence && data.influence.length > 0" class="section-card">
        <div class="section-label">TOP AGENTS BY INFLUENCE</div>
        <div class="leaderboard">
          <div
            v-for="agent in data.influence"
            :key="agent.agent_name"
            class="leaderboard-row"
          >
            <span class="rank">#{{ agent.rank }}</span>
            <span class="agent-name">{{ agent.agent_name }}</span>
            <div class="agent-stats">
              <span class="agent-stat" title="Posts created">{{ agent.posts_created }} posts</span>
              <span class="agent-stat" title="Engagement received">{{ agent.engagement_received }} eng</span>
              <span class="agent-stat highlight" title="Influence score">{{ agent.influence_score }} pts</span>
            </div>
            <div class="score-bar-wrap">
              <div class="score-bar" :style="{ width: scoreBarWidth(agent.influence_score) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Market Prices (if available) -->
      <div v-if="data.markets && data.markets.length > 0" class="section-card">
        <div class="section-label">PREDICTION MARKET</div>
        <div class="market-grid">
          <div v-for="market in data.markets" :key="market.market_id" class="market-item">
            <div class="market-label">Market {{ market.market_id }}</div>
            <div class="price-bar-wrap">
              <div class="price-bar yes" :style="{ width: (market.price_yes * 100) + '%' }"></div>
              <div class="price-bar no" :style="{ width: ((1 - market.price_yes) * 100) + '%' }"></div>
            </div>
            <div class="price-labels">
              <span class="price-yes">YES {{ formatPrice(market.price_yes) }}</span>
              <span class="price-no">NO {{ formatPrice(1 - market.price_yes) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- CTA -->
      <div class="cta-section">
        <div class="cta-divider">
          <span class="divider-line"></span>
          <span class="divider-text">RUN YOUR OWN SIMULATION</span>
          <span class="divider-line"></span>
        </div>
        <p class="cta-desc">
          MiroShark is an open-source multi-agent simulation engine. Upload any document — a policy draft, press release, or research paper — and watch hundreds of AI agents react, debate, and trade in real time.
        </p>
        <a
          href="https://github.com/aaronjmars/MiroShark"
          target="_blank"
          rel="noopener noreferrer"
          class="cta-btn"
        >★ Star on GitHub →</a>
      </div>

      <!-- Footer -->
      <div class="share-footer">
        <span class="footer-brand">MIROSHARK</span>
        <span class="footer-sep">·</span>
        <span class="footer-info">Shared {{ formatDate(data.share_created_at) }}</span>
        <span class="footer-sep">·</span>
        <span class="footer-info">{{ formatSimId(data.simulation_id) }}</span>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getShare } from '../api/simulation'

const props = defineProps({
  token: String
})

const route = useRoute()
const router = useRouter()

const token = props.token || route.params.token
const loading = ref(true)
const error = ref(null)
const data = ref(null)

const totalActions = computed(() => {
  if (!data.value?.timeline) return 0
  return data.value.timeline.reduce((sum, r) => sum + (r.total_actions || 0), 0)
})

const chartRounds = computed(() => {
  if (!data.value?.timeline?.length) return []
  const rounds = data.value.timeline
  const maxActions = Math.max(...rounds.map(r => r.total_actions || 0), 1)
  return rounds.map(r => ({
    ...r,
    barHeight: Math.max(4, Math.round(((r.total_actions || 0) / maxActions) * 100))
  }))
})

const maxInfluenceScore = computed(() => {
  if (!data.value?.influence?.length) return 1
  return Math.max(...data.value.influence.map(a => a.influence_score || 0), 1)
})

const scoreBarWidth = (score) => {
  return Math.max(4, Math.round((score / maxInfluenceScore.value) * 100))
}

const formatSimId = (simId) => {
  if (!simId) return 'UNKNOWN'
  return 'SIM_' + simId.replace('sim_', '').slice(0, 6).toUpperCase()
}

const formatPrice = (price) => {
  if (price === null || price === undefined) return '—'
  return (price * 100).toFixed(1) + '%'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateStr.slice(0, 10)
  }
}

const setOpenGraphTags = (simData) => {
  const title = simData.simulation_requirement
    ? `MiroShark: ${simData.simulation_requirement.slice(0, 60)}${simData.simulation_requirement.length > 60 ? '...' : ''}`
    : 'MiroShark Simulation Results'
  const description = `${simData.agent_count} AI agents · ${simData.current_round} rounds · ${totalActions.value} events. Built with MiroShark open-source simulation engine.`

  document.title = title

  const setMeta = (property, content, useProperty = true) => {
    const selector = useProperty ? `meta[property="${property}"]` : `meta[name="${property}"]`
    let el = document.querySelector(selector)
    if (!el) {
      el = document.createElement('meta')
      if (useProperty) el.setAttribute('property', property)
      else el.setAttribute('name', property)
      document.head.appendChild(el)
    }
    el.setAttribute('content', content)
  }

  setMeta('og:title', title)
  setMeta('og:description', description)
  setMeta('og:type', 'website')
  setMeta('og:url', window.location.href)
  setMeta('twitter:card', 'summary', false)
  setMeta('twitter:title', title, false)
  setMeta('twitter:description', description, false)
}

onMounted(async () => {
  try {
    const resp = await getShare(token)
    if (resp.data.success) {
      data.value = resp.data.data
      setOpenGraphTags(data.value)
    } else {
      error.value = resp.data.error || 'Share link not found.'
    }
  } catch (err) {
    error.value = 'Failed to load shared simulation.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.share-page {
  min-height: 100vh;
  background: #FAFAFA;
  font-family: 'Space Mono', monospace;
  color: #0A0A0A;
}

/* Header */
.share-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 40px;
  border-bottom: 2px solid rgba(10, 10, 10, 0.08);
  background: #FAFAFA;
}

.brand {
  font-size: 1.1rem;
  font-weight: 700;
  letter-spacing: 4px;
  color: #0A0A0A;
  cursor: pointer;
}

.brand:hover {
  color: #FF6B1A;
}

.header-tag {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 3px;
  color: rgba(10, 10, 10, 0.4);
  padding: 4px 10px;
  border: 1px solid rgba(10, 10, 10, 0.12);
  text-transform: uppercase;
}

/* Loading / error states */
.state-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 40px;
  color: rgba(10, 10, 10, 0.4);
}

.loading-spinner {
  width: 28px;
  height: 28px;
  border: 2px solid rgba(10, 10, 10, 0.08);
  border-top-color: #FF6B1A;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 2rem;
  opacity: 0.4;
}

.state-text {
  font-size: 14px;
  letter-spacing: 1px;
}

/* Main content */
.share-content {
  max-width: 780px;
  margin: 0 auto;
  padding: 40px 24px 60px;
}

/* Sim meta strip */
.sim-meta-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: rgba(10, 10, 10, 0.4);
}

.sim-id {
  font-weight: 700;
  color: #0A0A0A;
  letter-spacing: 3px;
}

.sim-status {
  font-weight: 600;
  letter-spacing: 2px;
}

.sim-status.completed { color: #43C165; }
.sim-status.running { color: #FF6B1A; }
.sim-status.failed { color: #FF4444; }

/* Scenario card */
.scenario-card {
  background: #F5F5F5;
  border: 2px solid rgba(10, 10, 10, 0.08);
  padding: 20px 24px;
  margin-bottom: 24px;
  position: relative;
}

.scenario-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 14px;
  height: 14px;
  border-top: 2px solid #FF6B1A;
  border-left: 2px solid #FF6B1A;
}

.scenario-card::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 14px;
  height: 14px;
  border-bottom: 2px solid #43C165;
  border-right: 2px solid #43C165;
}

.card-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 3px;
  color: rgba(10, 10, 10, 0.4);
  margin-bottom: 10px;
  text-transform: uppercase;
}

.scenario-text {
  font-size: 15px;
  line-height: 1.6;
  color: #0A0A0A;
  margin: 0;
  font-family: 'Young Serif', serif;
}

/* Stats row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.stat-box {
  background: #F5F5F5;
  border: 1px solid rgba(10, 10, 10, 0.08);
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #FF6B1A;
  letter-spacing: -1px;
}

.stat-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 3px;
  color: rgba(10, 10, 10, 0.4);
  text-transform: uppercase;
}

/* Section cards */
.section-card {
  background: #F5F5F5;
  border: 1px solid rgba(10, 10, 10, 0.08);
  padding: 20px 24px;
  margin-bottom: 24px;
}

.section-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 3px;
  color: rgba(10, 10, 10, 0.4);
  margin-bottom: 16px;
  text-transform: uppercase;
}

/* Activity chart */
.activity-chart {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 80px;
  padding: 0 2px;
}

.chart-bar-col {
  flex: 1;
  display: flex;
  align-items: flex-end;
  height: 100%;
  min-width: 2px;
  cursor: default;
}

.chart-bar {
  width: 100%;
  background: #FF6B1A;
  opacity: 0.7;
  transition: opacity 0.15s ease;
  min-height: 2px;
}

.chart-bar-col:hover .chart-bar {
  opacity: 1;
}

.chart-axis {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 9px;
  letter-spacing: 2px;
  color: rgba(10, 10, 10, 0.3);
  text-transform: uppercase;
}

/* Leaderboard */
.leaderboard {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.leaderboard-row {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  grid-template-rows: auto auto;
  align-items: center;
  gap: 8px 12px;
  padding: 10px 12px;
  background: #FAFAFA;
  border: 1px solid rgba(10, 10, 10, 0.06);
}

.rank {
  font-size: 11px;
  font-weight: 700;
  color: #FF6B1A;
  letter-spacing: 1px;
  grid-row: 1;
  grid-column: 1;
}

.agent-name {
  font-size: 13px;
  font-weight: 600;
  color: #0A0A0A;
  letter-spacing: 1px;
  grid-row: 1;
  grid-column: 2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-stats {
  display: flex;
  gap: 10px;
  grid-row: 1;
  grid-column: 3;
}

.agent-stat {
  font-size: 10px;
  color: rgba(10, 10, 10, 0.4);
  letter-spacing: 1px;
}

.agent-stat.highlight {
  color: #43C165;
  font-weight: 700;
}

.score-bar-wrap {
  grid-row: 2;
  grid-column: 1 / -1;
  height: 3px;
  background: rgba(10, 10, 10, 0.06);
}

.score-bar {
  height: 100%;
  background: linear-gradient(90deg, #FF6B1A, #43C165);
  transition: width 0.4s ease;
}

/* Market prices */
.market-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.market-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.market-label {
  font-size: 10px;
  letter-spacing: 2px;
  color: rgba(10, 10, 10, 0.4);
  text-transform: uppercase;
}

.price-bar-wrap {
  display: flex;
  height: 10px;
  overflow: hidden;
  border: 1px solid rgba(10, 10, 10, 0.08);
}

.price-bar.yes {
  background: #43C165;
  transition: width 0.4s ease;
}

.price-bar.no {
  background: rgba(10, 10, 10, 0.12);
  transition: width 0.4s ease;
}

.price-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  letter-spacing: 2px;
}

.price-yes {
  color: #43C165;
  font-weight: 600;
}

.price-no {
  color: rgba(10, 10, 10, 0.4);
}

/* CTA section */
.cta-section {
  margin-top: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
}

.cta-divider {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 16px;
}

.divider-line {
  flex: 1;
  height: 7px;
  background: repeating-linear-gradient(-45deg, #FF6B1A, #FF6B1A 11px, #FAFAFA 11px, #FAFAFA 22px);
}

.divider-text {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 3px;
  color: rgba(10, 10, 10, 0.4);
  white-space: nowrap;
  text-transform: uppercase;
}

.cta-desc {
  font-size: 13px;
  line-height: 1.7;
  color: rgba(10, 10, 10, 0.5);
  max-width: 540px;
  margin: 0;
}

.cta-btn {
  display: inline-block;
  padding: 12px 28px;
  background: #0A0A0A;
  color: #FAFAFA;
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  text-decoration: none;
  border: 2px solid #0A0A0A;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cta-btn:hover {
  background: #FF6B1A;
  border-color: #FF6B1A;
}

/* Footer */
.share-footer {
  margin-top: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 10px;
  letter-spacing: 2px;
  color: rgba(10, 10, 10, 0.3);
  text-transform: uppercase;
  padding-top: 24px;
  border-top: 1px solid rgba(10, 10, 10, 0.08);
}

.footer-brand {
  font-weight: 700;
  color: rgba(10, 10, 10, 0.5);
}

.footer-sep {
  opacity: 0.4;
}

/* Responsive */
@media (max-width: 600px) {
  .share-content {
    padding: 24px 16px 48px;
  }
  .share-header {
    padding: 14px 20px;
  }
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .sim-meta-strip {
    gap: 10px;
  }
  .agent-stats {
    flex-direction: column;
    gap: 3px;
  }
}
</style>
