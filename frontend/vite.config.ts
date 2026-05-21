import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // The dev origin is pinned so it always matches the backend CORS
    // allow-list (FRONTEND_ORIGIN = http://localhost:5173). strictPort makes a
    // busy port fail loudly instead of silently moving to 5174, which the
    // backend would then CORS-block.
    port: 5173,
    strictPort: true,
  },
  test: {
    // The Vitest suite covers only the pure lib/ modules, so the default node
    // environment is enough (no jsdom).
    environment: 'node',
  },
})
