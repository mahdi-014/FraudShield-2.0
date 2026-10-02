import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/v1': {
        target: process.env.FRAUDSHIELD_BACKEND_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: process.env.FRAUDSHIELD_BACKEND_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
