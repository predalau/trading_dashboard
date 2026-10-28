<template>
  <TermPanel title="tail -f sys.log" flush class="flex flex-col">
    <div
      ref="scroller"
      class="sys-log"
      role="log"
      aria-live="polite"
      aria-label="System log"
    >
      <div v-if="log.entries.length === 0" class="text-muted">
        waiting for events<span class="cursor-text" aria-hidden="true"> _</span>
      </div>
      <div v-for="(entry, i) in log.entries" :key="entry.id">
        <span class="text-muted">{{ entry.time }}</span>
        <span :class="levelClass(entry)"> [{{ entry.level }}]</span>
        {{ entry.msg }}<span v-if="i === log.entries.length - 1" class="cursor-text" aria-hidden="true"> _</span>
      </div>
    </div>
  </TermPanel>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useLogStore } from '../../stores/log'
import TermPanel from './TermPanel.vue'

const log = useLogStore()
const scroller = ref(null)

const LEVEL_CLASS = {
  OK: 'text-accent',
  SET: 'text-tp',
  FILL: 'text-up',
  WARN: 'text-down',
  ERR: 'text-down font-bold',
}

const levelClass = (entry) => {
  if (entry.level === 'FILL' && /SHORT|loss/i.test(entry.msg)) return 'text-down'
  return LEVEL_CLASS[entry.level] || 'text-muted'
}

// Keep the newest line in view
watch(() => log.entries.length, async () => {
  await nextTick()
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
})
</script>

<style scoped>
.sys-log {
  height: 220px;
  overflow-y: auto;
  padding: 12px 14px;
  font-size: 12px;
  line-height: 1.6;
}
</style>
