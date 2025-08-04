import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './playwright',
  projects: [
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
});
