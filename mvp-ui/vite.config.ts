import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const uiPort = Number(env.UI_PORT || 5173)
  const target = env.VITE_PROXY_TARGET || 'http://localhost:8000' // local fallback

  return {
    plugins: [react()],
    server: {
      host: true,
      port: uiPort,
      strictPort: true,
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
        },
      },
    },
  }
})
