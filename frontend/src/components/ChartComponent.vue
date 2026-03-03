<template>
  <div class="w-full">
    <div ref="chartContainer" class="w-full" style="height: 400px;"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { createChart } from 'lightweight-charts'

const props = defineProps({
  symbol: {
    type: String,
    required: true
  }
})

const chartContainer = ref(null)
let chart = null
let candleSeries = null

const sampleData = [
  { time: '2024-01-01', open: 42500, high: 43200, low: 42100, close: 43000 },
  { time: '2024-01-02', open: 43000, high: 44000, low: 42800, close: 43800 },
  { time: '2024-01-03', open: 43800, high: 44500, low: 43500, close: 44200 },
  { time: '2024-01-04', open: 44200, high: 44800, low: 43900, close: 44500 },
  { time: '2024-01-05', open: 44500, high: 45200, low: 44200, close: 44900 },
  { time: '2024-01-06', open: 44900, high: 45500, low: 44600, close: 45200 },
  { time: '2024-01-07', open: 45200, high: 45800, low: 45000, close: 45500 },
  { time: '2024-01-08', open: 45500, high: 45900, low: 45100, close: 45600 },
  { time: '2024-01-09', open: 45600, high: 46200, low: 45400, close: 45900 },
  { time: '2024-01-10', open: 45900, high: 46500, low: 45700, close: 46200 },
]

const initChart = () => {
  if (!chartContainer.value) return

  // Create chart
  chart = createChart(chartContainer.value, {
    layout: {
      textColor: '#94a3b8',
      background: {
        color: 'transparent',
      },
    },
    grid: {
      vertLines: {
        color: '#1e293b',
      },
      horzLines: {
        color: '#1e293b',
      },
    },
    timeScale: {
      timeVisible: true,
      secondsVisible: false,
    },
    width: chartContainer.value.clientWidth,
    height: 400,
  })

  // Create candle series
  candleSeries = chart.addCandlestickSeries({
    upColor: '#10b981',
    downColor: '#ef4444',
    borderUpColor: '#10b981',
    borderDownColor: '#ef4444',
    wickUpColor: '#10b981',
    wickDownColor: '#ef4444',
  })

  // Set data
  candleSeries.setData(sampleData)

  // Fit content
  chart.timeScale().fitContent()

  // Handle window resize
  const handleResize = () => {
    if (chartContainer.value) {
      chart.applyOptions({
        width: chartContainer.value.clientWidth,
      })
    }
  }

  window.addEventListener('resize', handleResize)
}

onMounted(() => {
  initChart()
})

watch(
  () => props.symbol,
  () => {
    // Reload chart data for new symbol
    if (candleSeries) {
      candleSeries.setData(sampleData)
      chart.timeScale().fitContent()
    }
  }
)
</script>

<style scoped>
</style>
