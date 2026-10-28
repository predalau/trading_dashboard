<template>
  <div class="flex flex-col gap-5">
    <h1 class="sr-only">Backtest</h1>

    <TermPanel title="backtest.sh" tone="surface">
      <form @submit.prevent="run" class="flex flex-col gap-3">
        <div class="flex flex-wrap gap-3">
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">--strategy</span>
            <select v-model="form.module" class="t-input min-w-[200px]">
              <option value="strategies.sma_cross">strategies.sma_cross</option>
              <option v-for="s in strategies" :key="s.slug" :value="s.module">{{ s.slug }} ({{ s.module }})</option>
            </select>
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">--symbol</span>
            <select v-model="form.symbol" class="t-input">
              <option v-for="s in symbols" :key="s" :value="s">{{ s }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">--timeframe</span>
            <select v-model="form.timeframe" class="t-input">
              <option v-for="t in timeframes" :key="t" :value="t">{{ t }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">--lookback (bars)</span>
            <input v-model.number="form.lookback" type="number" min="50" max="1000" class="t-input w-32" />
          </label>
        </div>
        <label class="flex flex-col gap-1">
          <span class="text-muted text-xs">--params (JSON)</span>
          <input v-model="form.paramsText" class="t-input" placeholder='{"fast": 10, "slow": 30}' />
        </label>
        <div class="flex items-center gap-3">
          <button type="submit" class="t-btn justify-start py-3" :disabled="running">
            {{ running ? '$ running backtest...' : '$ ./backtest --run ⏎' }}
          </button>
          <span v-if="error" class="text-down text-xs">{{ error }}</span>
        </div>
      </form>
    </TermPanel>

    <TermPanel v-if="result" title="result">
      <template #meta>
        <span :class="result.metrics.total_return >= 0 ? 'text-up' : 'text-down'">
          {{ pct(result.metrics.total_return) }}
        </span>
      </template>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div v-for="m in metricCards" :key="m.label" class="bg-term-surface border border-term-line p-3">
            <div class="text-muted text-[11px] uppercase tracking-[0.12em]">{{ m.label }}</div>
            <div class="mt-1 text-lg font-bold" :class="m.class">{{ m.value }}</div>
          </div>
        </div>

        <!-- Equity curve -->
        <svg v-if="curvePoints" :viewBox="`0 0 ${W} ${H}`" class="w-full border border-term-line bg-term-surface" preserveAspectRatio="none" style="height:160px">
          <polyline :points="curvePoints" fill="none" :stroke="result.metrics.total_return >= 0 ? 'var(--up, #3fb950)' : 'var(--down, #f85149)'" stroke-width="1.5" />
        </svg>
        <div class="text-muted text-xs">
          backtest #{{ result.id }} · {{ result.bars }} bars · {{ result.metrics.num_trades }} trades ·
          buy&amp;hold {{ pct(result.metrics.buy_hold_return) }}
        </div>
      </div>
    </TermPanel>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import TermPanel from '../components/term/TermPanel.vue'

const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
const timeframes = ['15m', '1h', '4h', '1d']

const W = 600
const H = 160

const strategies = ref([])
const running = ref(false)
const error = ref('')
const result = ref(null)

const form = ref({
  module: 'strategies.sma_cross',
  symbol: 'BTCUSDT',
  timeframe: '1h',
  lookback: 500,
  paramsText: '{"fast": 10, "slow": 30}',
})

const pct = (x) => (x == null ? '--' : (x >= 0 ? '+' : '') + (x * 100).toFixed(2) + '%')

const metricCards = computed(() => {
  if (!result.value) return []
  const m = result.value.metrics
  return [
    { label: 'total return', value: pct(m.total_return), class: m.total_return >= 0 ? 'text-up' : 'text-down' },
    { label: 'max drawdown', value: pct(m.max_drawdown), class: 'text-down' },
    { label: 'sharpe', value: m.sharpe.toFixed(2), class: '' },
    { label: 'win rate', value: (m.win_rate * 100).toFixed(0) + '%', class: '' },
  ]
})

const curvePoints = computed(() => {
  const curve = result.value?.equity_curve
  if (!curve || curve.length < 2) return null
  const eqs = curve.map((p) => p.equity)
  const min = Math.min(...eqs)
  const max = Math.max(...eqs)
  const range = max - min || 1
  return eqs
    .map((e, i) => {
      const x = (i / (eqs.length - 1)) * W
      const y = H - ((e - min) / range) * (H - 8) - 4
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
})

const fetchStrategies = async () => {
  try {
    const r = await fetch('/trading/api/v1/backtest/strategies')
    if (r.ok) strategies.value = await r.json()
  } catch (e) { /* ignore */ }
}

const run = async () => {
  error.value = ''
  let params
  try {
    params = JSON.parse(form.value.paramsText || '{}')
  } catch (e) {
    error.value = 'params is not valid JSON'
    return
  }
  running.value = true
  result.value = null
  try {
    const runRes = await fetch('/trading/api/v1/backtest/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        module: form.value.module,
        symbol: form.value.symbol,
        timeframe: form.value.timeframe,
        lookback: form.value.lookback,
        params,
      }),
    })
    const body = await runRes.json()
    if (!runRes.ok) throw new Error(body.detail || `HTTP ${runRes.status}`)
    // fetch full record (with equity curve)
    const full = await fetch(`/trading/api/v1/backtest/${body.id}`)
    result.value = await full.json()
    result.value.bars = body.bars
  } catch (e) {
    error.value = e.message
  } finally {
    running.value = false
  }
}

onMounted(fetchStrategies)
</script>
