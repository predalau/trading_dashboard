<template>
  <div class="flex flex-col gap-5">
    <!-- Charts Section -->
    <div class="flex flex-wrap gap-5">
      <TermPanel flush class="chart-panel">
        <div class="flex flex-wrap items-center gap-x-5 gap-y-2.5 px-3.5 py-2.5 border-b border-term-line">
          <!-- Ticker Dropdown -->
          <div class="relative flex items-center">
            <span class="text-muted" aria-hidden="true">╔═[</span>
            <button
              @click="dropdownOpen = !dropdownOpen"
              class="px-1 py-1.5 font-bold text-[15px] text-term-text hover:text-accent"
              :aria-expanded="dropdownOpen"
              aria-haspopup="listbox"
            >{{ selectedLabel }} {{ dropdownOpen ? '▴' : '▾' }}</button>
            <span class="text-muted" aria-hidden="true">]═</span>

            <!-- Dropdown Menu -->
            <div
              v-if="dropdownOpen"
              class="absolute top-full left-0 mt-1 w-60 bg-term-surface border border-term-line z-50"
            >
              <div class="max-h-64 overflow-y-auto" role="listbox">
                <div
                  v-for="pair in allPairs"
                  :key="pair.symbol"
                  class="flex items-center"
                  :class="pair.symbol === selectedSymbol ? 'bg-term-accent text-term-on-accent font-bold' : 'text-muted hover:text-term-text'"
                >
                  <button
                    @click="selectPair(pair.symbol)"
                    class="flex-1 px-3.5 py-2.5 text-left"
                    role="option"
                    :aria-selected="pair.symbol === selectedSymbol"
                  >{{ pair.symbol === selectedSymbol ? '> ' : '  ' }}{{ pair.label }}</button>
                  <button
                    v-if="isCustomPair(pair.symbol)"
                    @click.stop="removeCustomPair(pair.symbol)"
                    class="px-3 py-2.5 text-xs hover:text-down"
                    :aria-label="'Remove ' + pair.label"
                  >rm</button>
                </div>
              </div>

              <!-- Add Custom Pair -->
              <div class="border-t border-term-line p-2">
                <div v-if="showAddPair" class="flex gap-1">
                  <label class="sr-only" for="new-pair">New pair symbol</label>
                  <input
                    id="new-pair"
                    v-model="newPairInput"
                    @keyup.enter="addCustomPair"
                    placeholder="e.g. DOGE"
                    class="t-input flex-1"
                    autofocus
                  />
                  <button @click="addCustomPair" class="t-btn px-2.5 py-1.5">add</button>
                </div>
                <button
                  v-else
                  @click="showAddPair = true"
                  class="w-full text-left px-2 py-1.5 text-accent hover:text-term-text"
                >+ add pair</button>
              </div>
            </div>
          </div>

          <template v-if="symbolTicker">
            <span class="text-[22px] font-extrabold glow" :class="symbolTicker.change >= 0 ? 'text-up' : 'text-down'">
              {{ formatPrice(symbolTicker.price) }}
            </span>
            <span :class="symbolTicker.change >= 0 ? 'text-up' : 'text-down'">
              {{ symbolTicker.change >= 0 ? '+' : '' }}{{ formatPrice(symbolTicker.priceChange) }}
              ({{ symbolTicker.change >= 0 ? '+' : '' }}{{ symbolTicker.change.toFixed(2) }}%)
            </span>
          </template>

          <!-- Timeframe Buttons -->
          <div class="flex gap-0.5 ml-auto" role="group" aria-label="Timeframe">
            <button
              v-for="tf in timeframes"
              :key="tf.value"
              @click="selectedTimeframe = tf.value"
              class="px-2.5 py-2 border"
              :class="selectedTimeframe === tf.value ? 'border-term-accent text-accent' : 'border-transparent text-muted hover:text-term-text'"
              :aria-pressed="selectedTimeframe === tf.value"
            >{{ tf.label }}</button>
          </div>
        </div>
        <div class="p-3.5">
          <ChartComponent
            :symbol="selectedSymbol"
            :interval="selectedTimeframe"
            :trades="openTrades"
            :clickMode="clickMode"
            @chart-click="handleChartClick"
          />
        </div>
      </TermPanel>

      <!-- Right column: order form -->
      <div class="side-column flex flex-col gap-5">
        <TermPanel title="new_order.sh" tone="surface">
          <form class="flex flex-col gap-3" @submit.prevent="submitTrade">
            <!-- Side Toggle -->
            <div class="flex gap-2" role="group" aria-label="Side">
              <button
                type="button"
                @click="tradeForm.trade_type = 'BUY'"
                class="flex-1"
                :class="tradeForm.trade_type === 'BUY' ? 't-btn' : 't-btn-ghost'"
                :aria-pressed="tradeForm.trade_type === 'BUY'"
              >LONG</button>
              <button
                type="button"
                @click="tradeForm.trade_type = 'SELL'"
                class="flex-1 font-extrabold"
                :class="tradeForm.trade_type === 'SELL' ? 't-btn-short' : 't-btn-ghost'"
                :aria-pressed="tradeForm.trade_type === 'SELL'"
              >SHORT</button>
            </div>

            <!-- Price Inputs -->
            <div v-for="field in priceFields" :key="field.key" class="flex items-center gap-2.5">
              <label :for="'order-' + field.key" class="w-24 shrink-0 text-muted">{{ field.flag }}</label>
              <input
                :id="'order-' + field.key"
                v-model.number="tradeForm[field.key]"
                type="number"
                :step="field.step"
                class="t-input flex-1"
                :class="field.color"
              />
              <button
                v-if="field.mode"
                type="button"
                @click="startClickMode(field.mode)"
                class="t-btn-ghost px-2.5 py-1.5"
                :class="{ 'is-active': clickMode === field.mode }"
                :aria-label="'Pick ' + field.flag.replace('--', '') + ' on chart'"
                :aria-pressed="clickMode === field.mode"
              >+</button>
            </div>

            <div class="text-muted leading-relaxed">
              risk <span class="text-down">{{ riskReward ? '-' + riskReward.risk.toFixed(2) : '--' }}</span>
              · reward <span class="text-up">{{ riskReward ? '+' + riskReward.reward.toFixed(2) : '--' }}</span>
              · r:r <span class="text-term-text">{{ riskReward ? '1:' + riskReward.rr.toFixed(2) : '--' }}</span>
              <br>
              <span class="text-accent" aria-hidden="true">[{{ rrBar }}]</span> r:r out of 3
            </div>

            <div v-if="clickMode" class="text-accent">
              &gt; click the chart to set {{ clickMode === 'entry' ? 'entry' : clickMode === 'sl' ? 'stop loss' : 'take profit' }}<span class="cursor-text"> _</span>
            </div>

            <button
              type="submit"
              class="t-btn justify-start py-3.5"
              :disabled="!tradeForm.entry_price || !tradeForm.quantity"
            >$ ./execute --{{ isRealTrading ? 'real' : 'paper' }} ⏎</button>
          </form>
        </TermPanel>
        <SysLog class="flex-1" />
      </div>
    </div>

    <!-- Active Trades -->
    <TermPanel title="ps --positions" tone="surface" flush>
      <template #meta>
        <span>{{ openTrades.length }} running</span>
        <span v-if="openTrades.length > 0">
          unrealized
          <span class="font-bold" :class="totalUnrealized >= 0 ? 'text-up' : 'text-down'">
            {{ totalUnrealized >= 0 ? '+' : '' }}{{ totalUnrealized.toFixed(2) }} USDT
          </span>
        </span>
      </template>
      <div v-if="openTrades.length === 0" class="px-3.5 py-4 text-muted">
        no running positions on {{ selectedLabel }}
      </div>
      <div v-else class="overflow-x-auto">
        <table class="t-table">
          <thead>
            <tr>
              <th>PID</th>
              <th>Symbol</th>
              <th>Side</th>
              <th>Entry</th>
              <th>Mark</th>
              <th>SL</th>
              <th>TP</th>
              <th>Qty</th>
              <th>P&amp;L</th>
              <th>R</th>
              <th><span class="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trade in openTrades" :key="trade.id">
              <td class="text-muted">{{ formatPid(trade.id) }}</td>
              <td>{{ trade.symbol }}</td>
              <td :class="trade.trade_type === 'BUY' ? 'text-up' : 'text-down'">
                {{ trade.trade_type === 'BUY' ? 'LONG' : 'SHORT' }}
              </td>
              <td>{{ formatPrice(trade.entry_price) }}</td>
              <td>{{ currentPrices[trade.symbol] ? formatPrice(currentPrices[trade.symbol]) : '--' }}</td>
              <td class="text-down">{{ trade.stop_loss ? formatPrice(trade.stop_loss) : '--' }}</td>
              <td class="text-tp">{{ trade.take_profit ? formatPrice(trade.take_profit) : '--' }}</td>
              <td>{{ trade.quantity }}</td>
              <td class="font-bold" :class="getTradePnL(trade) >= 0 ? 'text-up' : 'text-down'">
                {{ currentPrices[trade.symbol] ? (getTradePnL(trade) >= 0 ? '+' : '') + getTradePnL(trade).toFixed(2) : '--' }}
              </td>
              <td>{{ formatR(trade) }}</td>
              <td>
                <button
                  v-if="confirmKill !== trade.id"
                  @click="confirmKill = trade.id"
                  class="t-btn-danger"
                >kill -9</button>
                <span v-else class="inline-flex gap-1.5">
                  <button @click="confirmKill = null; closeTrade(trade.id)" class="t-btn-danger">confirm</button>
                  <button @click="confirmKill = null" class="t-btn-ghost px-2.5 py-1.5">esc</button>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </TermPanel>
  </div>
</template>

<script setup>
import { ref, reactive, computed, inject, watch, onMounted, onUnmounted } from 'vue'
import ChartComponent from '../components/ChartComponent.vue'
import TermPanel from '../components/term/TermPanel.vue'
import SysLog from '../components/term/SysLog.vue'
import { useLogStore } from '../stores/log'
import binanceWS from '../services/websocket'

const STORAGE_KEY = 'trading_custom_pairs'
const DEFAULT_PAIRS = [
  { symbol: 'BTCUSDT', label: 'BTC/USDT' },
  { symbol: 'ETHUSDT', label: 'ETH/USDT' },
  { symbol: 'BNBUSDT', label: 'BNB/USDT' },
  { symbol: 'SOLUSDT', label: 'SOL/USDT' },
  { symbol: 'XRPUSDT', label: 'XRP/USDT' },
]

const selectedSymbol = ref('BTCUSDT')
const selectedTimeframe = ref('1h')
const showAddPair = ref(false)
const newPairInput = ref('')
const dropdownOpen = ref(false)

// Trade management
const openTrades = ref([])
const currentPrices = reactive({})
const tradeTickerUnsubs = ref([])
const closingTrades = new Set() // Prevent double-close
const clickMode = ref(null)
const tradeForm = ref({
  trade_type: 'BUY',
  entry_price: null,
  stop_loss: null,
  take_profit: null,
  quantity: null,
})

const priceFields = [
  { key: 'entry_price', flag: '--entry', step: '0.01', mode: 'entry', color: '' },
  { key: 'stop_loss', flag: '--sl', step: '0.01', mode: 'sl', color: 'text-down' },
  { key: 'take_profit', flag: '--tp', step: '0.01', mode: 'tp', color: 'text-tp' },
  { key: 'quantity', flag: '--qty', step: '0.001', mode: null, color: '' },
]

// Planned risk and reward in quote currency, from the form values
const riskReward = computed(() => {
  const { entry_price: entry, stop_loss: sl, take_profit: tp, quantity: qty } = tradeForm.value
  if (!entry || !sl || !tp || !qty) return null
  const risk = Math.abs(entry - sl) * qty
  const reward = Math.abs(tp - entry) * qty
  if (risk === 0) return null
  return { risk, reward, rr: reward / risk }
})

// Short hex id shown as the position "PID"
const formatPid = (id) => '0x' + Number(id).toString(16)

const hitLabel = (trade, price) => {
  const isBuy = trade.trade_type === 'BUY'
  const hitSl = trade.stop_loss && (isBuy ? price <= trade.stop_loss : price >= trade.stop_loss)
  return hitSl ? 'SL' : 'TP'
}

const confirmKill = ref(null)

const totalUnrealized = computed(() => openTrades.value.reduce((sum, t) => sum + getTradePnL(t), 0))

const RR_CELLS = 20
const rrBar = computed(() => {
  const filled = riskReward.value ? Math.round(Math.min(riskReward.value.rr, 3) / 3 * RR_CELLS) : 0
  return '■'.repeat(filled) + '□'.repeat(RR_CELLS - filled)
})

const isRealTrading = inject('isRealTrading')
const log = useLogStore()

const timeframes = [
  { label: '1h', value: '1h' },
  { label: '4h', value: '4h' },
  { label: '1d', value: '1d' },
  { label: '1w', value: '1w' }
]

// 24h ticker for the selected pair, shown in the chart header
const symbolTicker = ref(null)
let symbolTickerUnsub = null

const subscribeSymbolTicker = async () => {
  if (symbolTickerUnsub) symbolTickerUnsub()
  symbolTicker.value = null
  try {
    await binanceWS.connect()
  } catch (err) {
    console.error('Failed to connect WebSocket:', err)
    return
  }
  symbolTickerUnsub = binanceWS.subscribe(selectedSymbol.value, 'ticker', null, (data) => {
    if (data.symbol !== selectedSymbol.value) return
    symbolTicker.value = { price: data.price, priceChange: data.price_change, change: data.price_change_percent }
  })
}

const formatPrice = (p) => p.toLocaleString('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: Math.abs(p) < 10 ? 4 : 2,
})

// Load custom pairs from localStorage
const loadCustomPairs = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

const customPairs = ref(loadCustomPairs())

const allPairs = ref([...DEFAULT_PAIRS, ...customPairs.value])

const selectedLabel = ref(
  allPairs.value.find(p => p.symbol === selectedSymbol.value)?.label || 'BTC/USDT'
)

const addCustomPair = () => {
  const raw = newPairInput.value.trim().toUpperCase()
  if (!raw) return

  // Ensure it ends with USDT
  const symbol = raw.endsWith('USDT') ? raw : raw + 'USDT'
  const base = symbol.replace('USDT', '')
  const label = `${base}/USDT`

  // Check for duplicates
  if (allPairs.value.some(p => p.symbol === symbol)) {
    newPairInput.value = ''
    showAddPair.value = false
    return
  }

  const newPair = { symbol, label }
  customPairs.value.push(newPair)
  allPairs.value.push(newPair)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(customPairs.value))

  newPairInput.value = ''
  showAddPair.value = false
}

const removeCustomPair = (symbol) => {
  customPairs.value = customPairs.value.filter(p => p.symbol !== symbol)
  allPairs.value = [...DEFAULT_PAIRS, ...customPairs.value]
  localStorage.setItem(STORAGE_KEY, JSON.stringify(customPairs.value))

  // If we removed the selected pair, switch to BTC
  if (selectedSymbol.value === symbol) {
    selectPair('BTCUSDT')
  }
}

const isCustomPair = (symbol) => {
  return customPairs.value.some(p => p.symbol === symbol)
}

const selectPair = (symbol) => {
  selectedSymbol.value = symbol
  selectedLabel.value = allPairs.value.find(p => p.symbol === symbol)?.label || symbol
  dropdownOpen.value = false
}

/**
 * Calculate unrealized P&L for a trade
 */
const getTradePnL = (trade) => {
  const price = currentPrices[trade.symbol]
  if (!price) return 0
  if (trade.trade_type === 'BUY') {
    return (price - trade.entry_price) * trade.quantity
  }
  return (trade.entry_price - price) * trade.quantity
}

/**
 * Calculate R (reward-to-risk ratio): |TP - entry| / |entry - SL|
 * Requires both stop_loss and take_profit to be set.
 */
const getTradeR = (trade) => {
  if (!trade.stop_loss || !trade.take_profit) return null
  const risk = Math.abs(trade.entry_price - trade.stop_loss)
  if (risk === 0) return null
  return Math.abs(trade.take_profit - trade.entry_price) / risk
}

const formatR = (trade) => {
  const r = getTradeR(trade)
  if (r === null) return '-'
  return r.toFixed(2) + 'R'
}

/**
 * Handle trade ticker updates - update current prices and check SL/TP
 */
const handleTradeTickerUpdate = (tickerData) => {
  const symbol = tickerData.symbol
  const price = tickerData.price
  currentPrices[symbol] = price

  // Check SL/TP for all open trades with this symbol
  for (const trade of openTrades.value) {
    if (trade.symbol !== symbol || closingTrades.has(trade.id)) continue
    if (!trade.is_open) continue

    let shouldClose = false
    if (trade.trade_type === 'BUY') {
      if (trade.stop_loss && price <= trade.stop_loss) shouldClose = true
      if (trade.take_profit && price >= trade.take_profit) shouldClose = true
    } else {
      if (trade.stop_loss && price >= trade.stop_loss) shouldClose = true
      if (trade.take_profit && price <= trade.take_profit) shouldClose = true
    }

    if (shouldClose) {
      closingTrades.add(trade.id)
      log.push('WARN', `${trade.symbol} hit ${hitLabel(trade, price)} @ ${price}`)
      closeTrade(trade.id, price)
    }
  }
}

/**
 * Subscribe to tickers for all symbols with open trades
 */
const subscribeToTradeTickers = async () => {
  // Unsubscribe from previous trade ticker subs
  tradeTickerUnsubs.value.forEach(unsub => unsub())
  tradeTickerUnsubs.value = []

  // Get unique symbols from open trades (excluding selectedSymbol which is already subscribed)
  const symbols = [...new Set(openTrades.value.map(t => t.symbol))]

  if (!binanceWS.getStatus().connected) {
    try {
      await binanceWS.connect()
    } catch (err) {
      console.error('Failed to connect WebSocket:', err)
      return
    }
  }

  for (const symbol of symbols) {
    const unsub = binanceWS.subscribe(symbol, 'ticker', null, handleTradeTickerUpdate)
    tradeTickerUnsubs.value.push(unsub)
  }
}

/**
 * Fetch open trades for the selected symbol
 */
const fetchTrades = async () => {
  try {
    const response = await fetch(`/trading/api/v1/trades/?symbol=${selectedSymbol.value}&open=true`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    openTrades.value = await response.json()
    await subscribeToTradeTickers()
  } catch (err) {
    console.error('Failed to fetch trades:', err)
  }
}

/**
 * Submit a new trade
 */
const submitTrade = async () => {
  try {
    const response = await fetch('/trading/api/v1/trades/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: selectedSymbol.value,
        trade_type: tradeForm.value.trade_type,
        entry_price: tradeForm.value.entry_price,
        stop_loss: tradeForm.value.stop_loss || null,
        take_profit: tradeForm.value.take_profit || null,
        quantity: tradeForm.value.quantity,
      })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const f = tradeForm.value
    log.push('FILL', `${f.trade_type === 'BUY' ? 'LONG' : 'SHORT'} ${f.quantity} ${selectedSymbol.value} @ ${f.entry_price}`)
    if (f.stop_loss || f.take_profit) {
      log.push('SET', `TP ${f.take_profit || '--'} · SL ${f.stop_loss || '--'}`)
    }

    // Reset form and refresh trades
    tradeForm.value = { trade_type: 'BUY', entry_price: null, stop_loss: null, take_profit: null, quantity: null }
    await fetchTrades()
  } catch (err) {
    log.push('ERR', `order rejected: ${err.message}`)
    console.error('Failed to create trade:', err)
  }
}

/**
 * Close a trade, optionally with an exit price
 */
const closeTrade = async (tradeId, exitPrice = null) => {
  try {
    const options = { method: 'DELETE' }
    if (exitPrice !== null) {
      options.headers = { 'Content-Type': 'application/json' }
      options.body = JSON.stringify({ exit_price: exitPrice })
    }
    const response = await fetch(`/trading/api/v1/trades/${tradeId}`, options)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    closingTrades.delete(tradeId)
    log.push('FILL', `closed position ${formatPid(tradeId)}${exitPrice !== null ? ' @ ' + exitPrice : ''}`)
    await fetchTrades()
  } catch (err) {
    closingTrades.delete(tradeId)
    log.push('ERR', `close ${formatPid(tradeId)} failed: ${err.message}`)
    console.error('Failed to close trade:', err)
  }
}

/**
 * Handle click-to-set mode
 */
const startClickMode = (mode) => {
  clickMode.value = clickMode.value === mode ? null : mode
}

const handleChartClick = ({ mode, price }) => {
  if (mode === 'entry') tradeForm.value.entry_price = price
  else if (mode === 'sl') tradeForm.value.stop_loss = price
  else if (mode === 'tp') tradeForm.value.take_profit = price
  log.push('SET', `${mode} = ${price}`)
  clickMode.value = null
}

// Watch for symbol changes to update stats + ticker subscription + trades
watch(selectedSymbol, async () => {
  subscribeSymbolTicker()
  await fetchTrades()
})

const closeDropdown = (e) => {
  if (dropdownOpen.value && !e.target.closest('.relative')) {
    dropdownOpen.value = false
    showAddPair.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', closeDropdown)
  subscribeSymbolTicker()
  await fetchTrades()
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
  tradeTickerUnsubs.value.forEach(unsub => unsub())
  if (symbolTickerUnsub) symbolTickerUnsub()
})
</script>

<style scoped>
.chart-panel {
  flex: 999 1 640px;
}

.side-column {
  flex: 1 1 320px;
  min-width: 0;
}

.t-btn-short {
  @apply inline-flex items-center justify-center px-3.5 py-2.5 cursor-pointer;
  background: var(--down);
  color: var(--on-accent);
  border: 1px solid var(--down);
}
</style>
