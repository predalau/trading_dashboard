<template>
  <div class="min-h-screen flex flex-col bg-term-bg text-term-text pb-20 md:pb-0">
    <TermHeader />

    <TermNav :items="navItems" />

    <main class="w-full max-w-[1440px] mx-auto px-4 md:px-7 py-6 flex-1">
      <router-view />
    </main>

    <StatusBar :items="navItems" />

    <!-- Mobile bottom tab bar -->
    <nav class="mobile-tab-bar" aria-label="Main">
      <router-link
        v-for="(item, i) in navItems"
        :key="item.to"
        :to="item.to"
        class="mobile-tab"
        :class="{ 'mobile-tab-active': isActive(item.to) }"
        :aria-current="isActive(item.to) ? 'page' : undefined"
      >{{ i }} {{ item.label }}</router-link>
    </nav>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { ref, provide } from 'vue'
import TermHeader from './components/term/TermHeader.vue'
import TermNav from './components/term/TermNav.vue'
import StatusBar from './components/term/StatusBar.vue'

const route = useRoute()

const isRealTrading = ref(false)
provide('isRealTrading', isRealTrading)

const navItems = [
  { to: '/', label: 'home' },
  { to: '/dashboard', label: 'dashboard' },
  { to: '/trades', label: 'trades' },
  { to: '/profile', label: 'profile' },
]

const isActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
.mobile-tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  padding-bottom: env(safe-area-inset-bottom, 0);
  background: var(--surface);
  border-top: 1px solid var(--line);
}

@media (min-width: 768px) {
  .mobile-tab-bar {
    display: none;
  }
}

.mobile-tab {
  flex: 1;
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--muted);
  text-decoration: none;
}

.mobile-tab-active {
  background: var(--accent);
  color: var(--on-accent);
  font-weight: 700;
}
</style>
