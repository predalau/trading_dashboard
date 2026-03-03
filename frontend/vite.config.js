import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  base: '/trading/',
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    middlewareMode: false,
    allowedHosts: ['preda.home.ro', 'investhor_frontend', 'localhost'],
    hmr: {
      host: 'localhost',
      port: 5173,
      protocol: 'ws'
    },
    proxy: {
      '/trading/api': {
        target: 'http://investhor_backend:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/trading\/api/, '/api')
      }
    }
  }
})
