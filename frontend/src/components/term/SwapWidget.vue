<template>
  <TermPanel title="swap.sh (solana · jupiter)">
    <template #meta>
      <span v-if="pubkey" class="text-accent">{{ short(pubkey) }}</span>
      <span v-else class="text-muted">not connected</span>
    </template>

    <div class="flex flex-col gap-3">
      <div v-if="!pubkey">
        <button @click="connect" class="t-btn" :disabled="busy">connect Phantom</button>
        <span class="text-muted text-xs ml-3">real swaps — you sign in Phantom; the backend never holds your keys.</span>
      </div>

      <template v-else>
        <div class="flex flex-wrap items-end gap-3">
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">from</span>
            <select v-model="fromMint" class="t-input">
              <option v-for="t in tokens" :key="t.mint" :value="t.mint">{{ t.sym }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">amount</span>
            <input v-model.number="amount" type="number" min="0" step="any" class="t-input w-36" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">to</span>
            <select v-model="toMint" class="t-input">
              <option v-for="t in tokens" :key="t.mint" :value="t.mint">{{ t.sym }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-muted text-xs">slippage bps</span>
            <input v-model.number="slippageBps" type="number" min="1" max="500" class="t-input w-24" />
          </label>
          <button @click="getQuote" class="t-btn" :disabled="busy || !amount">quote</button>
        </div>

        <div v-if="quote" class="text-muted text-xs">
          out ≈ <span class="text-term-text">{{ outUi }} {{ sym(toMint) }}</span> ·
          price impact {{ quote.price_impact_pct }}%
        </div>

        <button v-if="quote" @click="doSwap" class="t-btn-danger justify-start" :disabled="busy">
          {{ busy ? '… signing / broadcasting' : `sign & swap ${amount} ${sym(fromMint)} → ${sym(toMint)} (REAL)` }}
        </button>
      </template>

      <div v-if="msg" class="text-xs break-all" :class="msgErr ? 'text-down' : 'text-up'">
        {{ msg }}
        <a v-if="explorer" :href="explorer" target="_blank" rel="noopener" class="underline ml-1">view on solscan</a>
      </div>
    </div>
  </TermPanel>
</template>

<script setup>
import { ref, computed } from 'vue'
import TermPanel from './TermPanel.vue'
import { connectWallet, signUnsignedTxB64 } from '../../services/phantom'

const tokens = [
  { sym: 'SOL', mint: 'So11111111111111111111111111111111111111112', dec: 9 },
  { sym: 'USDC', mint: 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', dec: 6 },
  { sym: 'USDT', mint: 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB', dec: 6 },
  { sym: 'JUP', mint: 'JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN', dec: 6 },
  { sym: 'BONK', mint: 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263', dec: 5 },
]

const pubkey = ref('')
const fromMint = ref(tokens[0].mint)
const toMint = ref(tokens[1].mint)
const amount = ref(0.01)
const slippageBps = ref(50)
const quote = ref(null)
const busy = ref(false)
const msg = ref('')
const msgErr = ref(false)
const explorer = ref('')

const token = (mint) => tokens.find((t) => t.mint === mint)
const sym = (mint) => token(mint)?.sym || '?'
const short = (a) => (a ? a.slice(0, 4) + '…' + a.slice(-4) : '')
const outUi = computed(() => {
  if (!quote.value) return ''
  return (Number(quote.value.out_amount) / 10 ** token(toMint.value).dec).toFixed(6)
})

const setMsg = (text, err = false) => { msg.value = text; msgErr.value = err }

const connect = async () => {
  busy.value = true; setMsg('')
  try {
    pubkey.value = await connectWallet()
    setMsg('connected: ' + pubkey.value)
  } catch (e) { setMsg(e.message, true) } finally { busy.value = false }
}

const baseAmount = () => Math.round(amount.value * 10 ** token(fromMint.value).dec)

const getQuote = async () => {
  busy.value = true; setMsg(''); quote.value = null; explorer.value = ''
  try {
    if (fromMint.value === toMint.value) throw new Error('from and to must differ')
    const r = await fetch('/trading/api/v1/solana/quote', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_mint: fromMint.value, output_mint: toMint.value, amount: baseAmount(), slippage_bps: slippageBps.value }),
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`)
    quote.value = d
  } catch (e) { setMsg(e.message, true) } finally { busy.value = false }
}

const doSwap = async () => {
  busy.value = true; setMsg(''); explorer.value = ''
  try {
    // 1) prepare unsigned tx
    const prep = await fetch('/trading/api/v1/solana/swap/prepare', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input_mint: fromMint.value, output_mint: toMint.value, amount: baseAmount(), slippage_bps: slippageBps.value, user_pubkey: pubkey.value }),
    })
    const prepBody = await prep.json()
    if (!prep.ok) throw new Error(prepBody.detail || `prepare HTTP ${prep.status}`)

    // 2) sign in Phantom (no broadcast)
    const signedB64 = await signUnsignedTxB64(prepBody.swap_transaction)

    // 3) backend broadcasts + records the order
    const sub = await fetch('/trading/api/v1/solana/swap/submit', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ signed_transaction: signedB64, input_mint: fromMint.value, output_mint: toMint.value, in_amount: amount.value, user_pubkey: pubkey.value }),
    })
    const subBody = await sub.json()
    if (!sub.ok) throw new Error(subBody.detail || `submit HTTP ${sub.status}`)
    explorer.value = subBody.explorer
    setMsg(`swap ${subBody.status} · sig ${short(subBody.signature)}`, false)
    quote.value = null
  } catch (e) { setMsg(e.message, true) } finally { busy.value = false }
}
</script>
