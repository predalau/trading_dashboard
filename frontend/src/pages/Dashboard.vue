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

      <!-- New Trade Form -->
      <div>
        <div class="chart-container">
          <h3 class="text-lg font-semibold mb-4">New Trade</h3>
          <div class="space-y-3">
            <!-- Side Toggle -->
            <div class="flex gap-2">
              <button
                @click="tradeForm.trade_type = 'BUY'"
                :class="['btn flex-1 text-sm', tradeForm.trade_type === 'BUY' ? 'btn-success' : 'btn-secondary']"
              >Buy</button>
              <button
                @click="tradeForm.trade_type = 'SELL'"
                :class="['btn flex-1 text-sm', tradeForm.trade_type === 'SELL' ? 'btn-danger' : 'btn-secondary']"
              >Sell</button>
            </div>

            <!-- Price Inputs -->
            <div>
              <label class="text-xs text-dark-400 block mb-1">Entry Price</label>
              <div class="flex gap-1">
                <input v-model.number="tradeForm.entry_price" type="number" step="0.01"
                  class="flex-1 px-2 py-1.5 bg-dark-900 border border-dark-600 rounded text-sm text-white focus:border-secondary-500 focus:outline-none" />
                <button @click="startClickMode('entry')" :class="['btn text-xs px-2', clickMode === 'entry' ? 'btn-primary' : 'btn-secondary']" title="Click chart to set">+</button>
              </div>
            </div>

            <div>
              <label class="text-xs text-dark-400 block mb-1">Stop Loss</label>
              <div class="flex gap-1">
                <input v-model.number="tradeForm.stop_loss" type="number" step="0.01"
                  class="flex-1 px-2 py-1.5 bg-dark-900 border border-dark-600 rounded text-sm text-white focus:border-secondary-500 focus:outline-none" />
                <button @click="startClickMode('sl')" :class="['btn text-xs px-2', clickMode === 'sl' ? 'btn-primary' : 'btn-secondary']" title="Click chart to set">+</button>
              </div>
            </div>

            <div>
              <label class="text-xs text-dark-400 block mb-1">Take Profit</label>
              <div class="flex gap-1">
                <input v-model.number="tradeForm.take_profit" type="number" step="0.01"
                  class="flex-1 px-2 py-1.5 bg-dark-900 border border-dark-600 rounded text-sm text-white focus:border-secondary-500 focus:outline-none" />
                <button @click="startClickMode('tp')" :class="['btn text-xs px-2', clickMode === 'tp' ? 'btn-primary' : 'btn-secondary']" title="Click chart to set">+</button>
              </div>
            </div>

            <div>
              <label class="text-xs text-dark-400 block mb-1">Quantity</label>
              <input v-model.number="tradeForm.quantity" type="number" step="0.001"
                class="w-full px-2 py-1.5 bg-dark-900 border border-dark-600 rounded text-sm text-white focus:border-secondary-500 focus:outline-none" />
            </div>

            <button @click="submitTrade" class="btn btn-primary w-full text-sm" :disabled="!tradeForm.entry_price || !tradeForm.quantity">
              Place Trade
            </button>

            <div v-if="clickMode" class="text-xs text-secondary-400 text-center animate-pulse">
              Click on chart to set {{ clickMode === 'entry' ? 'Entry' : clickMode === 'sl' ? 'Stop Loss' : 'Take Profit' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Trades -->
    <div v-if="openTrades.length > 0" class="chart-container">
      <h2 class="text-xl font-semibold mb-4">Active Trades</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="border-b border-dark-700">
            <tr>
              <th class="text-left py-2 text-dark-400">Symbol</th>
              <th class="text-left py-2 text-dark-400">Side</th>
              <th class="text-left py-2 text-dark-400">Entry</th>
              <th class="text-left py-2 text-dark-400">Current</th>
              <th class="text-left py-2 text-dark-400">SL</th>
              <th class="text-left py-2 text-dark-400">TP</th>
              <th class="text-left py-2 text-dark-400">Qty</th>
              <th class="text-left py-2 text-dark-400">P&L</th>
              <th class="text-left py-2 text-dark-400">R</th>
              <th class="text-left py-2 text-dark-400"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trade in openTrades" :key="trade.id" class="border-b border-dark-800 hover:bg-dark-800 transition">
              <td class="py-3">{{ trade.symbol }}</td>
              <td class="py-3" :class="trade.trade_type === 'BUY' ? 'text-positive' : 'text-negative'">
                {{ trade.trade_type }}
              </td>
              <td class="py-3">${{ trade.entry_price.toFixed(2) }}</td>
              <td class="py-3">
                {{ currentPrices[trade.symbol] ? '$' + currentPrices[trade.symbol].toFixed(2) : '-' }}
              </td>
              <td class="py-3 text-red-400">{{ trade.stop_loss ? '$' + trade.stop_loss.toFixed(2) : '-' }}</td>
              <td class="py-3 text-green-400">{{ trade.take_profit ? '$' + trade.take_profit.toFixed(2) : '-' }}</td>
              <td class="py-3">{{ trade.quantity }}</td>
              <td class="py-3 font-semibold" :class="getTradePnL(trade) >= 0 ? 'text-positive' : 'text-negative'">
                {{ currentPrices[trade.symbol] ? (getTradePnL(trade) >= 0 ? '+' : '') + '$' + getTradePnL(trade).toFixed(2) : '-' }}
              </td>
              <td class="py-3 font-semibold text-secondary-400">
                {{ formatR(trade) }}
              </td>
              <td class="py-3">
                <button @click="closeTrade(trade.id)" class="text-red-400 hover:text-red-300 text-xs">Close</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue'
import ChartComponent from '../components/ChartComponent.vue'
import TermPanel from '../components/term/TermPanel.vue'
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

    // Reset form and refresh trades
    tradeForm.value = { trade_type: 'BUY', entry_price: null, stop_loss: null, take_profit: null, quantity: null }
    await fetchTrades()
  } catch (err) {
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
    await fetchTrades()
  } catch (err) {
    closingTrades.delete(tradeId)
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
</style>
