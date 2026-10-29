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
            <input v-model.number="form.lookback" type="number" min="50" max="10000" class="t-input w-32" />
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

        <!-- Multi-timeframe trend bias (applies to single strategies and combos) -->
        <div class="flex flex-col gap-2 border-t border-term-line pt-3">
          <div class="flex items-center gap-3 flex-wrap">
            <span class="text-muted text-xs">--trend-bias</span>
            <button type="button" class="t-btn px-4 py-1.5" :class="bias.enabled ? '' : 't-btn-ghost'"
                    @click="bias.enabled = !bias.enabled">{{ bias.enabled ? 'on' : 'off' }}</button>
            <span v-if="bias.enabled && higherTFs.length" class="text-muted text-xs">
              uses {{ higherTFs.join(' + ') }} trend
            </span>
            <span v-else-if="bias.enabled" class="text-down text-xs">no higher timeframe above {{ form.timeframe }}</span>
          </div>

          <template v-if="bias.enabled">
            <p class="text-muted text-xs -mt-1">Blocks entries that fight the higher-timeframe trend (price vs SMA). −1 = off · +1 = require full alignment.</p>

            <div class="flex items-center gap-3">
              <span class="text-xs w-24 shrink-0">SMA length</span>
              <input type="number" min="5" max="200" step="1" v-model.number="bias.sma_len"
                     class="t-input text-center shrink-0 px-1" style="width: 3.5rem; flex: none" />
              <input type="range" min="5" max="200" step="1" v-model.number="bias.sma_len" class="param-slider flex-1 min-w-0" />
            </div>

            <div class="flex items-center gap-3">
              <span class="text-xs w-24 shrink-0">entry ≥</span>
              <input type="number" min="-1" max="1" step="0.1" v-model.number="bias.entry_threshold"
                     class="t-input text-center shrink-0 px-1" style="width: 3.5rem; flex: none" />
              <input type="range" min="-1" max="1" step="0.1" v-model.number="bias.entry_threshold" class="param-slider flex-1 min-w-0" />
            </div>

            <div class="flex items-center gap-3">
              <span class="text-xs w-24 shrink-0">force exit</span>
              <button type="button" class="t-btn px-4 py-1.5" :class="bias.exit_enabled ? '' : 't-btn-ghost'"
                      @click="bias.exit_enabled = !bias.exit_enabled">{{ bias.exit_enabled ? 'on' : 'off' }}</button>
              <span class="text-muted text-xs">close a long when the higher-TF trend flips bearish</span>
            </div>
            <div v-if="bias.exit_enabled" class="flex items-center gap-3">
              <span class="text-xs w-24 shrink-0">exit ≤</span>
              <input type="number" min="-1" max="0" step="0.1" v-model.number="bias.exit_threshold"
                     class="t-input text-center shrink-0 px-1" style="width: 3.5rem; flex: none" />
              <input type="range" min="-1" max="0" step="0.1" v-model.number="bias.exit_threshold" class="param-slider flex-1 min-w-0" />
            </div>
          </template>
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

    <!-- Optimizer: sweep all settings -->
    <TermPanel title="sweep.sh — optimizer" tone="surface">
      <div class="flex flex-col gap-3">
        <div class="flex flex-wrap gap-3 items-end">
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">grid steps / param</span>
            <input v-model.number="sweepOpts.grid_steps" type="number" min="2" max="12" class="t-input w-24" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">max combos</span>
            <input v-model.number="sweepOpts.max_combos" type="number" min="50" max="100000" class="t-input w-28" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">lookback (bars)</span>
            <input v-model.number="sweepOpts.lookback" type="number" min="50" max="10000" class="t-input w-28" />
          </label>
          <button type="button" class="t-btn justify-start py-3" :disabled="sweepRunning" @click="startSweep">
            {{ sweepRunning ? '$ sweeping…' : '$ ./sweep --all ⏎' }}
          </button>
          <button type="button" class="t-btn justify-start py-3" :disabled="sweepRunning" @click="startComboSweep">
            $ ./discover-combos ⏎
          </button>
          <button v-if="sweepRunning" type="button" class="t-btn-danger py-3 px-4" @click="stopSweep">stop</button>
        </div>
        <p class="text-muted text-xs">
          Full cross-product: all strategies × all 5 symbols × all 4 timeframes × param grid × bias (off / on@0.0 / on@0.5),
          capped at max-combos. Results are cached, so repeated combos are skipped instantly (and a stopped sweep resumes on re-run).
        </p>
        <div v-if="sweep" class="flex flex-col gap-1">
          <div class="flex justify-between text-xs text-muted">
            <span>{{ sweep.status }}</span>
            <span>{{ sweep.done }} / {{ sweep.total }}</span>
          </div>
          <div class="h-2 bg-term-surface border border-term-line">
            <div class="h-full bg-term-accent" :style="{ width: sweepPct + '%' }"></div>
          </div>
          <span v-if="sweep.error" class="text-down text-xs">{{ sweep.error }}</span>
        </div>
      </div>
    </TermPanel>

    <!-- Report: filterable top results over the whole sweep cache -->
    <TermPanel title="report — top results">
      <template #meta><span>{{ reportRows.length }} shown · ranked by total return</span></template>

      <div class="flex flex-wrap gap-2 mb-3">
        <select v-model="reportFilters.symbol" class="t-input" style="width: auto">
          <option value="">all symbols</option>
          <option v-for="s in symbols" :key="s" :value="s">{{ s }}</option>
        </select>
        <select v-model="reportFilters.timeframe" class="t-input" style="width: auto">
          <option value="">all timeframes</option>
          <option v-for="t in timeframes" :key="t" :value="t">{{ t }}</option>
        </select>
        <select v-model="reportFilters.slug" class="t-input" style="width: auto">
          <option value="">all strategies</option>
          <option v-for="s in strategyOptions" :key="s.slug" :value="s.slug">{{ s.name }}</option>
        </select>
        <select v-model="reportFilters.bias" class="t-input" style="width: auto">
          <option value="">bias: any</option>
          <option value="on">bias: on</option>
          <option value="off">bias: off</option>
        </select>
        <button v-if="reportFilters.symbol || reportFilters.timeframe || reportFilters.slug || reportFilters.bias"
                type="button" class="t-btn-ghost text-xs px-2" @click="clearReportFilters">clear</button>
      </div>

      <div v-if="!reportRows.length" class="text-muted text-xs py-3">
        no cached results for this filter — run a sweep above.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="t-table">
          <thead>
            <tr>
              <th>#</th><th>strategy</th><th>symbol</th><th>tf</th>
              <th>params</th><th>bias</th><th>return</th><th>trades</th><th></th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in reportRows" :key="i"
                class="cursor-pointer hover:bg-term-surface"
                @click="applyResult(r.config)">
              <td class="text-muted">{{ i + 1 }}</td>
              <td>{{ r.config.slug }}</td>
              <td>{{ r.config.symbol }}</td>
              <td>{{ r.config.timeframe }}</td>
              <td class="text-muted text-xs">{{ paramsStr(r.config.params) }}</td>
              <td class="text-xs">{{ r.config.bias.enabled ? ('≥' + r.config.bias.entry_threshold) : '—' }}</td>
              <td :class="r.score >= 0 ? 'text-up' : 'text-down'">{{ pct(r.score) }}</td>
              <td>{{ r.metrics.num_trades }}</td>
              <td class="text-muted hover:text-accent text-xs" @click.stop="saveConfigFromRow(r.config)">save</td>
              <td class="text-accent text-xs">run ▸</td>
            </tr>
          </tbody>
        </table>
      </div>
    </TermPanel>

    <!-- Saved configurations (presets) -->
    <TermPanel title="saved configs" tone="surface">
      <template #meta>
        <button type="button" class="t-btn-ghost text-xs px-2" :disabled="!currentStrategy" @click="saveCurrentConfig">
          + save current
        </button>
      </template>
      <span v-if="configMsg" class="text-xs text-muted">{{ configMsg }}</span>
      <div v-if="!savedConfigs.length" class="text-muted text-xs py-2">
        no saved configs yet — tune a strategy and “save current”, or save a row from the report.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="t-table">
          <thead>
            <tr><th>name</th><th>strategy</th><th>symbol</th><th>tf</th><th>params</th><th>bias</th><th></th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="c in savedConfigs" :key="c.id" class="hover:bg-term-surface">
              <td>{{ c.name }}</td>
              <td>{{ c.slug }}</td>
              <td>{{ c.symbol }}</td>
              <td>{{ c.timeframe }}</td>
              <td class="text-muted text-xs">{{ paramsStr(c.params) }}</td>
              <td class="text-xs">{{ c.bias.enabled ? ('≥' + c.bias.entry_threshold) : '—' }}</td>
              <td class="text-accent text-xs cursor-pointer" @click="loadConfig(c)">run ▸</td>
              <td class="text-down text-xs cursor-pointer" @click="deleteSavedConfig(c.id)">✕</td>
            </tr>
          </tbody>
        </table>
      </div>
    </TermPanel>

    <!-- Sweep history -->
    <TermPanel title="sweep history" tone="surface">
      <div v-if="!sweepHistory.length" class="text-muted text-xs py-2">no sweeps run yet.</div>
      <div v-else class="overflow-x-auto">
        <table class="t-table">
          <thead><tr><th>#</th><th>status</th><th>combos</th><th>when</th><th></th></tr></thead>
          <tbody>
            <tr v-for="s in sweepHistory" :key="s.id" class="hover:bg-term-surface">
              <td class="text-muted">{{ s.id }}</td>
              <td :class="s.status === 'done' ? 'text-up' : (s.status === 'running' ? 'text-accent' : 'text-muted')">{{ s.status }}</td>
              <td>{{ s.done }}/{{ s.total }}</td>
              <td class="text-muted text-xs">{{ fmtDate(s.created_at) }}</td>
              <td class="text-accent text-xs cursor-pointer" @click="viewSweep(s.id)">view ▸</td>
            </tr>
          </tbody>
        </table>
      </div>
    </TermPanel>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
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

// Multi-timeframe trend bias
const bias = ref({ enabled: false, sma_len: 50, entry_threshold: 0.0, exit_enabled: false, exit_threshold: -0.5 })
const TF_LADDER = ['15m', '1h', '4h', '1d', '1w']
const higherTFs = computed(() => {
  const i = TF_LADDER.indexOf(form.value.timeframe)
  return i < 0 ? [] : TF_LADDER.slice(i + 1).slice(0, 2)
})

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
        bias_enabled: bias.value.enabled,
        bias_sma_len: bias.value.sma_len,
        bias_entry_threshold: bias.value.entry_threshold,
        bias_exit_enabled: bias.value.exit_enabled,
        bias_exit_threshold: bias.value.exit_threshold,
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

onMounted(() => { fetchStrategies(); fetchResults(); fetchSavedConfigs(); fetchSweepHistory() })
onUnmounted(() => { if (sweepPoll) clearInterval(sweepPoll) })

// ---- Report: filterable results over the sweep cache ----
const reportFilters = ref({ symbol: '', timeframe: '', slug: '', bias: '' })
const reportRows = ref([])
const strategyOptions = computed(() => combinable.value.map((s) => ({ slug: s.slug, name: s.name || s.slug })))

const fetchResults = async () => {
  const p = new URLSearchParams()
  const f = reportFilters.value
  if (f.symbol) p.set('symbol', f.symbol)
  if (f.timeframe) p.set('timeframe', f.timeframe)
  if (f.slug) p.set('slug', f.slug)
  if (f.bias) p.set('bias', f.bias)
  p.set('limit', '100')
  try {
    const r = await fetch('/trading/api/v1/backtest/results?' + p.toString())
    if (r.ok) reportRows.value = await r.json()
  } catch (e) { /* ignore */ }
}
const clearReportFilters = () => { reportFilters.value = { symbol: '', timeframe: '', slug: '', bias: '' } }
watch(reportFilters, fetchResults, { deep: true })

// ---- Saved configs (presets) + sweep history ----
const savedConfigs = ref([])
const configMsg = ref('')
const sweepHistory = ref([])
const fmtDate = (s) => (s ? new Date(s).toLocaleString() : '')

const fetchSavedConfigs = async () => {
  try { const r = await fetch('/trading/api/v1/backtest/saved-configs'); if (r.ok) savedConfigs.value = await r.json() } catch (e) { /* ignore */ }
}
const fetchSweepHistory = async () => {
  try { const r = await fetch('/trading/api/v1/backtest/sweeps?limit=20'); if (r.ok) sweepHistory.value = await r.json() } catch (e) { /* ignore */ }
}

const postConfig = async (payload) => {
  const r = await fetch('/trading/api/v1/backtest/saved-configs', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  })
  const d = await r.json()
  if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`)
  await fetchSavedConfigs()
  return d
}

const saveCurrentConfig = async () => {
  if (!currentStrategy.value) return
  const name = window.prompt('Save configuration as:', `${form.value.slug} ${form.value.symbol} ${form.value.timeframe}`)
  if (!name) return
  configMsg.value = ''
  try {
    await postConfig({
      name, module: currentStrategy.value.module, slug: form.value.slug,
      params: buildRunParams(), symbol: form.value.symbol, timeframe: form.value.timeframe,
      lookback: form.value.lookback, bias: { ...bias.value },
    })
    configMsg.value = 'saved ✓'
  } catch (e) { configMsg.value = e.message }
}

const saveConfigFromRow = async (cfg) => {
  const name = window.prompt('Save configuration as:', `${cfg.slug} ${cfg.symbol} ${cfg.timeframe}${cfg.bias.enabled ? ' +bias' : ''}`)
  if (!name) return
  try {
    await postConfig({
      name, module: cfg.module, slug: cfg.slug, params: cfg.params,
      symbol: cfg.symbol, timeframe: cfg.timeframe, lookback: cfg.lookback, bias: cfg.bias,
    })
  } catch (e) { error.value = e.message }
}

const loadConfig = async (cfg) => {
  form.value.slug = cfg.slug
  form.value.symbol = cfg.symbol
  form.value.timeframe = cfg.timeframe
  form.value.lookback = cfg.lookback
  bias.value = {
    enabled: !!cfg.bias.enabled, sma_len: cfg.bias.sma_len || 50,
    entry_threshold: cfg.bias.entry_threshold ?? 0,
    exit_enabled: !!cfg.bias.exit_enabled, exit_threshold: cfg.bias.exit_threshold ?? -0.5,
  }
  await nextTick()
  if (!isEnsemble.value) form.value.params = { ...cfg.params }
  await nextTick()
  run()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const deleteSavedConfig = async (id) => {
  try { await fetch(`/trading/api/v1/backtest/saved-configs/${id}`, { method: 'DELETE' }); await fetchSavedConfigs() } catch (e) { /* ignore */ }
}

const viewSweep = async (id) => {
  try {
    const d = await (await fetch(`/trading/api/v1/backtest/sweep/${id}`)).json()
    reportRows.value = d.results || []
  } catch (e) { /* ignore */ }
}

// ---- Optimizer sweep + report ----
const sweepOpts = ref({ grid_steps: 7, max_combos: 4000, lookback: 1000 })
const sweep = ref(null)
const sweepRunning = ref(false)
let sweepPoll = null

const sweepPct = computed(() => {
  if (!sweep.value || !sweep.value.total) return 0
  return Math.round((sweep.value.done / sweep.value.total) * 100)
})

const paramsStr = (p) => {
  if (!p) return ''
  if (Array.isArray(p.components)) {
    const names = p.components
      .map((c) => c.module.split('.').pop() + (Number(c.weight) > 1 ? '×' + c.weight : ''))
      .join('+')
    return `thr=${p.threshold} · ${names}`
  }
  return Object.entries(p).map(([k, v]) => `${k}=${v}`).join(' ')
}

const startComboSweep = async () => {
  error.value = ''
  sweepRunning.value = true
  sweep.value = null
  try {
    const r = await fetch('/trading/api/v1/backtest/combo-sweep', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lookback: sweepOpts.value.lookback, max_combos: sweepOpts.value.max_combos }),
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`)
    pollSweep(d.id)
  } catch (e) {
    error.value = e.message
    sweepRunning.value = false
  }
}

const startSweep = async () => {
  error.value = ''
  sweepRunning.value = true
  sweep.value = null
  try {
    const r = await fetch('/trading/api/v1/backtest/sweep', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lookback: sweepOpts.value.lookback,
        grid_steps: sweepOpts.value.grid_steps,
        max_combos: sweepOpts.value.max_combos,
      }),
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`)
    pollSweep(d.id)
  } catch (e) {
    error.value = e.message
    sweepRunning.value = false
  }
}

const pollSweep = (id) => {
  if (sweepPoll) clearInterval(sweepPoll)
  sweep.value = sweep.value || { id }
  sweep.value.id = id
  sweepPoll = setInterval(async () => {
    try {
      const d = await (await fetch(`/trading/api/v1/backtest/sweep/${id}`)).json()
      d.id = id
      sweep.value = d
      if (d.status !== 'running') {
        clearInterval(sweepPoll); sweepPoll = null; sweepRunning.value = false
        fetchResults()        // refresh the report with the newly-cached results
        fetchSweepHistory()   // and the history list
      }
    } catch (e) { /* keep polling */ }
  }, 2000)
}

const stopSweep = async () => {
  if (!sweep.value?.id) return
  try { await fetch(`/trading/api/v1/backtest/sweep/${sweep.value.id}/cancel`, { method: 'POST' }) } catch (e) { /* ignore */ }
}

// Click a report row -> load that config into the form and run it
const applyResult = async (cfg) => {
  form.value.symbol = cfg.symbol
  form.value.timeframe = cfg.timeframe
  form.value.lookback = cfg.lookback
  bias.value = {
    enabled: !!cfg.bias.enabled,
    sma_len: cfg.bias.sma_len || 50,
    entry_threshold: cfg.bias.entry_threshold ?? 0,
    exit_enabled: !!cfg.bias.exit_enabled,
    exit_threshold: cfg.bias.exit_threshold ?? -0.5,
  }
  if (cfg.module === 'strategies.ensemble') {
    // pick the saved combo if its slug exists, else the generic "Combine Strategies" entry
    const match = strategies.value.find((s) => s.slug === cfg.slug && s.module === 'strategies.ensemble')
    const base = strategies.value.find((s) => s.module === 'strategies.ensemble' && s.id == null)
    form.value.slug = (match || base)?.slug || cfg.slug
    await nextTick()                 // slug watcher seeds the combo builder
    combo.value = {
      threshold: cfg.params.threshold ?? 0.5,
      components: (cfg.params.components || []).map((c) => ({
        module: c.module, weight: Number(c.weight) || 1, params: { ...(c.params || {}) },
      })),
    }
  } else {
    form.value.slug = cfg.slug
    await nextTick()                 // slug watcher resets params to defaults
    form.value.params = { ...cfg.params }
  }
  await nextTick()
  run()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
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
