<template>
  <nav class="term-nav" aria-label="Main">
    <router-link
      v-for="(item, i) in items"
      :key="item.to"
      :to="item.to"
      class="term-tab"
      :class="{ 'term-tab-active': isActive(item.to) }"
      :aria-current="isActive(item.to) ? 'page' : undefined"
    >[{{ i }}] {{ item.label }}{{ isActive(item.to) ? '*' : '' }}</router-link>
    <TickerStrip class="ml-auto px-4 py-2.5" />
  </nav>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TickerStrip from './TickerStrip.vue'

const props = defineProps({
  items: { type: Array, required: true },
})

const route = useRoute()
const router = useRouter()

const isActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

// Number keys switch tabs, like tmux windows
const onKey = (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return
  const tag = e.target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.target.isContentEditable) return
  const item = props.items[Number(e.key)]
  if (item && /^[0-9]$/.test(e.key)) router.push(item.to)
}

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.term-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.term-tab {
  padding: 10px 16px;
  color: var(--muted);
  text-decoration: none;
}

.term-tab:hover {
  color: var(--text);
}

.term-tab-active,
.term-tab-active:hover {
  background: var(--accent);
  color: var(--on-accent);
  font-weight: 700;
}
</style>
