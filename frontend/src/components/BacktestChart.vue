<template>
  <div class="w-full relative" style="height: 360px">
    <div ref="el" class="w-full h-full"></div>
    <div v-if="!bars.length" class="absolute inset-0 flex items-center justify-center text-muted">
      no price data
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { createChart } from 'lightweight-charts'

const props = defineProps({
  bars: { type: Array, default: () => [] },     // [{ ts(ms), open, high, low, close }]
  trades: { type: Array, default: () => [] },   // [{ entry_ts, entry_price, exit_ts, exit_price, pnl }]
})

const el = ref(null)
let chart = null
let series = null
let ro = null

const token = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim()
const fmt = (p) => '$' + Number(p).toFixed(2)

const destroy = () => {
  if (ro) { ro.disconnect(); ro = null }
  if (chart) { chart.remove(); chart = null; series = null }
}

const build = () => {
  if (!el.value || !props.bars.length) return
  destroy()

  chart = createChart(el.value, {
    width: el.value.clientWidth,
    height: el.value.clientHeight,
    layout: {
      textColor: token('--muted'),
      background: { color: 'transparent' },
      fontFamily: "'JetBrains Mono', ui-monospace, monospace",
      fontSize: 11,
    },
    grid: { vertLines: { color: token('--grid') }, horzLines: { color: token('--grid') } },
    rightPriceScale: { borderColor: token('--line') },
    timeScale: { borderColor: token('--line'), timeVisible: true, secondsVisible: false },
  })

  series = chart.addCandlestickSeries({
    upColor: token('--up'),
    downColor: 'transparent',
    borderUpColor: token('--up'),
    borderDownColor: token('--down'),
    wickUpColor: token('--up'),
    wickDownColor: token('--down'),
  })
  series.setData(props.bars.map(b => ({
    time: Math.floor(b.ts / 1000), open: b.open, high: b.high, low: b.low, close: b.close,
  })))

  const markers = []
  for (const t of props.trades) {
    if (t.entry_ts) {
      markers.push({
        time: Math.floor(t.entry_ts / 1000),
        position: 'belowBar', color: token('--up'), shape: 'arrowUp',
        text: `BUY ${fmt(t.entry_price)}`,
      })
    }
    if (t.exit_ts) {
      const win = (t.pnl || 0) >= 0
      markers.push({
        time: Math.floor(t.exit_ts / 1000),
        position: 'aboveBar', color: win ? token('--up') : token('--down'), shape: 'square',
        text: `SELL ${fmt(t.exit_price)}`,
      })
    }
  }
  markers.sort((a, b) => a.time - b.time)
  series.setMarkers(markers)
  chart.timeScale().fitContent()

  ro = new ResizeObserver(() => {
    if (el.value && chart) chart.applyOptions({ width: el.value.clientWidth, height: el.value.clientHeight })
  })
  ro.observe(el.value)
}

onMounted(async () => { await nextTick(); build() })
onUnmounted(destroy)
watch(() => [props.bars, props.trades], async () => { await nextTick(); build() }, { deep: true })
</script>
