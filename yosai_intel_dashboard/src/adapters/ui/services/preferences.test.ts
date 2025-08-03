import { getPreferences, savePreferences, resetPreferences } from './preferences';

describe('preferences service', () => {
  beforeEach(() => {
    resetPreferences();
  });

  test('returns default preferences', () => {
    const prefs = getPreferences();
    expect(prefs.colorScheme).toBe('light');
    expect(prefs.defaultZoom).toBe(1);
    expect(prefs.animationSpeed).toBe(1);
  });

  test('saves and retrieves preferences', () => {
    savePreferences({ colorScheme: 'dark', defaultZoom: 2, animationSpeed: 0.5 });
    const prefs = getPreferences();
    expect(prefs).toEqual({ colorScheme: 'dark', defaultZoom: 2, animationSpeed: 0.5 });
  });
});
