<template>
  <section class="term-panel" :class="tone === 'surface' ? 'bg-term-surface' : 'bg-term-panel'">
    <header v-if="title" class="term-panel-header">
      <span class="text-muted">
        <span aria-hidden="true">╔═[ </span><h2 class="term-panel-title">{{ title }}</h2><span aria-hidden="true"> ]</span>
      </span>
      <div v-if="$slots.meta" class="term-panel-meta">
        <slot name="meta" />
      </div>
    </header>
    <div :class="flush ? '' : 'p-3.5'">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  tone: { type: String, default: 'panel' },
  flush: { type: Boolean, default: false },
})
</script>

<style scoped>
.term-panel {
  border: 1px solid var(--line);
  min-width: 0;
}

.term-panel-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 20px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--line);
}

.term-panel-title {
  display: inline;
  font-size: inherit;
  font-weight: 700;
  color: var(--accent);
}

.term-panel-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 20px;
  margin-left: auto;
  color: var(--muted);
}
</style>
