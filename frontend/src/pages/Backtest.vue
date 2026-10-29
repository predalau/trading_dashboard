<template>
  <div class="flex flex-col gap-5">
    <h1 class="sr-only">Backtest</h1>

    <TermPanel title="backtest.sh" tone="surface">
      <form @submit.prevent="run" class="flex flex-col gap-3">
        <div class="flex flex-wrap gap-3">
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">--strategy</span>
            <select v-model="form.slug" class="t-input min-w-[200px]">
              <option v-for="s in strategies" :key="s.slug" :value="s.slug">
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
        <div v-if="currentSpec.length && !isEnsemble" class="flex flex-col gap-2 border-t border-term-line pt-3">
          <span class="text-muted text-xs">--params</span>
          <p v-if="currentStrategy?.description" class="text-muted text-xs -mt-1">{{ currentStrategy.description }}</p>
          <ParamControls :spec="currentSpec" :params="form.params" />
        </div>

        <!-- Combine strategies (ensemble) builder -->
        <div v-if="isEnsemble" class="flex flex-col gap-3 border-t border-term-line pt-3">
          <div class="flex items-center justify-between">
            <span class="text-muted text-xs">--combine</span>
            <button type="button" class="t-btn-ghost text-xs px-2 py-1" @click="addComponent">+ add strategy</button>
          </div>
          <p class="text-muted text-xs -mt-1">Weighted vote — goes long when the weighted long-score ≥ threshold.</p>

          <div v-for="(c, idx) in combo.components" :key="idx" class="flex flex-col gap-2 border border-term-line p-2">
            <div class="flex items-center gap-3">
              <select v-model="c.module" @change="onComponentModuleChange(c)" class="t-input flex-1 min-w-0">
                <option v-for="s in combinable" :key="s.slug" :value="s.module">{{ s.name || s.slug }}</option>
              </select>
              <span class="text-xs text-muted shrink-0">w</span>
              <input type="number" min="1" max="10" step="1" v-model.number="c.weight"
                     class="t-input text-center shrink-0 px-1" style="width: 3.5rem; flex: none" />
              <input type="range" min="1" max="10" step="1" v-model.number="c.weight"
                     class="param-slider shrink-0" style="width: 120px" />
              <button type="button" class="t-btn-danger text-xs px-2 py-1 shrink-0" @click="removeComponent(idx)">x</button>
            </div>
            <ParamControls v-if="specFor(c.module).length" :spec="specFor(c.module)" :params="c.params" />
          </div>
          <p v-if="!combo.components.length" class="text-muted text-xs">no strategies yet — click “+ add strategy”.</p>

          <div class="flex items-center gap-3">
            <span class="text-xs w-24 shrink-0">threshold</span>
            <input type="number" min="0" max="1" step="0.05" v-model.number="combo.threshold"
                   class="t-input text-center shrink-0 px-1" style="width: 3.5rem; flex: none" />
            <input type="range" min="0" max="1" step="0.05" v-model.number="combo.threshold"
                   class="param-slider flex-1 min-w-0" />
          </div>

          <div class="flex items-center gap-2 flex-wrap">
            <input v-model="comboName" placeholder="combo name" class="t-input" style="max-width: 220px" />
            <button type="button" class="t-btn-ghost px-3 py-1.5" :disabled="savingCombo" @click="saveCombo">
              {{ savingCombo ? 'saving…' : 'save combo' }}
            </button>
            <span v-if="comboMsg" class="text-xs" :class="comboErr ? 'text-down' : 'text-up'">{{ comboMsg }}</span>
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
import ParamControls from '../components/ParamControls.vue'

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
  slug: 'sma_cross',
  symbol: 'BTCUSDT',
  timeframe: '1h',
  lookback: 500,
  params: {},
})

// Combine-strategies (ensemble) builder state
const combo = ref({ threshold: 0.5, components: [] })
const comboName = ref('')
const savingCombo = ref(false)
const comboMsg = ref('')
const comboErr = ref(false)

const currentStrategy = computed(() =>
  strategies.value.find((s) => s.slug === form.value.slug) || null
)
const currentSpec = computed(() => currentStrategy.value?.param_spec || [])
const isEnsemble = computed(() => currentStrategy.value?.module === 'strategies.ensemble')
// strategies that can be used as components (exclude ensembles to avoid nesting)
const combinable = computed(() => strategies.value.filter((s) => s.module !== 'strategies.ensemble'))

// param spec + default params for a given strategy module (used by combo components)
const specFor = (module) => strategies.value.find((s) => s.module === module)?.param_spec || []
const defaultParamsFor = (module) => {
  const s = strategies.value.find((x) => x.module === module)
  const out = {}
  for (const p of (s?.param_spec || [])) out[p.name] = s.params?.[p.name] ?? p.default
  return out
}

// Seed the params object from the selected strategy's defaults
const resetParams = () => {
  const next = {}
  const defaults = currentStrategy.value?.params || {}
  for (const p of currentSpec.value) {
    next[p.name] = defaults[p.name] ?? p.default
  }
  form.value.params = next
}

// Seed the combo builder from the selected ensemble's stored params
const seedCombo = () => {
  const p = currentStrategy.value?.params || {}
  combo.value = {
    threshold: typeof p.threshold === 'number' ? p.threshold : 0.5,
    components: (p.components || []).map((c) => ({
      module: c.module,
      weight: Number(c.weight) || 1,
      params: { ...defaultParamsFor(c.module), ...(c.params || {}) },
    })),
  }
  comboMsg.value = ''
  comboName.value = currentStrategy.value?.id != null ? (currentStrategy.value.name || '') : ''
}

const onStrategyChange = () => {
  if (isEnsemble.value) seedCombo()
  else resetParams()
}

watch(() => form.value.slug, onStrategyChange)

const addComponent = () => {
  const first = combinable.value[0]
  const module = first ? first.module : ''
  combo.value.components.push({ module, weight: 1, params: defaultParamsFor(module) })
}
const removeComponent = (idx) => combo.value.components.splice(idx, 1)
// reset a component's params to the new strategy's defaults when its module changes
const onComponentModuleChange = (c) => { c.params = defaultParamsFor(c.module) }

const buildRunParams = () => {
  if (isEnsemble.value) {
    return {
      threshold: combo.value.threshold,
      components: combo.value.components
        .filter((c) => c.module)
        .map((c) => ({ module: c.module, params: { ...c.params }, weight: Number(c.weight) || 1 })),
    }
  }
  return form.value.params
}

const saveCombo = async () => {
  comboMsg.value = ''
  const name = comboName.value.trim()
  if (!name) { comboErr.value = true; comboMsg.value = 'name required'; return }
  const comps = combo.value.components
    .filter((c) => c.module)
    .map((c) => ({ module: c.module, params: { ...c.params }, weight: Number(c.weight) || 1 }))
  if (!comps.length) { comboErr.value = true; comboMsg.value = 'add at least one strategy'; return }
  const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  savingCombo.value = true
  try {
    const r = await fetch('/trading/api/v1/backtest/combos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug, name, threshold: combo.value.threshold, components: comps }),
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`)
    await fetchStrategies()
    form.value.slug = d.slug   // select the saved combo (triggers seedCombo)
    comboErr.value = false
    comboMsg.value = 'saved ✓'
  } catch (e) {
    comboErr.value = true
    comboMsg.value = e.message
  } finally {
    savingCombo.value = false
  }
}

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
        form.value.slug = (strategies.value.find((s) => s.slug === 'sma_cross')
          || strategies.value[0]).slug
      }
      onStrategyChange()
    }
  } catch (e) { /* ignore */ }
}

const run = async () => {
  error.value = ''
  if (!currentStrategy.value) { error.value = 'no strategy selected'; return }
  running.value = true
  result.value = null
  try {
    const runRes = await fetch('/trading/api/v1/backtest/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        module: currentStrategy.value.module,
        symbol: form.value.symbol,
        timeframe: form.value.timeframe,
        lookback: form.value.lookback,
        params: buildRunParams(),
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
