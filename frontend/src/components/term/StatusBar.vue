<template>
  <footer class="status-bar" :class="{ 'status-bar-real': isRealTrading }">
    <span>[investhor] {{ windowLabel }}</span>
    <span>mode: {{ isRealTrading ? 'REAL' : 'PAPER' }}</span>
    <span v-if="equity !== null">equity: {{ formatNumber(equity) }} USDT</span>
    <span class="ml-auto">{{ clock }} UTC</span>
  </footer>
</template>

<script setup>
import { computed, inject, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  items: { type: Array, required: true },
})

const route = useRoute()
const isRealTrading = inject('isRealTrading')
const equity = ref(null)
const clock = ref('')
let timer = null

const windowLabel = computed(() => {
  const i = props.items.findIndex(item =>
    item.to === '/' ? route.path === '/' : route.path.startsWith(item.to)
  )
  return i === -1 ? '' : `${i}:${props.items[i].label}*`
})

const formatNumber = (n) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

const tick = () => {
  clock.value = new Date().toISOString().slice(0, 16).replace('T', ' ')
}

const fetchEquity = async () => {
  try {
    const res = await fetch('/trading/api/v1/paper-trading/accounts')
    if (!res.ok) return
    const accounts = await res.json()
    if (accounts.length > 0) equity.value = accounts[0].current_balance
  } catch (err) {
    console.error('Status bar failed to fetch equity:', err)
  }
}

// Refresh equity when the page changes, since trades are placed and closed on other pages
watch(() => route.path, fetchEquity)

onMounted(() => {
  tick()
  timer = setInterval(tick, 30000)
  fetchEquity()
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.status-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 24px;
  padding: 8px 28px;
  background: var(--accent);
  color: var(--on-accent);
  font-size: 12px;
  font-weight: 700;
}

.status-bar-real {
  background: var(--down);
}

@media (max-width: 767px) {
  .status-bar {
    padding: 6px 16px;
    font-size: 11px;
  }
}
</style>
