<template>
  <div class="flex flex-col gap-5">
    <h1 class="sr-only">Profile</h1>

    <!-- Stats -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div v-for="stat in stats" :key="stat.label" class="bg-term-surface border border-term-line p-4">
        <div class="text-muted text-[11px] uppercase tracking-[0.12em]">{{ stat.label }}</div>
        <div class="mt-1.5 text-[22px] font-bold" :class="stat.class">{{ stat.value }}</div>
        <div class="mt-1 text-muted text-xs">{{ stat.note }}</div>
      </div>
    </div>

    <!-- User Info -->
    <TermPanel title="whoami">
      <div v-if="loading" class="text-muted">[..] loading<span class="cursor-text" aria-hidden="true"> _</span></div>
      <dl v-else class="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2">
        <dt class="text-muted">account:</dt>
        <dd>{{ account.account_name || 'paper-account' }}</dd>
        <dt class="text-muted">mode:</dt>
        <dd :class="isRealTrading ? 'text-down' : 'text-accent'">{{ isRealTrading ? 'REAL' : 'PAPER' }}</dd>
        <dt class="text-muted">initial_balance:</dt>
        <dd>{{ formatNumber(account.initial_balance) }} USDT</dd>
        <dt class="text-muted">current_balance:</dt>
        <dd>{{ formatNumber(account.current_balance) }} USDT</dd>
        <dt class="text-muted">total_trades:</dt>
        <dd>{{ wins + losses + activeTradesCount }}</dd>
        <template v-if="account.created_at">
          <dt class="text-muted">created:</dt>
          <dd>{{ account.created_at.slice(0, 10) }}</dd>
        </template>
      </dl>
    </TermPanel>

    <!-- Closed Trades History -->
    <HistoryTable :trades="closedTrades" />
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import TermPanel from '../components/term/TermPanel.vue'
import HistoryTable from '../components/term/HistoryTable.vue'

const isRealTrading = inject('isRealTrading')

const loading = ref(true)
const account = ref({
  account_name: '',
  initial_balance: 50000,
  current_balance: 50000,
})
const closedTrades = ref([])
const activeTradesCount = ref(0)

// The API does not return profit_loss yet, so derive it from the exit price
const pnl = (t) => {
  if (t.profit_loss != null) return t.profit_loss
  if (t.exit_price == null) return 0
  const diff = t.exit_price - t.entry_price
  return (t.trade_type === 'BUY' ? diff : -diff) * t.quantity
}

const wins = computed(() => closedTrades.value.filter(t => pnl(t) > 0).length)
const losses = computed(() => closedTrades.value.filter(t => pnl(t) <= 0).length)
const winRate = computed(() => {
  const total = wins.value + losses.value
  return total > 0 ? (wins.value / total) * 100 : 0
})
const totalPnL = computed(() => closedTrades.value.reduce((sum, t) => sum + pnl(t), 0))

// Average realized R over closed trades that had a stop loss
const avgR = computed(() => {
  const rs = closedTrades.value
    .filter(t => t.stop_loss && t.exit_price != null && t.entry_price !== t.stop_loss)
    .map(t => pnl(t) / (Math.abs(t.entry_price - t.stop_loss) * t.quantity))
  return rs.length ? rs.reduce((a, b) => a + b, 0) / rs.length : null
})

const stats = computed(() => {
  const pct = account.value.initial_balance ? (totalPnL.value / account.value.initial_balance) * 100 : 0
  return [
    { label: 'equity', value: formatNumber(account.value.current_balance), note: 'USDT', class: '' },
    {
      label: 'total p&l',
      value: (totalPnL.value >= 0 ? '+' : '') + formatNumber(totalPnL.value),
      note: (pct >= 0 ? '+' : '') + pct.toFixed(1) + '% of initial',
      class: totalPnL.value >= 0 ? 'text-up' : 'text-down',
    },
    { label: 'win rate', value: winRate.value.toFixed(0) + '%', note: `${wins.value} wins / ${losses.value} losses`, class: '' },
    {
      label: 'avg r',
      value: avgR.value === null ? '--' : (avgR.value >= 0 ? '+' : '') + avgR.value.toFixed(2) + 'R',
      note: `${activeTradesCount.value} open now`,
      class: avgR.value === null ? '' : avgR.value >= 0 ? 'text-up' : 'text-down',
    },
  ]
})

const formatNumber = (num) => {
  if (!num && num !== 0) return '0.00'
  if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M'
  if (num >= 1000) return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return num.toFixed(2)
}

const fetchData = async () => {
  loading.value = true
  try {
    const [accountRes, closedRes, openRes] = await Promise.all([
      fetch('/trading/api/v1/paper-trading/accounts'),
      fetch('/trading/api/v1/trades/?open=false'),
      fetch('/trading/api/v1/trades/?open=true'),
    ])

    if (accountRes.ok) {
      const accounts = await accountRes.json()
      if (accounts.length > 0) account.value = accounts[0]
    }
    if (closedRes.ok) closedTrades.value = await closedRes.json()
    if (openRes.ok) {
      const openTrades = await openRes.json()
      activeTradesCount.value = openTrades.length
    }
  } catch (err) {
    console.error('Failed to fetch profile data:', err)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
