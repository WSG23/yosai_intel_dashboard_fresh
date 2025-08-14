import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: process.env.ANALYZE
    ? [visualizer({ filename: 'bundle-stats.html', open: true })]
    : [],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@headlessui/react', '@heroicons/react'],
          charts: ['echarts'],
          maps: ['mapbox-gl'],
        },
      },
    },
  },
});
