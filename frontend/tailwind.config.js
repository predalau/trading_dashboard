/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '0',
      },
      colors: {
        term: {
          bg: 'var(--bg)',
          panel: 'var(--panel)',
          surface: 'var(--surface)',
          line: 'var(--line)',
          grid: 'var(--grid)',
          text: 'var(--text)',
          muted: 'var(--muted)',
          accent: 'var(--accent)',
          up: 'var(--up)',
          down: 'var(--down)',
          tp: 'var(--tp)',
          'on-accent': 'var(--on-accent)',
        },
      },
    },
  },
  plugins: [],
}
