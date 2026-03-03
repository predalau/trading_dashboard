<template>
  <div class="space-y-8 animate-fade-in">
    <section class="space-y-4">
      <h1 class="text-4xl font-bold">Dashboard</h1>
      <p class="text-dark-300">Monitor your portfolio and trading activity</p>
    </section>

    <!-- Portfolio Overview -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="card">
        <div class="text-sm text-dark-400 mb-2">Account Balance</div>
        <div class="text-3xl font-bold text-blue-400">$50,000</div>
        <div class="text-sm text-dark-500 mt-2">Starting Balance</div>
      </div>

      <div class="card">
        <div class="text-sm text-dark-400 mb-2">Portfolio Value</div>
        <div class="text-3xl font-bold text-green-400">$52,500</div>
        <div class="text-sm text-positive mt-2">+5% from start</div>
      </div>

      <div class="card">
        <div class="text-sm text-dark-400 mb-2">Open Positions</div>
        <div class="text-3xl font-bold">3</div>
        <div class="text-sm text-dark-500 mt-2">Active trades</div>
      </div>

      <div class="card">
        <div class="text-sm text-dark-400 mb-2">Win Rate</div>
        <div class="text-3xl font-bold text-accent-green">65%</div>
        <div class="text-sm text-dark-500 mt-2">13 wins / 7 losses</div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 chart-container">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-semibold">BTC/USDT</h2>
          <div class="flex gap-2">
            <button class="btn btn-secondary text-sm">1H</button>
            <button class="btn btn-secondary text-sm">4H</button>
            <button class="btn btn-primary text-sm">1D</button>
            <button class="btn btn-secondary text-sm">1W</button>
          </div>
        </div>
        <ChartComponent symbol="BTCUSDT" />
      </div>

      <div class="space-y-4">
        <div class="chart-container">
          <h3 class="text-lg font-semibold mb-4">Quick Stats</h3>
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-dark-400">24h High</span>
              <span class="font-semibold">$45,230</span>
            </div>
            <div class="flex justify-between items-center border-t border-dark-700 pt-3">
              <span class="text-dark-400">24h Low</span>
              <span class="font-semibold">$42,100</span>
            </div>
            <div class="flex justify-between items-center border-t border-dark-700 pt-3">
              <span class="text-dark-400">24h Volume</span>
              <span class="font-semibold">$2.5B</span>
            </div>
            <div class="flex justify-between items-center border-t border-dark-700 pt-3">
              <span class="text-dark-400">24h Change</span>
              <span class="font-semibold text-positive">+3.5%</span>
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
import ChartComponent from '../components/ChartComponent.vue'
</script>
