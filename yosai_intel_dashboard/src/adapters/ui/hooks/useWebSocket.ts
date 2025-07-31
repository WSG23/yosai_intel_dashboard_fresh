import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (
  path: string,
  socketFactory?: (url: string) => WebSocket
) => {
  const [data, setData] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retryTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const stoppedRef = useRef(false);

  const connect = () => {
    const fullUrl = path.startsWith('ws')
      ? path
      : `ws://${window.location.host}${path}`;
    const ws = socketFactory ? socketFactory(fullUrl) : new WebSocket(fullUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      attemptRef.current = 0;
    };
    ws.onclose = () => {
      setIsConnected(false);
      if (!stoppedRef.current) {
        const delay = Math.min(1000 * 2 ** attemptRef.current, 30000);
        attemptRef.current += 1;
        retryTimeout.current = setTimeout(connect, delay);
      }
    };
    ws.onmessage = (ev: MessageEvent) => setData(ev.data as string);
  };

  const cleanup = () => {
    stoppedRef.current = true;
    if (retryTimeout.current) {
      clearTimeout(retryTimeout.current);
    }
    wsRef.current?.close();
  };
  useEffect(() => {
    stoppedRef.current = false;
    connect();

    return () => {
      cleanup();
    };
  }, [path, socketFactory]);

  return { data, isConnected, cleanup };
};

export default useWebSocket;
