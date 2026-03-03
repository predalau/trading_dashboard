<template>
  <div class="space-y-8 animate-fade-in">
    <section class="space-y-4 text-center py-8">
      <h1 class="text-5xl font-bold bg-gradient-to-r from-purple-400 via-purple-300 to-violet-400 bg-clip-text text-transparent">
        ⚔️ InvesThor ⚡
      </h1>
      <p class="text-purple-400 text-lg font-semibold">Conquer the Markets with Warrior Strategy</p>
      <p class="text-dark-300 text-sm">A Viking's Guide to Paper Trading and Market Dominance</p>
    </section>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="card border-purple-700 hover:border-purple-600">
        <div class="text-sm text-purple-400 mb-2 font-semibold">⚔️ PREPARE FOR BATTLE</div>
        <h3 class="text-xl font-semibold mb-4 text-purple-400">Forge Your Account</h3>
        <p class="text-dark-300 mb-4">Arm yourself with a paper trading account and virtual wealth to conquer the markets</p>
        <router-link to="/dashboard" class="text-purple-400 hover:text-purple-300 font-semibold">Begin Your Saga →</router-link>
      </div>

      <div class="card border-purple-700 hover:border-purple-600">
        <div class="text-sm text-purple-400 mb-2 font-semibold">🛡️ RAID THE MARKETS</div>
        <h3 class="text-xl font-semibold mb-4 text-purple-400">Paper Trading</h3>
        <p class="text-dark-300 mb-4">Execute bold trades in glorious battle with real-time market data and zero risk</p>
        <router-link to="/trades" class="text-purple-400 hover:text-purple-300 font-semibold">Join the Raid →</router-link>
      </div>

      <div class="card border-purple-700 hover:border-purple-600">
        <div class="text-sm text-purple-400 mb-2 font-semibold">⚡ DIVINE POWER</div>
        <h3 class="text-xl font-semibold mb-4 text-purple-400">API Sorcery</h3>
        <p class="text-dark-300 mb-4">Unleash algorithmic magic with our REST API and automate your trading conquests</p>
        <a href="/api/v1" class="text-purple-400 hover:text-purple-300 font-semibold">Harness the Power →</a>
      </div>
    </div>

    <section class="space-y-4 mt-12">
      <h2 class="text-2xl font-bold text-purple-400">⚔️ Allies & Trading Grounds</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="card text-center border-purple-700">
          <div class="text-4xl mb-2">📊</div>
          <div class="font-semibold text-purple-400">Binance</div>
          <div class="text-sm text-purple-400 font-semibold">The Great Exchange</div>
        </div>
        <div class="card text-center border-purple-700">
          <div class="text-4xl mb-2">⛓️</div>
          <div class="font-semibold text-purple-400">Solana</div>
          <div class="text-sm text-purple-400 font-semibold">Coming in Future Quests</div>
        </div>
        <div class="card text-center opacity-50 border-purple-700">
          <div class="text-4xl mb-2">🚀</div>
          <div class="font-semibold text-purple-400">More Allies</div>
          <div class="text-sm text-purple-400 font-semibold">Awaiting Discovery</div>
        </div>
        <div class="card text-center opacity-50 border-purple-700">
          <div class="text-4xl mb-2">🔗</div>
          <div class="font-semibold text-purple-400">Integrations</div>
          <div class="text-sm text-purple-400 font-semibold">Under Construction</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
</script>
