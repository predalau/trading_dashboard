<template>
  <div class="flex flex-col gap-5 max-w-4xl">
    <h1 class="sr-only">InvesThor home</h1>

    <!-- Boot sequence -->
    <TermPanel title="boot.log">
      <div class="flex flex-col gap-1 leading-relaxed">
        <div
          v-for="(line, i) in bootLines"
          :key="line.msg"
          class="boot-line"
          :style="{ animationDelay: i * 120 + 'ms' }"
        >
          <span :class="line.level === 'OK' ? 'text-accent' : 'text-muted'">[{{ line.level }}]</span> {{ line.msg }}
        </div>
      </div>
    </TermPanel>

    <!-- Message of the day -->
    <TermPanel title="cat motd" tone="surface">
      <p class="text-base font-bold">Manage assets and backtest strategies.</p>
      <p class="mt-2 text-muted">Live Binance charts, paper trading with stop loss and take profit, and a full trade history.</p>
    </TermPanel>

    <!-- Commands -->
    <TermPanel title="help">
      <ul class="flex flex-col">
        <li v-for="cmd in commands" :key="cmd.to" class="cmd-row">
          <router-link :to="cmd.to" class="cmd-link">{{ cmd.name }}</router-link>
          <span class="text-muted">{{ cmd.desc }}</span>
        </li>
        <li class="cmd-row">
          <a href="/api/v1" class="cmd-link">./api</a>
          <span class="text-muted">REST API for automated strategies</span>
        </li>
      </ul>
    </TermPanel>

    <!-- Integrations -->
    <TermPanel title="ls integrations/">
      <ul class="flex flex-col gap-1">
        <li v-for="item in integrations" :key="item.name" class="flex gap-4">
          <span class="w-28" :class="item.live ? 'text-term-text' : 'text-muted'">{{ item.name }}</span>
          <span :class="item.live ? 'text-accent' : 'text-muted'">{{ item.status }}</span>
        </li>
      </ul>
    </TermPanel>
  </div>
</template>

<script setup>
import TermPanel from '../components/term/TermPanel.vue'

const bootLines = [
  { level: 'OK', msg: 'loading terminal theme' },
  { level: 'OK', msg: 'mounting paper trading account' },
  { level: 'OK', msg: 'connecting market feed stream.binance.com' },
  { level: 'OK', msg: 'restoring open positions' },
  { level: 'OK', msg: 'risk engine armed (SL / TP watch)' },
  { level: '..', msg: 'ready' },
]

const commands = [
  { to: '/dashboard', name: './dashboard', desc: 'live chart, orders and sys.log' },
  { to: '/trades', name: './trades', desc: 'place, close and review paper trades' },
  { to: '/profile', name: './profile', desc: 'account stats and trade history' },
]

const integrations = [
  { name: 'binance', status: 'online', live: true },
  { name: 'solana', status: 'planned', live: false },
  { name: 'more', status: 'planned', live: false },
]
</script>

<style scoped>
@keyframes boot-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.boot-line {
  opacity: 0;
  animation: boot-in 0.01s steps(1) forwards;
}

@media (prefers-reduced-motion: reduce) {
  .boot-line {
    opacity: 1;
    animation: none;
  }
}

.cmd-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 24px;
  padding: 8px 0;
  border-top: 1px dashed var(--line);
}

.cmd-row:first-child {
  border-top: 0;
  padding-top: 0;
}

.cmd-link {
  width: 9rem;
  color: var(--accent);
  font-weight: 700;
  text-decoration: none;
}

.cmd-link:hover {
  text-decoration: underline;
}
</style>
