import { useEffect, useRef, useState } from 'react';
import { eventBus } from '../eventBus';
import { HEARTBEAT_TIMEOUT } from './websocketPool';
import ExtendedWebSocket from './extendedWebSocket';

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
  const wsRef = useRef<ExtendedWebSocket | null>(null);
  const retryTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const stoppedRef = useRef(false);

  const connect = () => {
    setState(EventSocketState.CONNECTING);
    eventBus.emit('event_socket_state', EventSocketState.CONNECTING);

    const ws = (socketFactory ? socketFactory(url) : new WebSocket(url)) as ExtendedWebSocket;
    wsRef.current = ws;

    const resetHeartbeat = () => {
      if (heartbeatTimeout.current) {
        clearTimeout(heartbeatTimeout.current);
      }
      heartbeatTimeout.current = setTimeout(() => ws.close(), HEARTBEAT_TIMEOUT);
    };
    resetHeartbeat();
    if (typeof ws.on === 'function') {
      ws.on('ping', () => {
        ws.pong?.();
        resetHeartbeat();
      });
    }

    ws.onopen = () => {
      setState(EventSocketState.CONNECTED);
      eventBus.emit('event_socket_state', EventSocketState.CONNECTED);
      attemptRef.current = 0;
    };
    ws.onclose = () => {
      if (stoppedRef.current) {
        return;
      }
      setState(EventSocketState.RECONNECTING);
      eventBus.emit('event_socket_state', EventSocketState.RECONNECTING);
      let delay = Math.min(1000 * 2 ** attemptRef.current, 30000);
      if (jitter) {
        delay += Math.random() * 1000;
      }
      attemptRef.current += 1;
      retryTimeout.current = setTimeout(connect, delay);
    };
    ws.onmessage = ev => setData(ev.data as string);
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
    setState(EventSocketState.DISCONNECTED);
    eventBus.emit('event_socket_state', EventSocketState.DISCONNECTED);
  };

  useEffect(() => {
    stoppedRef.current = false;
    connect();

    return () => {
      cleanup();
    };
  }, [url, socketFactory, jitter]);

  const isConnected = state === EventSocketState.CONNECTED;
  return { data, isConnected, state, cleanup };

};

export default useEventSocket;
