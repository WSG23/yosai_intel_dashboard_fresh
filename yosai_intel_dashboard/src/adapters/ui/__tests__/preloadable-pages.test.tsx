import React from 'react';

// We import the module to ensure the lazy declarations are type-correct.
// The test only ensures calling preload() does not throw when present.
import * as UI from '../index';

test('Preloadable lazy pages expose preload() (if defined) without throwing', () => {
  const maybePages = [
    (UI as any).RealTimeAnalyticsPage,
    (UI as any).Upload,
    (UI as any).Analytics,
    (UI as any).Graphs,
    (UI as any).Export,
    (UI as any).Settings,
    (UI as any).DashboardBuilder,
  ].filter(Boolean);

  for (const p of maybePages) {
    if (typeof p?.preload === 'function') {
      expect(() => p.preload()).not.toThrow();
    }
  }
});
