<template>
  <div class="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900">
    <!-- Viking header decoration -->
    <div class="h-1 bg-gradient-to-r from-purple-600 via-purple-500 to-purple-600"></div>

    <nav class="glass-effect border-b border-purple-700">
      <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <div class="flex items-center gap-3">
          <span class="text-3xl">⚔️</span>
          <div>
            <div class="text-2xl font-bold bg-gradient-to-r from-purple-400 via-purple-300 to-violet-400 bg-clip-text text-transparent">
              InvesThor
            </div>
            <div class="text-xs text-purple-400 font-semibold tracking-widest">WARRIOR OF MARKETS</div>
          </div>
          <span class="text-3xl ml-2">🛡️</span>
        </div>
        <div class="flex gap-6">
          <router-link to="/" class="nav-link">Home</router-link>
          <router-link to="/dashboard" class="nav-link">Dashboard</router-link>
          <router-link to="/trades" class="nav-link">Raids</router-link>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-8">
      <router-view />
    </main>

    <!-- Viking footer decoration -->
    <div class="mt-12 border-t border-purple-700 pt-8 pb-4 text-center">
      <p class="text-purple-400 text-sm">Valhalla awaits the bold traders ⚡</p>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
/* Viking navigation animations */
.nav-link {
  position: relative;
  text-decoration: none;
  color: #c4b5fd;
  font-weight: 500;
  transition: color 0.3s ease;
}

.nav-link:hover {
  color: #a78bfa;
}

.nav-link::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 2px;
  bottom: -4px;
  left: 0;
  background: linear-gradient(to right, #7c3aed, #a78bfa, #7c3aed);
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.3s ease;
}

.nav-link:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}
</style>
