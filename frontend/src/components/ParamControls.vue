<template>
  <div class="flex flex-col gap-2">
    <div v-for="p in spec" :key="p.name" class="flex items-center gap-3">
      <span class="text-xs w-24 shrink-0">{{ p.label || p.name }}</span>

      <button
        v-if="p.type === 'bool'"
        type="button"
        class="t-btn px-4 py-1.5"
        :class="params[p.name] ? '' : 't-btn-ghost'"
        @click="params[p.name] = !params[p.name]"
      >{{ params[p.name] ? 'on' : 'off' }}</button>

      <select v-else-if="p.type === 'choice'" v-model="params[p.name]" class="t-input">
        <option v-for="c in (p.choices || [])" :key="c" :value="c">{{ c }}</option>
      </select>

      <template v-else-if="p.type === 'int' || p.type === 'float'">
        <input
          type="number"
          :min="p.min" :max="p.max" :step="p.step || 1"
          v-model.number="params[p.name]"
          class="t-input text-center shrink-0 px-1"
          style="width: 3.5rem; flex: none"
        />
        <input
          type="range"
          :min="p.min" :max="p.max" :step="p.step || 1"
          v-model.number="params[p.name]"
          class="param-slider flex-1 min-w-0"
        />
      </template>

      <input v-else v-model="params[p.name]" class="t-input flex-1" />
    </div>
  </div>
</template>

<script setup>
// `params` is a reactive object owned by the parent; we mutate its keys in place.
defineProps({
  spec: { type: Array, default: () => [] },
  params: { type: Object, default: () => ({}) },
})
</script>

<style scoped>
.param-slider {
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  border-radius: 4px;
  background: var(--line, #30363d);
  cursor: pointer;
  outline: none;
}
.param-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent, #4fd6ff);
  border: 2px solid var(--surface, #0a0f15);
  cursor: grab;
}
.param-slider::-webkit-slider-thumb:active { cursor: grabbing; }
.param-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent, #4fd6ff);
  border: 2px solid var(--surface, #0a0f15);
  cursor: grab;
}
.param-slider::-moz-range-track {
  height: 8px;
  border-radius: 4px;
  background: var(--line, #30363d);
}
</style>
