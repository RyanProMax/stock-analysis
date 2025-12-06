import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const base = process.env.GITHUB_ACTIONS ? '/stock-analysis/' : '/'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'html-transform',
      transformIndexHtml(html) {
        return html.replace(/href="\/favicons\//g, `href="${base}favicons/`)
      },
    },
  ],
  base,
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
