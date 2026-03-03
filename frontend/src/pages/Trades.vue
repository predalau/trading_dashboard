<template>
  <div class="space-y-8 animate-fade-in">
    <section class="space-y-4">
      <h1 class="text-4xl font-bold text-purple-400">🛡️ The Raid Hall</h1>
      <p class="text-purple-400">Prepare your raids and study your glorious victories and honorable defeats</p>
    </section>

    <!-- New Trade Form -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="chart-container border-purple-700">
        <h2 class="text-xl font-semibold mb-4 text-purple-400">⚔️ Plan Your Raid</h2>
        <form @submit.prevent="submitTrade" class="space-y-4">
          <div>
            <label class="block text-sm text-dark-400 mb-2">Symbol</label>
            <select v-model="form.symbol" class="w-full">
              <option value="">Select Symbol</option>
              <option value="BTCUSDT">BTC/USDT</option>
              <option value="ETHUSDT">ETH/USDT</option>
              <option value="BNBUSDT">BNB/USDT</option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <button
              type="button"
              @click="form.tradeType = 'BUY'"
              class="py-2 rounded-lg font-medium transition"
              :class="form.tradeType === 'BUY' ? 'bg-green-600 text-white' : 'bg-dark-700 text-dark-400'"
            >
              Buy
            </button>
            <button
              type="button"
              @click="form.tradeType = 'SELL'"
              class="py-2 rounded-lg font-medium transition"
              :class="form.tradeType === 'SELL' ? 'bg-red-600 text-white' : 'bg-dark-700 text-dark-400'"
            >
              Sell
            </button>
          </div>

          <div>
            <label class="block text-sm text-dark-400 mb-2">Entry Price</label>
            <input v-model.number="form.entryPrice" type="number" placeholder="0.00" step="0.01" class="w-full" />
          </div>

          <div>
            <label class="block text-sm text-dark-400 mb-2">Quantity</label>
            <input v-model.number="form.quantity" type="number" placeholder="0.0" step="0.1" class="w-full" />
          </div>

          <div>
            <label class="block text-sm text-dark-400 mb-2">Notes (Optional)</label>
            <textarea v-model="form.notes" placeholder="Add notes..." rows="3" class="w-full"></textarea>
          </div>

          <button type="submit" class="btn btn-primary w-full bg-purple-700 hover:bg-purple-600">
            ⚔️ Launch Raid
          </button>
        </form>
      </div>

      <div class="lg:col-span-2">
        <div class="chart-container border-purple-700">
          <h2 class="text-xl font-semibold mb-4 text-purple-400">👑 Active Conquests</h2>
          <div class="space-y-3">
            <div
              v-for="trade in openTrades"
              :key="trade.id"
              class="border border-dark-700 rounded-lg p-4 hover:bg-dark-800 transition"
            >
              <div class="flex justify-between items-start mb-2">
                <div>
                  <div class="font-semibold">{{ trade.symbol }}</div>
                  <div class="text-sm text-dark-400">{{ trade.tradeType }}</div>
                </div>
                <button
                  @click="selectTradeForClose(trade)"
                  class="btn btn-secondary text-sm"
                >
                  Close
                </button>
              </div>
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div class="text-dark-400">Entry Price</div>
                  <div class="font-semibold">${{ trade.entryPrice }}</div>
                </div>
                <div>
                  <div class="text-dark-400">Quantity</div>
                  <div class="font-semibold">{{ trade.quantity }}</div>
                </div>
              </div>
            </div>

            <div v-if="openTrades.length === 0" class="text-center py-8 text-dark-400">
              No open positions. Create a new trade to get started.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Close Trade Modal -->
    <div v-if="tradeToClose" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div class="chart-container max-w-md w-full mx-4 border-purple-700">
        <h3 class="text-xl font-semibold mb-4 text-purple-400">⚡ End Your Raid</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-dark-400 mb-2">Exit Price</label>
            <input v-model.number="closeForm.exitPrice" type="number" placeholder="0.00" step="0.01" class="w-full" />
          </div>
          <div>
            <label class="block text-sm text-dark-400 mb-2">Notes</label>
            <textarea v-model="closeForm.notes" placeholder="Add notes..." rows="2" class="w-full"></textarea>
          </div>
          <div class="flex gap-3">
            <button @click="closeTrade" class="btn btn-primary flex-1">Close Trade</button>
            <button @click="tradeToClose = null" class="btn btn-secondary flex-1">Cancel</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Closed Trades History -->
    <div class="chart-container border-purple-700">
      <h2 class="text-xl font-semibold mb-4 text-purple-400">📜 Chronicles of Battle</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="border-b border-dark-700">
            <tr>
              <th class="text-left py-2 text-dark-400">Symbol</th>
              <th class="text-left py-2 text-dark-400">Type</th>
              <th class="text-left py-2 text-dark-400">Entry</th>
              <th class="text-left py-2 text-dark-400">Exit</th>
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
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const form = ref({
  symbol: '',
  tradeType: 'BUY',
  entryPrice: null,
  quantity: null,
  notes: ''
})

const closeForm = ref({
  exitPrice: null,
  notes: ''
})

const tradeToClose = ref(null)
const openTrades = ref([])

const submitTrade = () => {
  if (!form.value.symbol || !form.value.entryPrice || !form.value.quantity) {
    alert('Please fill in all required fields')
    return
  }

  openTrades.value.push({
    id: Date.now(),
    ...form.value
  })

  form.value = {
    symbol: '',
    tradeType: 'BUY',
    entryPrice: null,
    quantity: null,
    notes: ''
  }
}

const selectTradeForClose = (trade) => {
  tradeToClose.value = trade
  closeForm.value = {
    exitPrice: null,
    notes: ''
  }
}

const closeTrade = () => {
  if (!closeForm.value.exitPrice) {
    alert('Please enter exit price')
    return
  }

  // Here you would send the close request to the API
  console.log('Closing trade:', tradeToClose.value, closeForm.value)

  openTrades.value = openTrades.value.filter(t => t.id !== tradeToClose.value.id)
  tradeToClose.value = null
}
</script>
