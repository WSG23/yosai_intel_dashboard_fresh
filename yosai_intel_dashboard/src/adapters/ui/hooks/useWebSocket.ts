import { useEffect, useRef, useState } from 'react';
import { eventBus } from '../eventBus';

export enum WebSocketState {
  DISCONNECTED = 'DISCONNECTED',
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  RECONNECTING = 'RECONNECTING',
}

export const useWebSocket = (
  path: string,
  socketFactory?: (url: string) => WebSocket
) => {
  const [data, setData] = useState<string | null>(null);
  const [state, setState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
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

    const nextState =
      attemptRef.current > 0
        ? WebSocketState.RECONNECTING
        : WebSocketState.CONNECTING;
    setState(nextState);
    eventBus.emit('websocket_state', nextState);

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
    setState(WebSocketState.DISCONNECTED);
    eventBus.emit('websocket_state', WebSocketState.DISCONNECTED);
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
