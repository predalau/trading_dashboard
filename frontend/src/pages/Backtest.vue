<template>
  <div class="flex flex-col gap-5">
    <h1 class="sr-only">Backtest</h1>

    <TermPanel title="backtest.sh" tone="surface">
      <form @submit.prevent="run" class="flex flex-col gap-3">
        <div class="flex flex-wrap gap-3">
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">--strategy</span>
            <select v-model="form.module" class="t-input min-w-[200px]">
              <option v-for="s in strategies" :key="s.module" :value="s.module">
                {{ s.name || s.slug }}{{ s.id == null ? ' (built-in)' : '' }}
              </option>
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

        <!-- Strategy parameters: auto-generated controls -->
        <div v-if="currentSpec.length" class="flex flex-col gap-2 border-t border-term-line pt-3">
          <span class="text-muted text-xs">--params</span>
          <p v-if="currentStrategy?.description" class="text-muted text-xs -mt-1">{{ currentStrategy.description }}</p>
          <div v-for="p in currentSpec" :key="p.name" class="flex items-center gap-3">
            <span class="text-xs w-24 shrink-0">{{ p.label || p.name }}</span>

            <button
              v-if="p.type === 'bool'"
              type="button"
              class="t-btn px-4 py-1.5"
              :class="form.params[p.name] ? '' : 't-btn-ghost'"
              @click="form.params[p.name] = !form.params[p.name]"
            >{{ form.params[p.name] ? 'on' : 'off' }}</button>

            <select
              v-else-if="p.type === 'choice'"
              v-model="form.params[p.name]"
              class="t-input"
            >
              <option v-for="c in (p.choices || [])" :key="c" :value="c">{{ c }}</option>
            </select>

            <template v-else-if="p.type === 'int' || p.type === 'float'">
              <input
                type="number"
                :min="p.min" :max="p.max" :step="p.step || 1"
                v-model.number="form.params[p.name]"
                class="t-input w-16 text-center shrink-0 px-1"
              />
              <input
                type="range"
                :min="p.min" :max="p.max" :step="p.step || 1"
                v-model.number="form.params[p.name]"
                class="param-slider flex-1 min-w-0"
              />
            </template>

            <input v-else v-model="form.params[p.name]" class="t-input flex-1" />
          </div>
        </div>

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

        <!-- Price chart with entry (BUY ▲) / exit (SELL ■) markers -->
        <div>
          <div class="text-muted text-[11px] uppercase tracking-[0.12em] mb-1">price · entries &amp; exits</div>
          <div class="border border-term-line bg-term-surface">
            <BacktestChart :bars="chartBars" :trades="result.trades || []" />
          </div>
        </div>

        <!-- Equity curve -->
        <div class="text-muted text-[11px] uppercase tracking-[0.12em]">equity curve</div>
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
import { ref, computed, watch, onMounted } from 'vue'
import TermPanel from '../components/term/TermPanel.vue'
import BacktestChart from '../components/BacktestChart.vue'

const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
const timeframes = ['15m', '1h', '4h', '1d']

const W = 600
const H = 160

const strategies = ref([])
const running = ref(false)
const error = ref('')
const result = ref(null)
const chartBars = ref([])

const form = ref({
  module: 'strategies.sma_cross',
  symbol: 'BTCUSDT',
  timeframe: '1h',
  lookback: 500,
  params: {},
})

const currentStrategy = computed(() =>
  strategies.value.find((s) => s.module === form.value.module) || null
)
const currentSpec = computed(() => currentStrategy.value?.param_spec || [])

// Seed the params object from the selected strategy's defaults
const resetParams = () => {
  const next = {}
  const defaults = currentStrategy.value?.params || {}
  for (const p of currentSpec.value) {
    next[p.name] = defaults[p.name] ?? p.default
  }
  form.value.params = next
}

watch(() => form.value.module, resetParams)

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
    if (r.ok) {
      strategies.value = await r.json()
      // default to sma_cross if present, else first strategy
      if (!currentStrategy.value && strategies.value.length) {
        form.value.module = (strategies.value.find((s) => s.module === 'strategies.sma_cross')
          || strategies.value[0]).module
      }
      resetParams()
    }
  } catch (e) { /* ignore */ }
}

const run = async () => {
  error.value = ''
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
        params: form.value.params,
      }),
    })
    const body = await runRes.json()
    if (!runRes.ok) throw new Error(body.detail || `HTTP ${runRes.status}`)
    // fetch full record (with equity curve + trades) and price bars for the chart
    const [full, ohlcv] = await Promise.all([
      fetch(`/trading/api/v1/backtest/${body.id}`).then(r => r.json()),
      fetch(`/trading/api/v1/backtest/${body.id}/ohlcv`).then(r => r.ok ? r.json() : { bars: [] }),
    ])
    result.value = full
    result.value.bars = body.bars
    chartBars.value = ohlcv.bars || []
  } catch (e) {
    error.value = e.message
  } finally {
    running.value = false
  }
}

onMounted(fetchStrategies)
</script>

<style scoped>
/* Visible, grabbable range slider */
.param-slider {
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  border-radius: 4px;
  background: var(--line, #30363d);
  cursor: pointer;
  outline: none;
}
.param-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent, #4fd6ff);
  border: 2px solid var(--surface, #0a0f15);
  cursor: grab;
}
.param-slider::-webkit-slider-thumb:active {
  cursor: grabbing;
}
.param-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent, #4fd6ff);
  border: 2px solid var(--surface, #0a0f15);
  cursor: grab;
}
.param-slider::-moz-range-track {
  height: 8px;
  border-radius: 4px;
  background: var(--line, #30363d);
}
</style>
