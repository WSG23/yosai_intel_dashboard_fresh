import { useEffect, useRef, useState } from 'react';
import { eventBus } from '../eventBus';

export enum EventSocketState {
  DISCONNECTED = 'DISCONNECTED',
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  RECONNECTING = 'RECONNECTING',
}

export const useEventSocket = (
  url: string,
  socketFactory?: (url: string) => WebSocket,
  jitter: boolean = true,
) => {
  const [data, setData] = useState<string | null>(null);
  const [state, setState] = useState<EventSocketState>(EventSocketState.DISCONNECTED);
  const wsRef = useRef<WebSocket | null>(null);
  const retryTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const stoppedRef = useRef(false);

  const connect = () => {

    const ws = socketFactory ? socketFactory(url) : new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      attemptRef.current = 0;
    };
    ws.onclose = () => {
      setIsConnected(false);
      if (!stoppedRef.current) {
        let delay = Math.min(1000 * 2 ** attemptRef.current, 30000);
        if (jitter) {
          delay += Math.random() * 1000;
        }
        attemptRef.current += 1;
        retryTimeout.current = setTimeout(connect, delay);
      }

    };
    ws.onmessage = (ev) => setData(ev.data);
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
  }, [url, socketFactory, jitter]);

  return { data, isConnected, cleanup };

};

export default useEventSocket;
