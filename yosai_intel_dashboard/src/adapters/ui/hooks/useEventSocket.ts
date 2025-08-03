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
) => {
  const [data, setData] = useState<string | null>(null);
  const [state, setState] = useState<EventSocketState>(EventSocketState.DISCONNECTED);
  const wsRef = useRef<WebSocket | null>(null);
  const stoppedRef = useRef(false);

  useEffect(() => {
    stoppedRef.current = false;
    setState(EventSocketState.CONNECTING);
    eventBus.emit('event_socket_state', EventSocketState.CONNECTING);
    const ws = socketFactory ? socketFactory(url) : new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setState(EventSocketState.CONNECTED);
      eventBus.emit('event_socket_state', EventSocketState.CONNECTED);
    };
    ws.onclose = () => {
      if (stoppedRef.current) {
        return;
      }
      setState(EventSocketState.DISCONNECTED);
      eventBus.emit('event_socket_state', EventSocketState.DISCONNECTED);
    };
    ws.onmessage = (ev) => setData(ev.data);

    return () => {
      stoppedRef.current = true;
      setState(EventSocketState.DISCONNECTED);
      eventBus.emit('event_socket_state', EventSocketState.DISCONNECTED);
      ws.close();
    };
  }, [url, socketFactory]);

  const isConnected = state === EventSocketState.CONNECTED;
  return { data, isConnected, state };
};
