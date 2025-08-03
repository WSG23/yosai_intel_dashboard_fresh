import { useEffect, useState } from 'react';
import { useWebSocket } from '.';

export interface RealTimeAnalytics {
  [key: string]: any;
}

export const useRealTimeAnalytics = (
  url: string = 'ws://localhost:6789',
  interval: number = 1000,
  socketFactory?: (url: string) => WebSocket,
) => {
  const { data: raw } = useWebSocket(url, socketFactory);
  const [data, setData] = useState<RealTimeAnalytics | null>(null);
  const [summary, setSummary] = useState<RealTimeAnalytics | null>(null);
  const [charts, setCharts] = useState<RealTimeAnalytics | null>(null);

  useEffect(() => {
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        setData(parsed);
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
