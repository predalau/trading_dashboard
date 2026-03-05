<template>
  <div class="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900 pb-20 md:pb-0">
    <nav class="header-bar">
      <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <div class="logo-text text-2xl font-bold">
          InvesThor
        </div>
        <!-- Trading mode toggle -->
        <button class="mode-toggle" @click="toggleTradingMode">
          <span class="mode-toggle-label" :class="{ 'mode-toggle-active': !isRealTrading }">Paper</span>
          <span class="mode-toggle-label" :class="{ 'mode-toggle-active': isRealTrading }">Real</span>
          <span class="mode-toggle-slider" :class="{ 'mode-toggle-slider-real': isRealTrading }"></span>
        </button>

        <!-- Desktop nav: icon pills -->
        <div class="hidden md:flex gap-2">
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="nav-pill"
            :class="{ 'nav-pill-active': isActive(item.to) }"
          >
            <span class="text-base">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </router-link>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-8">
      <router-view />
    </main>

    <!-- Viking footer decoration -->
    <div class="mt-12 border-t border-secondary-800 pt-8 pb-4 text-center hidden md:block">
      <p class="text-dark-500 text-sm">InvesThor</p>
    </div>

    <!-- Mobile bottom tab bar -->
    <nav class="mobile-tab-bar">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="mobile-tab"
        :class="{ 'mobile-tab-active': isActive(item.to) }"
      >
        <div class="mobile-tab-indicator" v-if="isActive(item.to)"></div>
        <span class="text-xl">{{ item.icon }}</span>
        <span class="text-[10px] mt-0.5">{{ item.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { ref, provide } from 'vue'

const route = useRoute()

const isRealTrading = ref(false)
const toggleTradingMode = () => { isRealTrading.value = !isRealTrading.value }
provide('isRealTrading', isRealTrading)

const navItems = [
  { to: '/', icon: '🏠', label: 'Home' },
  { to: '/dashboard', icon: '📊', label: 'Dashboard' },
  { to: '/trades', icon: '⚔️', label: 'Raids' },
  { to: '/profile', icon: '👤', label: 'Profile' },
]

const isActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
/* Header bar */
.header-bar {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.7), rgba(30, 41, 59, 0.5));
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

/* Logo with text shadow glow */
.logo-text {
  background: linear-gradient(to right, #c4b5fd, #facc15, #c4b5fd);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 8px rgba(139, 92, 246, 0.6)) drop-shadow(0 0 20px rgba(139, 92, 246, 0.3)) drop-shadow(0 0 30px rgba(234, 179, 8, 0.15));
}

/* Trading mode toggle */
.mode-toggle {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0;
  padding: 2px;
  border-radius: 9999px;
  background: rgba(30, 30, 50, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.2);
  cursor: pointer;
  overflow: hidden;
}

.mode-toggle-label {
  position: relative;
  z-index: 1;
  padding: 5px 14px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #71717a;
  transition: color 0.25s ease;
  user-select: none;
}

.mode-toggle-active {
  color: #fff;
}

.mode-toggle-slider {
  position: absolute;
  top: 2px;
  left: 2px;
  width: calc(50% - 2px);
  height: calc(100% - 4px);
  border-radius: 9999px;
  background: rgba(139, 92, 246, 0.4);
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.3);
  transition: all 0.25s ease;
}

.mode-toggle-slider-real {
  left: calc(50%);
  background: rgba(234, 179, 8, 0.5);
  box-shadow: 0 0 8px rgba(234, 179, 8, 0.3);
}

/* Desktop: Icon pills with active glow */
.nav-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #a1a1aa;
  background: transparent;
  border: 1px solid transparent;
  transition: all 0.25s ease;
  text-decoration: none;
}

.nav-pill:hover {
  color: #c4b5fd;
  background: rgba(139, 92, 246, 0.08);
  border-color: rgba(139, 92, 246, 0.2);
}

.nav-pill-active {
  color: #e9d5ff !important;
  background: rgba(139, 92, 246, 0.15) !important;
  border-color: rgba(139, 92, 246, 0.35) !important;
  box-shadow: 0 0 12px rgba(139, 92, 246, 0.25), 0 0 4px rgba(139, 92, 246, 0.15), 0 0 16px rgba(234, 179, 8, 0.08);
}

/* Mobile: Fixed bottom tab bar */
.mobile-tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 6px 0 env(safe-area-inset-bottom, 8px);
  background: rgba(15, 10, 25, 0.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid rgba(139, 92, 246, 0.25);
}

@media (min-width: 768px) {
  .mobile-tab-bar {
    display: none;
  }
}

.mobile-tab {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 6px 0 4px;
  color: #71717a;
  text-decoration: none;
  transition: color 0.2s ease;
}

.mobile-tab-active {
  color: #c4b5fd !important;
}

.mobile-tab-indicator {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 2px;
  border-radius: 0 0 2px 2px;
  background: linear-gradient(to right, #7c3aed, #eab308);
  box-shadow: 0 2px 8px rgba(234, 179, 8, 0.3);
}
</style>
