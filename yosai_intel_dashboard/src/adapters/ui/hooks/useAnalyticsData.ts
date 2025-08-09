import { useEffect, useRef, useState, useCallback } from 'react';
import { useAnalyticsStore } from '../state/store';
import { AnalyticsData } from '../state/analyticsSlice';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/v1';

const useAnalyticsData = (sourceType: string) => {
  const { analyticsCache, setAnalytics } = useAnalyticsStore();
  const controllerRef = useRef<AbortController | null>(null);
  const [loading, setLoading] = useState(!analyticsCache[sourceType]);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(
    async (signal: AbortSignal) => {
      setError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/analytics/${sourceType}`, {
          signal,
          credentials: 'include',
        });
        if (!res.ok) {
          throw new Error('Failed to fetch analytics');
        }
        const payload = await res.json();
        const data: AnalyticsData = payload.data ? payload.data : payload;
        setAnalytics(sourceType, data);
      } catch (err: any) {
        if (signal.aborted) return;
        setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
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

export default useAnalyticsData;
