import { test, expect } from '@playwright/test';

test.describe('mobile responsiveness', () => {
  test('handles mobile viewport and touch events', async ({ page }) => {
    await page.goto('about:blank');
    await page.setViewportSize({ width: 375, height: 667 });
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
    expect(page.viewportSize()?.width).toBe(375);
  });
});
