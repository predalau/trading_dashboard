<template>
  <div class="w-full relative chart-fill">
    <!-- Chart Container (always in DOM) -->
    <div
      ref="chartContainer"
      class="w-full h-full"
      :style="{ background: 'transparent', cursor: clickMode ? 'crosshair' : 'default' }"
    ></div>

    <!-- Loading/Error Overlay -->
    <div
      v-if="!chartReady"
      class="absolute inset-0 w-full h-full flex items-center justify-center bg-term-panel"
    >
      <div class="text-center">
        <p :class="error ? 'text-down' : 'text-muted'">
          {{ error ? '[ERR] ' + error : '[..] loading ' + symbol.toLowerCase() + '@kline_' + interval }}<span v-if="!error" class="cursor-text" aria-hidden="true"> _</span>
        </p>
        <button v-if="error" @click="initChart" class="t-btn-ghost mt-4">$ retry</button>
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

// Historical lazy-loading (older candles when zooming/scrolling left)
const HISTORY_LIMIT = 500
let isLoadingHistory = false
let noMoreHistory = false
let historyRangeHandler = null

/**
 * Create and size the chart
 */
/** Read a design token from :root so the chart follows the CSS theme */
const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

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
        textColor: token('--muted'),
        background: { color: 'transparent' },
        fontFamily: "'JetBrains Mono', ui-monospace, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: token('--grid') },
        horzLines: { color: token('--grid') },
      },
      crosshair: {
        vertLine: { color: token('--muted'), style: 2, labelBackgroundColor: token('--surface') },
        horzLine: { color: token('--muted'), style: 2, labelBackgroundColor: token('--surface') },
      },
      rightPriceScale: {
        borderColor: token('--line'),
      },
      timeScale: {
        borderColor: token('--line'),
        timeVisible: true,
        secondsVisible: false,
      },
    })

    candleSeries = chart.addCandlestickSeries({
      upColor: token('--up'),
      downColor: 'transparent', // hollow down candles
      borderUpColor: token('--up'),
      borderDownColor: token('--down'),
      wickUpColor: token('--up'),
      wickDownColor: token('--down'),
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
    // Reset history pagination state for this symbol/interval
    isLoadingHistory = false
    noMoreHistory = false

    // Fetch initial candles via REST
    const response = await fetch(
      `/trading/api/v1/market/klines/${props.symbol}?interval=${props.interval}&limit=${HISTORY_LIMIT}`
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
    renderTrades()
    setupClickHandler()
    setupHistoryLoader()
  } catch (err) {
    console.error('Chart data error:', err)
    error.value = err.message || 'Failed to load chart data'
  }
}

/**
 * Lazy-load older candles when the user scrolls/zooms toward the left edge.
 */
const setupHistoryLoader = () => {
  if (!chart) return
  historyRangeHandler = () => {
    if (!candleSeries || isLoadingHistory || noMoreHistory) return
    const lr = chart.timeScale().getVisibleLogicalRange()
    if (!lr) return
    const bars = candleSeries.barsInLogicalRange(lr)
    if (bars && bars.barsBefore < 10) loadOlderHistory()
  }
  chart.timeScale().subscribeVisibleLogicalRangeChange(historyRangeHandler)
}

const loadOlderHistory = async () => {
  if (isLoadingHistory || noMoreHistory || historicalData.length === 0) return
  isLoadingHistory = true
  try {
    const oldest = historicalData[0].time // seconds
    const endMs = oldest * 1000 - 1
    const resp = await fetch(
      `/trading/api/v1/market/klines/${props.symbol}?interval=${props.interval}&limit=${HISTORY_LIMIT}&end_time=${endMs}`
    )
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = await resp.json()
    const older = (data.klines || [])
      .map(k => ({ time: k.time, open: k.open, high: k.high, low: k.low, close: k.close }))
      .filter(c => c.time < oldest)
    if (older.length === 0) { noMoreHistory = true; return }

    // Preserve the current view across the setData (shift by bars prepended)
    const range = chart.timeScale().getVisibleLogicalRange()
    historicalData = older.concat(historicalData)
    candleSeries.setData(historicalData)
    if (range) {
      const added = older.length
      chart.timeScale().setVisibleLogicalRange({ from: range.from + added, to: range.to + added })
    }
    renderTrades()
    if (older.length < HISTORY_LIMIT) noMoreHistory = true
  } catch (err) {
    console.error('History load error:', err)
  } finally {
    isLoadingHistory = false
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
 * Render trade levels (price lines) and entry/exit markers on the chart.
 */
const fmtP = (p) => '$' + Number(p).toFixed(2)

// Parse a server timestamp as UTC (naive isoformat has no offset) -> unix seconds
const toSec = (iso) => {
  if (!iso) return null
  const s = /[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + 'Z'
  const ms = Date.parse(s)
  return Number.isNaN(ms) ? null : Math.floor(ms / 1000)
}

const renderTradeLines = () => {
  if (!candleSeries) return

  // Remove existing price lines
  priceLines.forEach(line => {
    try { candleSeries.removePriceLine(line) } catch {}
  })
  priceLines = []

  // Draw level lines for open positions and resting (pending) orders
  for (const trade of props.trades) {
    const isPending = trade.status === 'pending'
    if (!trade.is_open && !isPending) continue

    // Entry level (solid for open positions, dashed for resting orders)
    const entryLine = candleSeries.createPriceLine({
      price: trade.entry_price,
      color: isPending ? token('--muted') : token('--text'),
      lineWidth: 1,
      lineStyle: isPending ? 2 : 1,
      axisLabelVisible: true,
      title: `${isPending ? 'Order' : 'Entry'} ${trade.trade_type === 'BUY' ? '▲' : '▼'} ${fmtP(trade.entry_price)}`,
    })
    priceLines.push(entryLine)

    // Stop loss line
    if (trade.stop_loss) {
      const slLine = candleSeries.createPriceLine({
        price: trade.stop_loss,
        color: token('--down'),
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: `SL ${fmtP(trade.stop_loss)}`,
      })
      priceLines.push(slLine)
    }

    // Take profit line
    if (trade.take_profit) {
      const tpLine = candleSeries.createPriceLine({
        price: trade.take_profit,
        color: token('--tp'),
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: `TP ${fmtP(trade.take_profit)}`,
      })
      priceLines.push(tpLine)
    }
  }
}

/**
 * Place entry/exit markers on the time axis for this symbol's trades.
 */
const renderTradeMarkers = () => {
  if (!candleSeries) return
  const markers = []
  for (const t of props.trades) {
    if (t.status === 'pending' || t.status === 'cancelled') continue

    // Entry marker (arrow in the trade direction)
    const et = toSec(t.entry_time || t.created_at)
    if (et) {
      markers.push({
        time: et,
        position: t.trade_type === 'BUY' ? 'belowBar' : 'aboveBar',
        color: t.trade_type === 'BUY' ? token('--up') : token('--down'),
        shape: t.trade_type === 'BUY' ? 'arrowUp' : 'arrowDown',
        text: `${t.trade_type === 'BUY' ? 'LONG' : 'SHORT'} ${fmtP(t.entry_price)}`,
      })
    }

    // Exit marker (square, colored by P&L)
    const xt = toSec(t.exit_time)
    if (xt && t.exit_price != null) {
      const win = (t.profit_loss || 0) >= 0
      markers.push({
        time: xt,
        position: t.trade_type === 'BUY' ? 'aboveBar' : 'belowBar',
        color: win ? token('--up') : token('--down'),
        shape: 'square',
        text: `EXIT ${fmtP(t.exit_price)}`,
      })
    }
  }
  markers.sort((a, b) => a.time - b.time)
  try { candleSeries.setMarkers(markers) } catch (err) { console.error('Marker error:', err) }
}

const renderTrades = () => {
  renderTradeLines()
  renderTradeMarkers()
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
  if (chart && historyRangeHandler) {
    try { chart.timeScale().unsubscribeVisibleLogicalRangeChange(historyRangeHandler) } catch {}
  }
  historyRangeHandler = null
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

// Re-render trade lines + markers when trades change
watch(() => props.trades, () => {
  renderTrades()
}, { deep: true })
</script>

<style scoped>
.chart-fill {
  height: 100%;
  min-height: 420px;
}

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
