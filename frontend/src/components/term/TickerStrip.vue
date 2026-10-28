<template>
  <div class="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-muted" aria-label="Live prices">
    <span v-for="t in tickers" :key="t.symbol">
      {{ t.base }}
      <span v-if="t.price !== null" :class="t.change >= 0 ? 'text-up' : 'text-down'">
        {{ formatPrice(t.price) }} {{ t.change >= 0 ? '▲' : '▼' }}{{ Math.abs(t.change).toFixed(2) }}
      </span>
      <span v-else>--</span>
    </span>
    <span>ws <span :class="connected ? 'text-accent' : 'text-down'" :aria-label="connected ? 'connected' : 'disconnected'">●</span></span>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted } from 'vue'
import binanceWS from '../../services/websocket'

const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

const tickers = reactive(SYMBOLS.map(symbol => ({
  symbol,
  base: symbol.replace('USDT', ''),
  price: null,
  change: 0,
})))
const connected = ref(false)
let unsubs = []
let statusTimer = null

const formatPrice = (p) => p.toLocaleString('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: p < 10 ? 4 : 2,
})

const onTicker = (data) => {
  const t = tickers.find(x => x.symbol === data.symbol)
  if (!t) return
  t.price = data.price
  t.change = data.price_change_percent
}

onMounted(async () => {
  statusTimer = setInterval(() => { connected.value = binanceWS.getStatus().connected }, 2000)
  try {
    await binanceWS.connect()
  } catch (err) {
    console.error('Ticker strip failed to connect:', err)
  }
  connected.value = binanceWS.getStatus().connected
  unsubs = SYMBOLS.map(s => binanceWS.subscribe(s, 'ticker', null, onTicker))
})

onUnmounted(() => {
  unsubs.forEach(unsub => unsub())
  clearInterval(statusTimer)
})
</script>
