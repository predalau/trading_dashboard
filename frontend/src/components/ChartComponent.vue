<template>
  <div class="w-full h-96 relative">
    <!-- Chart Container (always in DOM) -->
    <div
      ref="chartContainer"
      class="w-full h-full rounded-lg"
      :style="{ background: 'transparent', cursor: clickMode ? 'crosshair' : 'default' }"
    ></div>

    <!-- Loading/Error Overlay -->
    <div
      v-if="!chartReady"
      class="absolute inset-0 w-full h-full flex items-center justify-center bg-dark-800 bg-opacity-80 rounded-lg"
    >
      <div class="text-center">
        <div class="inline-block animate-pulse mb-2">⚡</div>
        <p class="text-dark-400">{{ error || 'Loading battle chart...' }}</p>
        <button v-if="error" @click="initChart" class="btn btn-primary text-sm mt-4">Retry</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { createChart } from 'lightweight-charts'
import binanceWS from '@/services/websocket'

const props = defineProps({
  symbol: { type: String, required: true },
  interval: { type: String, default: '1h' },
  trades: { type: Array, default: () => [] },
  clickMode: { type: String, default: null } // 'entry', 'sl', 'tp', or null
})

const emit = defineEmits(['chart-click'])

const chartContainer = ref(null)
const chartReady = ref(false)
const error = ref(null)

let chart = null
let candleSeries = null
let wsUnsubscribe = null
let historicalData = []
let resizeObserver = null
let priceLines = [] // Track active price lines for cleanup

/**
 * Create and size the chart
 */
const createChartInstance = () => {
  if (!chartContainer.value) {
    console.error('Chart container not found')
    return false
  }

  try {
    const container = chartContainer.value
    const width = container.clientWidth
    const height = container.clientHeight

    chart = createChart(container, {
      width,
      height,
      layout: {
        textColor: '#94a3b8',
        background: { color: 'transparent' },
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    })

    candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    })

    // Handle container resize
    resizeObserver = new ResizeObserver(() => {
      if (chartContainer.value && chart) {
        const newWidth = chartContainer.value.clientWidth
        const newHeight = chartContainer.value.clientHeight
        if (newWidth > 0 && newHeight > 0) {
          chart.applyOptions({ width: newWidth, height: newHeight })
        }
      }
    })
    resizeObserver.observe(container)

    return true
  } catch (err) {
    console.error('Chart creation error:', err)
    error.value = 'Failed to create chart'
    return false
  }
}

/**
 * Load initial historical data and setup real-time updates
 */
const loadChartData = async () => {
  if (!chart || !candleSeries) {
    error.value = 'Chart not initialized'
    return
  }

  try {
    // Fetch initial candles via REST
    const response = await fetch(
      `/trading/api/v1/market/klines/${props.symbol}?interval=${props.interval}&limit=100`
    )

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const data = await response.json()
    historicalData = data.klines.map(kline => ({
      time: kline.time,
      open: kline.open,
      high: kline.high,
      low: kline.low,
      close: kline.close
    }))

    // Validate data
    const isValid = historicalData.every(c =>
      typeof c.time === 'number' && typeof c.open === 'number' &&
      typeof c.high === 'number' && typeof c.low === 'number' && typeof c.close === 'number'
    )

    if (!isValid) throw new Error('Invalid candle data format')

    // Load data into chart
    candleSeries.setData(historicalData)

    // Fit to visible range
    try {
      chart.timeScale().fitContent()
    } catch (fitErr) {
      if (historicalData.length > 0) {
        const range = {
          from: historicalData[0].time,
          to: historicalData[historicalData.length - 1].time
        }
        chart.timeScale().setVisibleRange(range)
      }
    }

    // Subscribe to WebSocket for real-time trade updates and build candles
    wsUnsubscribe = binanceWS.subscribe(
      props.symbol,
      'aggTrade',
      null,
      handleTradeUpdate
    )

    chartReady.value = true
    error.value = null

    // Render trade positions and setup click handler
    renderTradeLines()
    setupClickHandler()
  } catch (err) {
    console.error('Chart data error:', err)
    error.value = err.message || 'Failed to load chart data'
  }
}

/**
 * Convert interval string to milliseconds
 */
const getIntervalMs = (interval) => {
  const unit = interval.slice(-1)
  const value = parseInt(interval.slice(0, -1))

  const unitMs = {
    'm': 60 * 1000,
    'h': 60 * 60 * 1000,
    'd': 24 * 60 * 60 * 1000,
    'w': 7 * 24 * 60 * 60 * 1000
  }

  return value * (unitMs[unit] || 1)
}

/**
 * Build candles from individual trades
 */
const handleTradeUpdate = (trade) => {
  if (!candleSeries) return

  try {
    const tradeTime = Math.floor(trade.time / 1000) // Convert ms to seconds
    const intervalMs = getIntervalMs(props.interval)
    const intervalSec = intervalMs / 1000

    // Calculate candle time based on interval
    const candleTime = Math.floor(tradeTime / intervalSec) * intervalSec
    const price = parseFloat(trade.price)

    const lastCandle = historicalData[historicalData.length - 1]

    if (!lastCandle || candleTime > lastCandle.time) {
      // New candle
      const newCandle = {
        time: candleTime,
        open: price,
        high: price,
        low: price,
        close: price,
        volume: parseFloat(trade.qty)
      }
      candleSeries.update(newCandle)
      historicalData.push(newCandle)
    } else if (candleTime === lastCandle.time) {
      // Update existing candle
      lastCandle.high = Math.max(lastCandle.high, price)
      lastCandle.low = Math.min(lastCandle.low, price)
      lastCandle.close = price
      lastCandle.volume += parseFloat(trade.qty)
      candleSeries.update(lastCandle)
    }
  } catch (err) {
    console.error('Trade update error:', err)
  }
}

/**
 * Render trade positions as price lines on the chart
 */
const renderTradeLines = () => {
  if (!candleSeries) return

  // Remove existing price lines
  priceLines.forEach(line => {
    try { candleSeries.removePriceLine(line) } catch {}
  })
  priceLines = []

  // Draw lines for each trade
  for (const trade of props.trades) {
    if (!trade.is_open) continue

    // Entry line
    const entryLine = candleSeries.createPriceLine({
      price: trade.entry_price,
      color: '#facc15',
      lineWidth: 2,
      lineStyle: 2, // Dashed
      axisLabelVisible: true,
      title: `Entry ${trade.trade_type === 'BUY' ? '▲' : '▼'} $${trade.entry_price.toFixed(2)}`,
    })
    priceLines.push(entryLine)

    // Stop loss line
    if (trade.stop_loss) {
      const slLine = candleSeries.createPriceLine({
        price: trade.stop_loss,
        color: '#ef4444',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: `SL $${trade.stop_loss.toFixed(2)}`,
      })
      priceLines.push(slLine)
    }

    // Take profit line
    if (trade.take_profit) {
      const tpLine = candleSeries.createPriceLine({
        price: trade.take_profit,
        color: '#10b981',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: `TP $${trade.take_profit.toFixed(2)}`,
      })
      priceLines.push(tpLine)
    }
  }
}

/**
 * Handle chart click for click-to-set mode
 */
const setupClickHandler = () => {
  if (!chart || !candleSeries) return

  chart.subscribeClick((param) => {
    if (!props.clickMode || !param.point) return

    const price = candleSeries.coordinateToPrice(param.point.y)
    if (price && price > 0) {
      emit('chart-click', { mode: props.clickMode, price: parseFloat(price.toFixed(2)) })
    }
  })
}

/**
 * Initialize chart and connect to data
 */
const initChart = async () => {
  chartReady.value = false
  error.value = null

  // Ensure WebSocket is connected
  if (!binanceWS.getStatus().connected) {
    try {
      await binanceWS.connect()
    } catch (err) {
      console.error('WebSocket connection failed:', err)
      error.value = 'Cannot connect to real-time data'
      return
    }
  }

  // Wait for DOM to be ready
  await nextTick()

  // Create chart with proper sizing
  if (!createChartInstance()) {
    return
  }

  // Load historical data and start real-time updates
  await loadChartData()
}

/**
 * Cleanup on unmount
 */
const cleanup = () => {
  if (wsUnsubscribe) wsUnsubscribe()
  if (resizeObserver) resizeObserver.disconnect()
  if (chart) chart.remove()
}

onMounted(initChart)
onUnmounted(cleanup)

// Re-initialize when symbol or interval changes
watch(() => props.symbol, () => {
  cleanup()
  initChart()
})

watch(() => props.interval, () => {
  cleanup()
  initChart()
})

// Re-render trade lines when trades change
watch(() => props.trades, () => {
  renderTradeLines()
}, { deep: true })
</script>

<style scoped>
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
