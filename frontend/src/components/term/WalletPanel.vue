<template>
  <TermPanel title="portfolio.sh">
    <template #meta>
      <span v-if="summary">Σ ${{ fmt(summary.grand_total_usd) }}</span>
    </template>

    <div v-if="loading" class="text-muted px-1 py-2">[..] loading<span class="cursor-text" aria-hidden="true"> _</span></div>

    <div v-else-if="summary" class="flex flex-col gap-4">
      <!-- Totals -->
      <div class="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <div class="bg-term-surface border border-term-line p-3">
          <div class="text-muted text-[11px] uppercase tracking-[0.12em]">paper equity</div>
          <div class="mt-1 text-lg font-bold">${{ fmt(summary.paper.equity) }}</div>
          <div class="text-muted text-xs">cash ${{ fmt(summary.paper.cash) }}</div>
        </div>
        <div class="bg-term-surface border border-term-line p-3">
          <div class="text-muted text-[11px] uppercase tracking-[0.12em]">wallets</div>
          <div class="mt-1 text-lg font-bold">${{ fmt(summary.wallets_total_usd) }}</div>
          <div class="text-muted text-xs">{{ summary.wallets.length }} tracked</div>
        </div>
        <div class="bg-term-surface border border-term-line p-3">
          <div class="text-muted text-[11px] uppercase tracking-[0.12em]">grand total</div>
          <div class="mt-1 text-lg font-bold text-accent">${{ fmt(summary.grand_total_usd) }}</div>
        </div>
      </div>

      <!-- Wallet list -->
      <div v-for="w in summary.wallets" :key="w.id" class="border border-term-line p-3">
        <div class="flex items-center justify-between gap-2">
          <div class="min-w-0">
            <span class="text-accent">{{ w.label || 'wallet' }}</span>
            <span class="text-muted text-xs ml-2">{{ short(w.address) }}</span>
          </div>
          <div class="flex items-center gap-3 shrink-0">
            <span class="font-bold">${{ fmt(w.value_usd) }}</span>
            <button @click="removeWallet(w.id)" class="t-btn-danger" aria-label="remove wallet">rm</button>
          </div>
        </div>
        <div v-if="w.error" class="text-down text-xs mt-1">fetch failed (rpc / price unavailable)</div>
        <div v-else class="text-muted text-xs mt-1">
          {{ (w.sol || 0).toFixed(3) }} SOL @ ${{ fmt(w.sol_price_usd) }}
          <span v-if="w.tokens && w.tokens.length"> · {{ w.tokens.length }} priced tokens</span>
        </div>
        <table v-if="w.tokens && w.tokens.length" class="t-table mt-2">
          <tbody>
            <tr v-for="t in w.tokens.slice(0, 6)" :key="t.mint">
              <td>{{ short(t.mint) }}</td>
              <td class="text-right">{{ Number(t.amount).toLocaleString() }}</td>
              <td class="text-right">${{ fmt(t.value_usd) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Add wallet -->
      <form @submit.prevent="addWallet" class="flex flex-wrap items-center gap-2">
        <input v-model="form.address" placeholder="Solana address" class="t-input flex-1 min-w-[240px]" />
        <input v-model="form.label" placeholder="label (optional)" class="t-input w-40" />
        <button type="submit" class="t-btn" :disabled="adding">{{ adding ? '...' : '+ track' }}</button>
      </form>
      <div v-if="error" class="text-down text-xs">{{ error }}</div>
    </div>
  </TermPanel>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TermPanel from './TermPanel.vue'

const loading = ref(true)
const adding = ref(false)
const summary = ref(null)
const error = ref('')
const form = ref({ address: '', label: '' })

const fmt = (n) =>
  n == null ? '0.00' : Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const short = (a) => (a ? a.slice(0, 4) + '…' + a.slice(-4) : '')

const fetchSummary = async () => {
  loading.value = true
  try {
    const r = await fetch('/trading/api/v1/portfolio/summary')
    if (r.ok) summary.value = await r.json()
  } catch (e) {
    console.error('portfolio summary failed:', e)
  } finally {
    loading.value = false
  }
}

const addWallet = async () => {
  error.value = ''
  if (!form.value.address) return
  adding.value = true
  try {
    const r = await fetch('/trading/api/v1/wallets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ address: form.value.address.trim(), label: form.value.label || null }),
    })
    if (!r.ok) {
      const d = await r.json().catch(() => ({}))
      throw new Error(d.detail || `HTTP ${r.status}`)
    }
    form.value = { address: '', label: '' }
    await fetchSummary()
  } catch (e) {
    error.value = e.message
  } finally {
    adding.value = false
  }
}

const removeWallet = async (id) => {
  try {
    await fetch(`/trading/api/v1/wallets/${id}`, { method: 'DELETE' })
    await fetchSummary()
  } catch (e) {
    console.error('remove wallet failed:', e)
  }
}

onMounted(fetchSummary)
</script>
