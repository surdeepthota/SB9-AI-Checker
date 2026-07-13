import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev server proxies API routes to the FastAPI backend so the app uses the same
// relative URLs in dev and production (where FastAPI serves the built frontend).
const backend = 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/analyze': backend,
      '/analyze-sample': backend,
      '/samples': backend,
      '/packet': backend,
      '/api': backend,
    },
  },
})
