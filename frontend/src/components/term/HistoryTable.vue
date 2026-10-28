<template>
  <TermPanel title="cat history.log" flush>
    <template #meta>
      <span>{{ trades.length }} closed</span>
    </template>
    <div v-if="trades.length === 0" class="px-3.5 py-4 text-muted">
      history.log is empty, no closed trades yet
    </div>
    <div v-else class="overflow-x-auto">
      <table class="t-table">
        <thead>
          <tr>
            <th>PID</th>
            <th>Opened</th>
            <th>Symbol</th>
            <th>Side</th>
            <th>Entry</th>
            <th>Exit</th>
            <th>Qty</th>
            <th>P&amp;L</th>
            <th v-if="showR">R</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="trade in sorted" :key="trade.id">
            <td class="text-muted">0x{{ Number(trade.id).toString(16) }}</td>
            <td class="text-muted">{{ formatDate(trade.entry_time) }}</td>
            <td>{{ trade.symbol }}</td>
            <td :class="trade.trade_type === 'BUY' ? 'text-up' : 'text-down'">
              {{ trade.trade_type === 'BUY' ? 'LONG' : 'SHORT' }}
            </td>
            <td>{{ trade.entry_price.toFixed(2) }}</td>
            <td>{{ trade.exit_price ? trade.exit_price.toFixed(2) : '--' }}</td>
            <td>{{ trade.quantity }}</td>
            <td class="font-bold" :class="(pnl(trade) || 0) >= 0 ? 'text-up' : 'text-down'">
              {{ pnl(trade) != null ? (pnl(trade) >= 0 ? '+' : '') + pnl(trade).toFixed(2) : '--' }}
            </td>
            <td v-if="showR">{{ formatR(trade) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </TermPanel>
</template>

<script setup>
import { computed } from 'vue'
import TermPanel from './TermPanel.vue'

const props = defineProps({
  trades: { type: Array, required: true },
  showR: { type: Boolean, default: true },
})

// Newest first
const sorted = computed(() => [...props.trades].sort((a, b) => {
  const ta = new Date(a.entry_time || 0).getTime()
  const tb = new Date(b.entry_time || 0).getTime()
  return tb - ta || b.id - a.id
}))

// The API does not return profit_loss yet, so derive it from the exit price
const pnl = (trade) => {
  if (trade.profit_loss != null) return trade.profit_loss
  if (trade.exit_price == null) return null
  const diff = trade.exit_price - trade.entry_price
  return (trade.trade_type === 'BUY' ? diff : -diff) * trade.quantity
}

const formatDate = (value) => {
  if (!value) return '--'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '--'
  return d.toISOString().slice(0, 16).replace('T', ' ')
}

const formatR = (trade) => {
  if (!trade.stop_loss || !trade.take_profit) return '--'
  const risk = Math.abs(trade.entry_price - trade.stop_loss)
  if (risk === 0) return '--'
  return (Math.abs(trade.take_profit - trade.entry_price) / risk).toFixed(2) + 'R'
}
</script>
