import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './setupTests.ts',
    include: [
      'components/**/*.vitest.test.{ts,tsx}',
      'pages/**/*.vitest.test.{ts,tsx}',
    ],
    exclude: ['yosai_intel_dashboard/**'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname),
      'react-native': 'react-native-web',
    },
  },
  css: {
    postcss: {
      plugins: [],
    },
  },
});
