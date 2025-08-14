import { useState, useEffect, useRef, useCallback } from 'react';

export interface UserSettings {
  theme: string;
  itemsPerPage: number;
}

const API_BASE_URL =
  process.env.REACT_APP_API_URL || 'http://localhost:5001/api/v1';
const DEFAULT_SETTINGS: UserSettings = { theme: 'light', itemsPerPage: 10 };
let cachedSettings: UserSettings | null = null;

export default function useSettingsData() {
  const [settings, setSettings] = useState<UserSettings>(
    cachedSettings || DEFAULT_SETTINGS,
  );
  const [loading, setLoading] = useState(!cachedSettings);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const fetchSettings = useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setError(null);
    if (!cachedSettings) {
      setLoading(true);
    }
    try {
      const res = await fetch(`${API_BASE_URL}/settings`, {
        signal: controller.signal,
        credentials: 'include',
      });
      if (!res.ok) {
        throw new Error('Failed to fetch settings');
      }
      const payload = await res.json();
      const data: UserSettings = payload.data ? payload.data : payload;
      cachedSettings = data;
      setSettings(data);
    } catch (err: unknown) {
      if (controller.signal.aborted) return;
      const message =
        err instanceof Error ? err.message : 'Failed to fetch settings';
      setError(message);
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchSettings();
    return () => {
      controllerRef.current?.abort();
    };
  }, [fetchSettings]);

  const refresh = useCallback(() => {
    cachedSettings = null;
    fetchSettings();
  }, [fetchSettings]);

  return { settings, setSettings, loading, error, refresh } as const;
}
