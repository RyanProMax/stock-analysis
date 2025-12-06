import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: process.env.GITHUB_ACTIONS ? '/stock-analysis/' : '/',
  server: {
    port: 3000,
    proxy: {
      '/stock': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
