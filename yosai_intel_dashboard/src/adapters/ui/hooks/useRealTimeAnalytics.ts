import { useEffect, useState } from 'react';
import { useWebSocket } from '.';
import type { RealTimeAnalyticsPayload } from './useRealTimeAnalyticsData';

export const useRealTimeAnalytics = (
  url: string = 'ws://localhost:6789',
  interval: number = 1000,
  socketFactory?: (url: string) => WebSocket,
) => {
  const { data: raw } = useWebSocket(url, socketFactory);
  const [data, setData] = useState<RealTimeAnalyticsPayload | null>(null);
  const [summary, setSummary] = useState<RealTimeAnalyticsPayload | null>(null);
  const [charts, setCharts] = useState<RealTimeAnalyticsPayload | null>(null);

  useEffect(() => {
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as any;
        if (
          parsed.access_patterns &&
          !Array.isArray(parsed.access_patterns)
        ) {
          parsed.access_patterns = Object.entries(
            parsed.access_patterns as Record<string, number>,
          ).map(([pattern, count]) => ({
            pattern,
            count: Number(count),
          }));
        }
        setData(parsed as RealTimeAnalyticsPayload);
      } catch {
        /* ignore malformed messages */
      }
    }
  }, [raw]);

  useEffect(() => {
    const id = setInterval(() => {
      if (data) {
        setSummary(data);
        setCharts(data);
      }
    }, interval);
    return () => clearInterval(id);
  }, [data, interval]);

  return { data, summary, charts };
};

export default useRealTimeAnalytics;
