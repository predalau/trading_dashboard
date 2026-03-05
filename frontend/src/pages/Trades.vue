<template>
  <div class="space-y-8 animate-fade-in">
    <section class="space-y-4">
      <h1 class="text-4xl font-bold text-purple-400">The Raid Hall</h1>
      <p class="text-purple-400">Prepare your raids and study your glorious victories and honorable defeats</p>
    </section>

    <!-- New Trade Form -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="chart-container border-purple-700">
        <h2 class="text-xl font-semibold mb-4 text-purple-400">Plan Your Raid</h2>
        <form @submit.prevent="submitTrade" class="space-y-4">
          <div>
            <label class="block text-sm text-dark-400 mb-2">Symbol</label>
            <select v-model="form.symbol" class="w-full">
              <option value="">Select Symbol</option>
              <option value="BTCUSDT">BTC/USDT</option>
              <option value="ETHUSDT">ETH/USDT</option>
              <option value="BNBUSDT">BNB/USDT</option>
              <option value="SOLUSDT">SOL/USDT</option>
              <option value="XRPUSDT">XRP/USDT</option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <button
              type="button"
              @click="form.trade_type = 'BUY'"
              class="py-2 rounded-lg font-medium transition"
              :class="form.trade_type === 'BUY' ? 'bg-green-600 text-white' : 'bg-dark-700 text-dark-400'"
            >
              Buy
            </button>
            <button
              type="button"
              @click="form.trade_type = 'SELL'"
              class="py-2 rounded-lg font-medium transition"
              :class="form.trade_type === 'SELL' ? 'bg-red-600 text-white' : 'bg-dark-700 text-dark-400'"
            >
              Sell
            </button>
          </div>

          <div>
            <label class="block text-sm text-dark-400 mb-2">Entry Price</label>
            <input v-model.number="form.entry_price" type="number" placeholder="0.00" step="0.01" class="w-full" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm text-dark-400 mb-2">Stop Loss</label>
              <input v-model.number="form.stop_loss" type="number" placeholder="0.00" step="0.01" class="w-full" />
            </div>
            <div>
              <label class="block text-sm text-dark-400 mb-2">Take Profit</label>
              <input v-model.number="form.take_profit" type="number" placeholder="0.00" step="0.01" class="w-full" />
            </div>
          </div>

          <div>
            <label class="block text-sm text-dark-400 mb-2">Quantity</label>
            <input v-model.number="form.quantity" type="number" placeholder="0.0" step="0.001" class="w-full" />
          </div>

          <div>
            <label class="block text-sm text-dark-400 mb-2">Notes (Optional)</label>
            <textarea v-model="form.notes" placeholder="Add notes..." rows="3" class="w-full"></textarea>
          </div>

          <button type="submit" class="btn btn-primary w-full bg-purple-700 hover:bg-purple-600" :disabled="submitting">
            {{ submitting ? 'Launching...' : 'Launch Raid' }}
          </button>
        </form>
      </div>

      <div class="lg:col-span-2">
        <div class="chart-container border-purple-700">
          <h2 class="text-xl font-semibold mb-4 text-purple-400">Active Conquests</h2>
          <div v-if="loading" class="text-center py-8 text-dark-400">Loading...</div>
          <div v-else class="space-y-3">
            <div
              v-for="trade in openTrades"
              :key="trade.id"
              class="border border-dark-700 rounded-lg p-4 hover:bg-dark-800 transition"
            >
              <div class="flex justify-between items-start mb-2">
                <div>
                  <div class="font-semibold">{{ trade.symbol }}</div>
                  <div class="text-sm" :class="trade.trade_type === 'BUY' ? 'text-positive' : 'text-negative'">{{ trade.trade_type }}</div>
                </div>
                <div class="flex items-center gap-3">
                  <!-- Live P&L -->
                  <div v-if="currentPrices[trade.symbol]" class="text-right">
                    <div class="text-xs text-dark-400">P&L</div>
                    <div class="font-semibold" :class="getTradePnL(trade) >= 0 ? 'text-positive' : 'text-negative'">
                      {{ getTradePnL(trade) >= 0 ? '+' : '' }}${{ getTradePnL(trade).toFixed(2) }}
                    </div>
                  </div>
                  <!-- R value -->
                  <div v-if="formatR(trade) !== '-'" class="text-right">
                    <div class="text-xs text-dark-400">R</div>
                    <div class="font-semibold text-secondary-400">
                      {{ formatR(trade) }}
                    </div>
                  </div>
                  <button
                    @click="selectTradeForClose(trade)"
                    class="btn btn-secondary text-sm"
                  >
                    Close
                  </button>
                </div>
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-5 gap-4 text-sm">
                <div>
                  <div class="text-dark-400">Entry Price</div>
                  <div class="font-semibold">${{ trade.entry_price.toFixed(2) }}</div>
                </div>
                <div>
                  <div class="text-dark-400">Current</div>
                  <div class="font-semibold">{{ currentPrices[trade.symbol] ? '$' + currentPrices[trade.symbol].toFixed(2) : '-' }}</div>
                </div>
                <div>
                  <div class="text-dark-400">Quantity</div>
                  <div class="font-semibold">{{ trade.quantity }}</div>
                </div>
                <div v-if="trade.stop_loss">
                  <div class="text-dark-400">Stop Loss</div>
                  <div class="font-semibold text-red-400">${{ trade.stop_loss.toFixed(2) }}</div>
                </div>
                <div v-if="trade.take_profit">
                  <div class="text-dark-400">Take Profit</div>
                  <div class="font-semibold text-green-400">${{ trade.take_profit.toFixed(2) }}</div>
                </div>
              </div>
            </div>

            <div v-if="openTrades.length === 0" class="text-center py-8 text-dark-400">
              No open positions. Create a new trade to get started.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Close Trade Modal -->
    <div v-if="tradeToClose" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="chart-container max-w-md w-full mx-4 border-purple-700">
        <h3 class="text-xl font-semibold mb-4 text-purple-400">End Your Raid</h3>
        <div class="mb-3 text-sm text-dark-400">
          {{ tradeToClose.symbol }} - {{ tradeToClose.trade_type }} @ ${{ tradeToClose.entry_price.toFixed(2) }}
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-dark-400 mb-2">Exit Price</label>
            <input v-model.number="closeForm.exitPrice" type="number" placeholder="0.00" step="0.01" class="w-full" />
          </div>
          <div class="flex gap-3">
            <button @click="closeTrade" class="btn btn-primary flex-1" :disabled="closingTrade">
              {{ closingTrade ? 'Closing...' : 'Close Trade' }}
            </button>
            <button @click="tradeToClose = null" class="btn btn-secondary flex-1">Cancel</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Closed Trades History -->
    <div class="chart-container border-purple-700">
      <h2 class="text-xl font-semibold mb-4 text-purple-400">Chronicles of Battle</h2>
      <div v-if="closedTrades.length === 0" class="text-center py-8 text-dark-400">
        No completed raids yet.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="border-b border-dark-700">
            <tr>
              <th class="text-left py-2 text-dark-400">Symbol</th>
              <th class="text-left py-2 text-dark-400">Type</th>
              <th class="text-left py-2 text-dark-400">Entry</th>
              <th class="text-left py-2 text-dark-400">Exit</th>
              <th class="text-left py-2 text-dark-400">Qty</th>
              <th class="text-left py-2 text-dark-400">P&L</th>
              <th class="text-left py-2 text-dark-400">R</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trade in closedTrades" :key="trade.id" class="border-b border-dark-800 hover:bg-dark-800 transition">
              <td class="py-3">{{ trade.symbol }}</td>
              <td class="py-3" :class="trade.trade_type === 'BUY' ? 'text-positive' : 'text-negative'">{{ trade.trade_type }}</td>
              <td class="py-3">${{ trade.entry_price.toFixed(2) }}</td>
              <td class="py-3">{{ trade.exit_price ? '$' + trade.exit_price.toFixed(2) : '-' }}</td>
              <td class="py-3">{{ trade.quantity }}</td>
              <td class="py-3 font-semibold" :class="(trade.profit_loss || 0) >= 0 ? 'text-positive' : 'text-negative'">
                {{ trade.profit_loss != null ? (trade.profit_loss >= 0 ? '+' : '') + '$' + trade.profit_loss.toFixed(2) : '-' }}
              </td>
              <td class="py-3 font-semibold text-secondary-400">
                {{ formatR(trade) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import binanceWS from '../services/websocket'

const loading = ref(true)
const submitting = ref(false)
const closingTrade = ref(false)
const openTrades = ref([])
const closedTrades = ref([])
const tradeToClose = ref(null)
const currentPrices = reactive({})
const tickerUnsubs = ref([])

const form = ref({
  symbol: '',
  trade_type: 'BUY',
  entry_price: null,
  stop_loss: null,
  take_profit: null,
  quantity: null,
  notes: ''
})

const closeForm = ref({
  exitPrice: null,
})

/**
 * Calculate unrealized P&L for an open trade
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
 * Handle ticker updates for live prices
 */
const handleTickerUpdate = (tickerData) => {
  currentPrices[tickerData.symbol] = tickerData.price
}

/**
 * Subscribe to tickers for all symbols with open trades
 */
const subscribeToTickers = async () => {
  tickerUnsubs.value.forEach(unsub => unsub())
  tickerUnsubs.value = []

  const symbols = [...new Set(openTrades.value.map(t => t.symbol))]
  if (symbols.length === 0) return

  if (!binanceWS.getStatus().connected) {
    try {
      await binanceWS.connect()
    } catch (err) {
      console.error('Failed to connect WebSocket:', err)
      return
    }
  }

  for (const symbol of symbols) {
    const unsub = binanceWS.subscribe(symbol, 'ticker', null, handleTickerUpdate)
    tickerUnsubs.value.push(unsub)
  }
}

const fetchTrades = async () => {
  try {
    const [openRes, closedRes] = await Promise.all([
      fetch('/trading/api/v1/trades/?open=true'),
      fetch('/trading/api/v1/trades/?open=false'),
    ])
    if (openRes.ok) openTrades.value = await openRes.json()
    if (closedRes.ok) closedTrades.value = await closedRes.json()
    await subscribeToTickers()
  } catch (err) {
    console.error('Failed to fetch trades:', err)
  } finally {
    loading.value = false
  }
}

const submitTrade = async () => {
  if (!form.value.symbol || !form.value.entry_price || !form.value.quantity) return

  submitting.value = true
  try {
    const response = await fetch('/trading/api/v1/trades/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: form.value.symbol,
        trade_type: form.value.trade_type,
        entry_price: form.value.entry_price,
        stop_loss: form.value.stop_loss || null,
        take_profit: form.value.take_profit || null,
        quantity: form.value.quantity,
        notes: form.value.notes || null,
      })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    form.value = { symbol: '', trade_type: 'BUY', entry_price: null, stop_loss: null, take_profit: null, quantity: null, notes: '' }
    await fetchTrades()
  } catch (err) {
    console.error('Failed to create trade:', err)
  } finally {
    submitting.value = false
  }
}

const selectTradeForClose = (trade) => {
  tradeToClose.value = trade
  closeForm.value = { exitPrice: null }
}

const closeTrade = async () => {
  if (!closeForm.value.exitPrice) return

  closingTrade.value = true
  try {
    const response = await fetch(`/trading/api/v1/trades/${tradeToClose.value.id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ exit_price: closeForm.value.exitPrice })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    tradeToClose.value = null
    await fetchTrades()
  } catch (err) {
    console.error('Failed to close trade:', err)
  } finally {
    closingTrade.value = false
  }
}

onMounted(fetchTrades)

onUnmounted(() => {
  tickerUnsubs.value.forEach(unsub => unsub())
})
</script>
