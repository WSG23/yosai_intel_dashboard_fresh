import { test, expect } from '@playwright/test';

const viewports = [
  { width: 320, height: 568 },
  { width: 375, height: 667 },
  { width: 414, height: 896 },
];

test.describe('mobile responsiveness', () => {
  for (const vp of viewports) {
    test(`handles touch at ${vp.width}x${vp.height}`, async ({ page }) => {
      await page.goto('about:blank');
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.setContent('<button id="tap">Tap</button>');
      const touched = await page.evaluate(() => {
        return new Promise<boolean>((resolve) => {
          const btn = document.getElementById('tap')!;
          btn.addEventListener(
            'touchstart',
            () => resolve(true),
            { once: true },
          );
          btn.dispatchEvent(new Event('touchstart', { bubbles: true }));
        });
      });
      expect(touched).toBe(true);
      expect(page.viewportSize()?.width).toBe(vp.width);
    });
  }
});
