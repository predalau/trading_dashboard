<template>
  <div class="min-h-screen bg-dark-900">
    <nav class="glass-effect border-b border-dark-700">
      <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <div class="flex items-center gap-2">
          <div class="text-2xl font-bold bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent">
            📈 Trading Dashboard
          </div>
        </div>
        <div class="flex gap-4">
          <router-link to="/" class="hover:text-blue-400 transition">Home</router-link>
          <router-link to="/dashboard" class="hover:text-blue-400 transition">Dashboard</router-link>
          <router-link to="/trades" class="hover:text-blue-400 transition">Trades</router-link>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-8">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
/* Navigation animations */
a {
  position: relative;
  text-decoration: none;
}

a::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 2px;
  bottom: -4px;
  left: 0;
  background: linear-gradient(to right, #3b82f6, #06b6d4);
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.3s ease;
}

a:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}
</style>
