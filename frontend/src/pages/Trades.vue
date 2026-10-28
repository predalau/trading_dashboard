<template>
  <div class="flex flex-col gap-5">
    <h1 class="sr-only">Trades</h1>

    <div class="flex flex-wrap gap-5">
      <!-- New Trade Form -->
      <TermPanel title="new_order.sh" tone="surface" class="order-column">
        <form @submit.prevent="submitTrade" class="flex flex-col gap-3">
          <div class="flex items-center gap-2.5">
            <label for="trade-symbol" class="w-24 shrink-0 text-muted">--symbol</label>
            <select id="trade-symbol" v-model="form.symbol" class="t-input flex-1">
              <option value="">select</option>
              <option value="BTCUSDT">BTC/USDT</option>
              <option value="ETHUSDT">ETH/USDT</option>
              <option value="BNBUSDT">BNB/USDT</option>
              <option value="SOLUSDT">SOL/USDT</option>
              <option value="XRPUSDT">XRP/USDT</option>
            </select>
          </div>

          <div class="flex gap-2" role="group" aria-label="Side">
            <button
              type="button"
              @click="form.trade_type = 'BUY'"
              class="flex-1"
              :class="form.trade_type === 'BUY' ? 't-btn' : 't-btn-ghost'"
              :aria-pressed="form.trade_type === 'BUY'"
            >LONG</button>
            <button
              type="button"
              @click="form.trade_type = 'SELL'"
              class="flex-1 font-extrabold"
              :class="form.trade_type === 'SELL' ? 't-btn-short' : 't-btn-ghost'"
              :aria-pressed="form.trade_type === 'SELL'"
            >SHORT</button>
          </div>

          <div v-for="field in fields" :key="field.key" class="flex items-center gap-2.5">
            <label :for="'trade-' + field.key" class="w-24 shrink-0 text-muted">{{ field.flag }}</label>
            <input
              :id="'trade-' + field.key"
              v-model.number="form[field.key]"
              type="number"
              :step="field.step"
              placeholder="0.00"
              class="t-input flex-1"
              :class="field.color"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <label for="trade-notes" class="text-muted">--notes (optional)</label>
            <textarea id="trade-notes" v-model="form.notes" placeholder="# why this trade" rows="3" class="t-input"></textarea>
          </div>

          <button type="submit" class="t-btn justify-start py-3.5" :disabled="submitting">
            {{ submitting ? '$ executing...' : '$ ./execute --' + (isRealTrading ? 'real' : 'paper') + ' ⏎' }}
          </button>
        </form>
      </TermPanel>

      <!-- Open positions -->
      <TermPanel title="ps --positions" flush class="positions-column">
        <template #meta>
          <span>{{ openTrades.length }} running</span>
        </template>
        <div v-if="loading" class="px-3.5 py-4 text-muted">[..] loading<span class="cursor-text" aria-hidden="true"> _</span></div>
        <div v-else-if="openTrades.length === 0" class="px-3.5 py-4 text-muted">
          no running positions, place an order to start one
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
                <td class="text-muted">0x{{ Number(trade.id).toString(16) }}</td>
                <td>{{ trade.symbol }}</td>
                <td :class="trade.trade_type === 'BUY' ? 'text-up' : 'text-down'">
                  {{ trade.trade_type === 'BUY' ? 'LONG' : 'SHORT' }}
                </td>
                <td>{{ trade.entry_price.toFixed(2) }}</td>
                <td>{{ currentPrices[trade.symbol] ? currentPrices[trade.symbol].toFixed(2) : '--' }}</td>
                <td class="text-down">{{ trade.stop_loss ? trade.stop_loss.toFixed(2) : '--' }}</td>
                <td class="text-tp">{{ trade.take_profit ? trade.take_profit.toFixed(2) : '--' }}</td>
                <td>{{ trade.quantity }}</td>
                <td class="font-bold" :class="getTradePnL(trade) >= 0 ? 'text-up' : 'text-down'">
                  {{ currentPrices[trade.symbol] ? (getTradePnL(trade) >= 0 ? '+' : '') + getTradePnL(trade).toFixed(2) : '--' }}
                </td>
                <td>{{ formatR(trade) }}</td>
                <td>
                  <button @click="selectTradeForClose(trade)" class="t-btn-danger">close</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </TermPanel>
    </div>

    <!-- Close Trade Modal -->
    <div
      v-if="tradeToClose"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4"
      @click.self="tradeToClose = null"
      @keydown.esc="tradeToClose = null"
    >
      <TermPanel title="close_position.sh" tone="surface" class="w-full max-w-md" role="dialog" aria-modal="true" aria-label="Close position">
        <form class="flex flex-col gap-3" @submit.prevent="closeTrade">
          <div class="text-muted">
            0x{{ Number(tradeToClose.id).toString(16) }} · {{ tradeToClose.symbol }}
            <span :class="tradeToClose.trade_type === 'BUY' ? 'text-up' : 'text-down'">{{ tradeToClose.trade_type === 'BUY' ? 'LONG' : 'SHORT' }}</span>
            @ {{ tradeToClose.entry_price.toFixed(2) }}
          </div>
          <div class="flex items-center gap-2.5">
            <label for="close-exit" class="w-24 shrink-0 text-muted">--exit</label>
            <input id="close-exit" v-model.number="closeForm.exitPrice" type="number" placeholder="0.00" step="0.01" class="t-input flex-1" autofocus />
          </div>
          <div class="flex gap-2">
            <button type="submit" class="t-btn flex-1" :disabled="closingTrade">
              {{ closingTrade ? 'closing...' : '$ ./close ⏎' }}
            </button>
            <button type="button" @click="tradeToClose = null" class="t-btn-ghost flex-1">esc</button>
          </div>
        </form>
      </TermPanel>
    </div>

    <!-- Closed Trades History -->
    <HistoryTable :trades="closedTrades" />
  </div>
</template>

<script setup>
import { ref, reactive, inject, onMounted, onUnmounted } from 'vue'
import binanceWS from '../services/websocket'
import TermPanel from '../components/term/TermPanel.vue'
import HistoryTable from '../components/term/HistoryTable.vue'
import { useLogStore } from '../stores/log'

const isRealTrading = inject('isRealTrading')
const log = useLogStore()

const fields = [
  { key: 'entry_price', flag: '--entry', step: '0.01', color: '' },
  { key: 'stop_loss', flag: '--sl', step: '0.01', color: 'text-down' },
  { key: 'take_profit', flag: '--tp', step: '0.01', color: 'text-tp' },
  { key: 'quantity', flag: '--qty', step: '0.001', color: '' },
]

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
  if (r === null) return '--'
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

    const f = form.value
    log.push('FILL', `${f.trade_type === 'BUY' ? 'LONG' : 'SHORT'} ${f.quantity} ${f.symbol} @ ${f.entry_price}`)
    form.value = { symbol: '', trade_type: 'BUY', entry_price: null, stop_loss: null, take_profit: null, quantity: null, notes: '' }
    await fetchTrades()
  } catch (err) {
    log.push('ERR', `order rejected: ${err.message}`)
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

    log.push('FILL', `closed position 0x${Number(tradeToClose.value.id).toString(16)} @ ${closeForm.value.exitPrice}`)
    tradeToClose.value = null
    await fetchTrades()
  } catch (err) {
    log.push('ERR', `close failed: ${err.message}`)
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

<style scoped>
.order-column {
  flex: 1 1 320px;
}

.positions-column {
  flex: 999 1 560px;
}

.t-btn-short {
  @apply inline-flex items-center justify-center px-3.5 py-2.5 cursor-pointer;
  background: var(--down);
  color: var(--on-accent);
  border: 1px solid var(--down);
}
</style>
