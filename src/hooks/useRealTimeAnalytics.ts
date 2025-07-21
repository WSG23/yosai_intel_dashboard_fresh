import { useEffect, useRef, useState } from 'react';

export interface RealTimeAnalytics {
  [key: string]: any;
}

export const useRealTimeAnalytics = (
  url: string = 'ws://localhost:6789',
  interval: number = 1000,
  socketFactory?: (url: string) => WebSocket,
) => {
  const [data, setData] = useState<RealTimeAnalytics | null>(null);
  const [summary, setSummary] = useState<RealTimeAnalytics | null>(null);
  const [charts, setCharts] = useState<RealTimeAnalytics | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = socketFactory ? socketFactory(url) : new WebSocket(url);
    wsRef.current = ws;
    ws.onmessage = (ev: MessageEvent) => {
      try {
        const parsed = JSON.parse(ev.data as string);
        setData(parsed);
      } catch {
        /* ignore malformed messages */
      }
    };
    return () => {
      ws.close();
    };
  }, [url, socketFactory]);

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
