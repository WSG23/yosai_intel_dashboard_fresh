import { useEffect, useRef, useState } from 'react';
import { defaultPool, HEARTBEAT_TIMEOUT } from './websocketPool';
import { eventBus } from '../eventBus';

export enum WebSocketState {
  DISCONNECTED,
  RECONNECTING,
  CONNECTED,
}

export const useWebSocket = (
  path: string,
  socketFactory?: (url: string) => WebSocket
) => {
  const [data, setData] = useState<string | null>(null);
  const [state, setState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const wsRef = useRef<WebSocket | null>(null);
  const retryTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const stoppedRef = useRef(false);

  const connect = () => {
    const fullUrl = path.startsWith('ws')
      ? path
      : `ws://${window.location.host}${path}`;
    const ws = socketFactory ? socketFactory(fullUrl) : defaultPool.get(fullUrl);
    wsRef.current = ws;

    const resetHeartbeat = () => {
      if (heartbeatTimeout.current) {
        clearTimeout(heartbeatTimeout.current);
      }
      heartbeatTimeout.current = setTimeout(() => ws.close(), HEARTBEAT_TIMEOUT);
    };
    resetHeartbeat();
    if (typeof (ws as any).on === 'function') {
      (ws as any).on('ping', () => {
        (ws as any).pong?.();
        resetHeartbeat();
      });
    }


    ws.onopen = () => {
      setState(WebSocketState.CONNECTED);
      eventBus.emit('websocket_state', WebSocketState.CONNECTED);
      attemptRef.current = 0;
    };
    ws.onclose = () => {
      if (stoppedRef.current) {
        return;
      }
      setState(WebSocketState.RECONNECTING);
      eventBus.emit('websocket_state', WebSocketState.RECONNECTING);
      const delay = Math.min(1000 * 2 ** attemptRef.current, 30000);
      attemptRef.current += 1;
      retryTimeout.current = setTimeout(connect, delay);
    };
    ws.onmessage = (ev: MessageEvent) => setData(ev.data as string);
  };

  const cleanup = () => {
    stoppedRef.current = true;
    if (retryTimeout.current) {
      clearTimeout(retryTimeout.current);
    }
    if (heartbeatTimeout.current) {
      clearTimeout(heartbeatTimeout.current);
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

  const isConnected = state === WebSocketState.CONNECTED;
  return { data, isConnected, state, cleanup };
};

export default useWebSocket;
