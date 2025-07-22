import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (
  path: string,
  socketFactory?: (url: string) => WebSocket
) => {
  const [data, setData] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const fullUrl = path.startsWith('ws')
      ? path
      : `ws://${window.location.host}${path}`;
    const ws = socketFactory ? socketFactory(fullUrl) : new WebSocket(fullUrl);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onmessage = (ev: MessageEvent) => setData(ev.data as string);

    return () => {
      ws.close();
    };
  }, [path, socketFactory]);

  return { data, isConnected };
};

export default useWebSocket;
