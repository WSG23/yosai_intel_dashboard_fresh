import { useEffect, useRef, useState } from 'react';

export const useEventSocket = (
  url: string,
  socketFactory?: (url: string) => WebSocket,
) => {
  const [data, setData] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = socketFactory ? socketFactory(url) : new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onmessage = (ev) => setData(ev.data);

    return () => {
      ws.close();
    };
  }, [url]);

  return { data, isConnected };
};
