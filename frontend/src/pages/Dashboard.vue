<template>
  <div class="space-y-8 animate-fade-in">
    <section class="space-y-4">
      <h1 class="text-4xl font-bold text-purple-400">⚔️ Battle Command Center</h1>
      <p class="text-purple-400">Track your conquests and monitor your Viking trading empire</p>
    </section>

    <!-- Portfolio Overview -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="card border-purple-700">
        <div class="text-sm text-purple-400 mb-2 font-semibold">🛡️ War Chest</div>
        <div class="text-3xl font-bold text-purple-400">$50,000</div>
        <div class="text-sm text-purple-400 mt-2">Your Battle Funds</div>
      </div>

      <div class="card border-purple-700">
        <div class="text-sm text-purple-400 mb-2 font-semibold">👑 Empire Worth</div>
        <div class="text-3xl font-bold text-purple-300">$52,500</div>
        <div class="text-sm text-positive mt-2">↑ 5% Victory Gain</div>
      </div>

      <div class="card border-purple-700">
        <div class="text-sm text-purple-400 mb-2 font-semibold">⚔️ Active Raids</div>
        <div class="text-3xl font-bold text-purple-400">3</div>
        <div class="text-sm text-purple-400 mt-2">Ongoing Conquests</div>
      </div>

      <div class="card border-purple-700">
        <div class="text-sm text-purple-400 mb-2 font-semibold">⚡ Glory Rate</div>
        <div class="text-3xl font-bold text-accent-green">65%</div>
        <div class="text-sm text-purple-400 mt-2">13 Victories / 7 Defeats</div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 chart-container border-purple-700">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-semibold text-purple-400">⚡ Bitcoin Battle Chart</h2>
          <div class="flex gap-2">
            <button
              v-for="tf in timeframes"
              :key="tf.value"
              @click="selectedTimeframe = tf.value"
              :class="[
                'btn text-sm',
                selectedTimeframe === tf.value ? 'btn-primary' : 'btn-secondary'
              ]"
            >
              {{ tf.label }}
            </button>
          </div>
        </div>
        <ChartComponent symbol="BTCUSDT" :interval="selectedTimeframe" />
      </div>

      <div class="space-y-4">
        <div class="chart-container">
          <h3 class="text-lg font-semibold mb-4">⚡ Quick Stats</h3>
          <div v-if="statsLoading" class="text-center py-4 text-dark-400">
            Loading...
          </div>
          <div v-else-if="statsError" class="text-center py-4 text-red-400">
            {{ statsError }}
          </div>
          <div v-else class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-dark-400">Price</span>
              <span class="font-semibold">${{ formatNumber(stats.price) }}</span>
            </div>
            <div class="flex justify-between items-center border-t border-dark-700 pt-3">
              <span class="text-dark-400">24h High</span>
              <span class="font-semibold">${{ formatNumber(stats.high) }}</span>
            </div>
            <div class="flex justify-between items-center border-t border-dark-700 pt-3">
              <span class="text-dark-400">24h Low</span>
              <span class="font-semibold">${{ formatNumber(stats.low) }}</span>
            </div>
            <div class="flex justify-between items-center border-t border-dark-700 pt-3">
              <span class="text-dark-400">24h Volume</span>
              <span class="font-semibold">${{ formatNumber(stats.volume / 1e9) }}B</span>
            </div>
            <div class="flex justify-between items-center border-t border-dark-700 pt-3">
              <span class="text-dark-400">24h Change</span>
              <span :class="stats.price_change_percent >= 0 ? 'text-positive' : 'text-negative'" class="font-semibold">
                {{ stats.price_change_percent >= 0 ? '+' : '' }}{{ stats.price_change_percent.toFixed(2) }}%
              </span>
            </div>
          </div>
        </div>

        <div class="chart-container">
          <h3 class="text-lg font-semibold mb-4">Actions</h3>
          <div class="space-y-2">
            <button class="btn btn-success w-full">Buy Position</button>
            <button class="btn btn-danger w-full">Sell Position</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Trades -->
    <div class="chart-container">
      <h2 class="text-xl font-semibold mb-4">Recent Trades</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="border-b border-dark-700">
            <tr>
              <th class="text-left py-2 text-dark-400">Symbol</th>
              <th class="text-left py-2 text-dark-400">Type</th>
              <th class="text-left py-2 text-dark-400">Entry Price</th>
              <th class="text-left py-2 text-dark-400">Exit Price</th>
              <th class="text-left py-2 text-dark-400">P&L</th>
              <th class="text-left py-2 text-dark-400">Return</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-dark-800 hover:bg-dark-800 transition">
              <td class="py-3">BTC/USDT</td>
              <td class="py-3">Buy</td>
              <td class="py-3">$42,500</td>
              <td class="py-3">$44,200</td>
              <td class="py-3 text-positive">+$1,700</td>
              <td class="py-3 text-positive">+4.0%</td>
            </tr>
            <tr class="border-b border-dark-800 hover:bg-dark-800 transition">
              <td class="py-3">ETH/USDT</td>
              <td class="py-3">Buy</td>
              <td class="py-3">$2,300</td>
              <td class="py-3">$2,150</td>
              <td class="py-3 text-negative">-$750</td>
              <td class="py-3 text-negative">-6.5%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import ChartComponent from '../components/ChartComponent.vue'
import binanceWS from '../services/websocket'

const selectedTimeframe = ref('1h')
const statsLoading = ref(true)
const statsError = ref(null)

const stats = ref({
  price: 0,
  high: 0,
  low: 0,
  volume: 0,
  price_change_percent: 0
})

const timeframes = [
  { label: '1H', value: '1h' },
  { label: '4H', value: '4h' },
  { label: '1D', value: '1d' },
  { label: '1W', value: '1w' }
]

let wsUnsubscribe = null

const formatNumber = (num) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(2) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(2) + 'K'
  }
  return num.toFixed(2)
}

/**
 * Fetch initial stats via REST API
 */
const fetchInitialStats = async () => {
  statsLoading.value = true
  statsError.value = null

  try {
    const response = await fetch('/trading/api/v1/market/24h/BTCUSDT')

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    stats.value = data
  } catch (err) {
    statsError.value = err.message || 'Failed to load stats'
    console.error('Stats fetch error:', err)
  } finally {
    statsLoading.value = false
  }
}

/**
 * Handle real-time ticker updates from WebSocket
 */
const handleTickerUpdate = (tickerData) => {
  stats.value = {
    symbol: tickerData.symbol,
    price: tickerData.price,
    price_change: tickerData.price_change,
    price_change_percent: tickerData.price_change_percent,
    high: tickerData.high,
    low: tickerData.low,
    volume: tickerData.volume,
    quote_volume: tickerData.quote_volume
  }
}

onMounted(async () => {
  // Load initial stats
  await fetchInitialStats()

  // Connect to WebSocket if not already connected
  if (!binanceWS.getStatus().connected) {
    try {
      await binanceWS.connect()
    } catch (err) {
      console.error('Failed to connect WebSocket:', err)
      // Will continue with REST API fallback
      return
    }
  }

  // Subscribe to real-time ticker updates
  wsUnsubscribe = binanceWS.subscribe(
    'BTCUSDT',
    'ticker',
    null,
    handleTickerUpdate
  )
})

onUnmounted(() => {
  // Unsubscribe from WebSocket when component is destroyed
  if (wsUnsubscribe) {
    wsUnsubscribe()
  }
})
</script>
