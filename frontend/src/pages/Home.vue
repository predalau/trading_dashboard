<template>
  <div class="space-y-8 animate-fade-in">
    <section class="space-y-4">
      <h1 class="text-4xl font-bold">Welcome to Trading Dashboard</h1>
      <p class="text-dark-300">Your comprehensive platform for paper trading and market analysis</p>
    </section>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="card">
        <div class="text-sm text-dark-400 mb-2">Getting Started</div>
        <h3 class="text-xl font-semibold mb-4">Create Account</h3>
        <p class="text-dark-300 mb-4">Set up your paper trading account and start trading with virtual funds</p>
        <router-link to="/dashboard" class="text-blue-400 hover:text-blue-300">Get Started →</router-link>
      </div>

      <div class="card">
        <div class="text-sm text-dark-400 mb-2">Features</div>
        <h3 class="text-xl font-semibold mb-4">Paper Trading</h3>
        <p class="text-dark-300 mb-4">Execute trades in a risk-free environment with real-time market data</p>
        <router-link to="/trades" class="text-blue-400 hover:text-blue-300">View Trades →</router-link>
      </div>

      <div class="card">
        <div class="text-sm text-dark-400 mb-2">API</div>
        <h3 class="text-xl font-semibold mb-4">Programmatic Trading</h3>
        <p class="text-dark-300 mb-4">Integrate with our REST API for algorithmic trading strategies</p>
        <a href="/api/v1" class="text-blue-400 hover:text-blue-300">API Docs →</a>
      </div>
    </div>

    <section class="space-y-4 mt-12">
      <h2 class="text-2xl font-bold">Supported Exchanges</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="card text-center">
          <div class="text-2xl mb-2">📊</div>
          <div class="font-semibold">Binance</div>
          <div class="text-sm text-dark-400">Spot Trading</div>
        </div>
        <div class="card text-center">
          <div class="text-2xl mb-2">⛓️</div>
          <div class="font-semibold">Solana</div>
          <div class="text-sm text-dark-400">Coming Soon</div>
        </div>
        <div class="card text-center opacity-50">
          <div class="text-2xl mb-2">🚀</div>
          <div class="font-semibold">More</div>
          <div class="text-sm text-dark-400">Coming Soon</div>
        </div>
        <div class="card text-center opacity-50">
          <div class="text-2xl mb-2">🔗</div>
          <div class="font-semibold">APIs</div>
          <div class="text-sm text-dark-400">Coming Soon</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
</script>
