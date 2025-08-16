import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const port = Number(env.UI_PORT || 5173);
  const target = env.VITE_PROXY_TARGET || "http://api:8000";
  return {
    plugins: [react()],
    server: {
      host: true,
      port,
      strictPort: true,
      proxy: { "/api": { target, changeOrigin: true, ws: false } },
    },
  };
});
