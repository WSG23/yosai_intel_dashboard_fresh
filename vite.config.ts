import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@headlessui/react', '@heroicons/react'],
          charts: ['recharts', 'd3', 'echarts'],
          maps: ['mapbox-gl', 'deck.gl'],
        },
      },
    },
  },
});
