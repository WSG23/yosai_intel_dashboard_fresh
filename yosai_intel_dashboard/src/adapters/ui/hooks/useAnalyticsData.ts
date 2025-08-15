import { useCallback, useEffect, useRef, useState } from 'react';
import { useAnalyticsStore } from '../state/store';
import { AnalyticsData } from '../state/analyticsSlice';
import { api } from '../api/client';

export const useAnalyticsData = (sourceType: string) => {
  const { analyticsCache, setAnalytics } = useAnalyticsStore();
  const controllerRef = useRef<AbortController | null>(null);
  const [loading, setLoading] = useState(!analyticsCache[sourceType]);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(
    async (signal: AbortSignal) => {
      setError(null);
      try {
        const data = await api.get<AnalyticsData>(`/analytics/${sourceType}`, {
          signal,
        });
        setAnalytics(sourceType, data);
      } catch (err: unknown) {
        if (signal.aborted) return;
        setError(
          err instanceof Error ? err.message : 'Failed to fetch analytics',
        );
      } finally {
        if (!signal.aborted) {
          setLoading(false);
        }
      }
    },
    [setAnalytics, sourceType],
  );

  const refresh = useCallback(() => {
    const controller = new AbortController();
    controllerRef.current?.abort();
    controllerRef.current = controller;
    setLoading(!analyticsCache[sourceType]);
    fetchData(controller.signal);
  }, [analyticsCache, fetchData, sourceType]);

  useEffect(() => {
    refresh();
    return () => {
      controllerRef.current?.abort();
    };
  }, [refresh, sourceType]);

  const data = analyticsCache[sourceType] || null;

  return { data, loading, error, refresh } as const;
};

