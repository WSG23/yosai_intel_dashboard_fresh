export interface Preferences {
  colorScheme: string;
  defaultZoom: number;
  animationSpeed: number;
}

const PREF_KEY = 'dashboard_preferences';

const DEFAULT_PREFERENCES: Preferences = {
  colorScheme: 'light',
  defaultZoom: 1,
  animationSpeed: 1,
};

export function getPreferences(): Preferences {
  try {
    const raw = localStorage.getItem(PREF_KEY);
    if (!raw) return { ...DEFAULT_PREFERENCES };
    const parsed = JSON.parse(raw);
    return { ...DEFAULT_PREFERENCES, ...parsed } as Preferences;
  } catch {
    return { ...DEFAULT_PREFERENCES };
  }
}

export function savePreferences(update: Partial<Preferences>): Preferences {
  const current = getPreferences();
  const merged = { ...current, ...update };
  localStorage.setItem(PREF_KEY, JSON.stringify(merged));
  return merged;
}

export function resetPreferences() {
  localStorage.removeItem(PREF_KEY);
}
