<template>
  <div class="space-y-8 animate-fade-in">
    <section class="space-y-4">
      <h1 class="text-4xl font-bold text-purple-400">Warrior Profile</h1>
      <p class="text-purple-400">Your trading empire at a glance</p>
    </section>

    <!-- Portfolio Overview -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="card border-purple-700">
        <div class="text-sm text-purple-400 mb-2 font-semibold">War Chest</div>
        <div class="text-3xl font-bold text-purple-400">${{ formatNumber(account.current_balance) }}</div>
        <div class="text-sm text-purple-400 mt-2">Your Battle Funds</div>
      </div>

      <div class="card border-purple-700">
        <div class="text-sm text-purple-400 mb-2 font-semibold">Empire Worth</div>
        <div class="text-3xl font-bold text-purple-300">${{ formatNumber(account.initial_balance + totalPnL) }}</div>
        <div class="text-sm mt-2" :class="totalPnL >= 0 ? 'text-positive' : 'text-negative'">
          {{ totalPnL >= 0 ? '+' : '' }}{{ ((totalPnL / account.initial_balance) * 100).toFixed(1) }}% {{ totalPnL >= 0 ? 'Victory Gain' : 'Battle Loss' }}
        </div>
      </div>

      <div class="card border-purple-700">
        <div class="text-sm text-purple-400 mb-2 font-semibold">Active Raids</div>
        <div class="text-3xl font-bold text-purple-400">{{ activeTradesCount }}</div>
        <div class="text-sm text-purple-400 mt-2">Ongoing Conquests</div>
      </div>

      <div class="card border-purple-700">
        <div class="text-sm text-purple-400 mb-2 font-semibold">Glory Rate</div>
        <div class="text-3xl font-bold" :class="winRate >= 50 ? 'text-accent-green' : 'text-red-400'">{{ winRate.toFixed(0) }}%</div>
        <div class="text-sm text-purple-400 mt-2">{{ wins }} Victories / {{ losses }} Defeats</div>
      </div>
    </div>

    <!-- User Info -->
    <div class="chart-container">
      <h2 class="text-xl font-semibold mb-4">Warrior Info</h2>
      <div v-if="loading" class="text-center py-4 text-dark-400">Loading...</div>
      <div v-else class="space-y-3">
        <div class="flex justify-between items-center">
          <span class="text-dark-400">Account</span>
          <span class="font-semibold">{{ account.account_name || 'Viking Trader' }}</span>
        </div>
        <div class="flex justify-between items-center border-t border-dark-700 pt-3">
          <span class="text-dark-400">Initial Balance</span>
          <span class="font-semibold">${{ formatNumber(account.initial_balance) }}</span>
        </div>
        <div class="flex justify-between items-center border-t border-dark-700 pt-3">
          <span class="text-dark-400">Current Balance</span>
          <span class="font-semibold">${{ formatNumber(account.current_balance) }}</span>
        </div>
        <div class="flex justify-between items-center border-t border-dark-700 pt-3">
          <span class="text-dark-400">Total Trades</span>
          <span class="font-semibold">{{ wins + losses + activeTradesCount }}</span>
        </div>
      </div>
    </div>

    <!-- Closed Trades History -->
    <div v-if="closedTrades.length > 0" class="chart-container">
      <h2 class="text-xl font-semibold mb-4">Battle History</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="border-b border-dark-700">
            <tr>
              <th class="text-left py-2 text-dark-400">Symbol</th>
              <th class="text-left py-2 text-dark-400">Side</th>
              <th class="text-left py-2 text-dark-400">Entry</th>
              <th class="text-left py-2 text-dark-400">Exit</th>
              <th class="text-left py-2 text-dark-400">Qty</th>
              <th class="text-left py-2 text-dark-400">P&L</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trade in closedTrades" :key="trade.id" class="border-b border-dark-800 hover:bg-dark-800 transition">
              <td class="py-3">{{ trade.symbol }}</td>
              <td class="py-3" :class="trade.trade_type === 'BUY' ? 'text-positive' : 'text-negative'">
                {{ trade.trade_type }}
              </td>
              <td class="py-3">${{ trade.entry_price.toFixed(2) }}</td>
              <td class="py-3">{{ trade.exit_price ? '$' + trade.exit_price.toFixed(2) : '-' }}</td>
              <td class="py-3">{{ trade.quantity }}</td>
              <td class="py-3 font-semibold" :class="(trade.profit_loss || 0) >= 0 ? 'text-positive' : 'text-negative'">
                {{ trade.profit_loss != null ? (trade.profit_loss >= 0 ? '+' : '') + '$' + trade.profit_loss.toFixed(2) : '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const loading = ref(true)
const account = ref({
  account_name: '',
  initial_balance: 50000,
  current_balance: 50000,
})
const closedTrades = ref([])
const activeTradesCount = ref(0)

const wins = computed(() => closedTrades.value.filter(t => (t.profit_loss || 0) > 0).length)
const losses = computed(() => closedTrades.value.filter(t => (t.profit_loss || 0) <= 0).length)
const winRate = computed(() => {
  const total = wins.value + losses.value
  return total > 0 ? (wins.value / total) * 100 : 0
})
const totalPnL = computed(() => closedTrades.value.reduce((sum, t) => sum + (t.profit_loss || 0), 0))

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
