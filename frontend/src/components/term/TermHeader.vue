<template>
  <header class="term-header" :class="{ 'term-header-real': isRealTrading }">
    <router-link to="/" class="no-underline">
      <AsciiLogo class="hidden md:block" />
      <span class="md:hidden font-extrabold text-accent text-base">investhor:~$</span>
    </router-link>

    <div class="prompt hidden sm:block">
      <span>root@investhor</span><span class="text-accent">:</span><span>~{{ path }}</span><span class="text-accent"># </span>
      <span class="text-term-text">{{ command }}</span><span class="cursor" aria-hidden="true"></span>
    </div>

    <div class="flex items-center gap-2 ml-auto" role="group" aria-label="Trading mode">
      <button
        type="button"
        :class="!isRealTrading ? 't-btn' : 't-btn-ghost'"
        :aria-pressed="!isRealTrading"
        @click="setReal(false)"
      >PAPER</button>
      <button
        type="button"
        :class="isRealTrading ? 't-btn-real' : 't-btn-ghost'"
        :aria-pressed="isRealTrading"
        @click="setReal(true)"
      >REAL</button>
    </div>
  </header>
</template>

<script setup>
import { computed, inject } from 'vue'
import { useRoute } from 'vue-router'
import AsciiLogo from './AsciiLogo.vue'

const route = useRoute()
const isRealTrading = inject('isRealTrading')

const COMMANDS = {
  Home: 'cat motd',
  Dashboard: 'watch --live market',
  Trades: 'ls -la trades/',
  Profile: 'whoami',
}

const path = computed(() => (route.path === '/' ? '' : route.path))
const command = computed(() => COMMANDS[route.name] || '')

const setReal = (value) => { isRealTrading.value = value }
</script>

<style scoped>
.term-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 28px;
  padding: 16px 28px;
  border-top: 2px solid transparent;
  border-bottom: 1px solid var(--line);
}

.term-header-real {
  border-top-color: var(--down);
}

.prompt {
  color: var(--muted);
}

.t-btn-real {
  @apply inline-flex items-center justify-center px-3.5 py-2.5 font-extrabold cursor-pointer;
  background: var(--down);
  color: var(--on-accent);
  border: 1px solid var(--down);
}

@media (max-width: 767px) {
  .term-header {
    padding: 12px 16px;
  }
}
</style>
