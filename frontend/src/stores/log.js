import { defineStore } from 'pinia'
import { ref } from 'vue'

const MAX_ENTRIES = 200

/**
 * App-wide event log shown in the sys.log panel.
 * Levels: OK, FILL, SET, WARN, ERR
 */
export const useLogStore = defineStore('log', () => {
  const entries = ref([])
  let nextId = 0

  const push = (level, msg) => {
    const time = new Date().toTimeString().slice(0, 8)
    entries.value.push({ id: nextId++, time, level, msg })
    if (entries.value.length > MAX_ENTRIES) {
      entries.value.splice(0, entries.value.length - MAX_ENTRIES)
    }
  }

  return { entries, push }
})

/**
 * Log from outside components (services, API client).
 * Ignored if Pinia is not installed yet.
 */
export const sysLog = (level, msg) => {
  try {
    useLogStore().push(level, msg)
  } catch {
    // Pinia not active yet
  }
}
