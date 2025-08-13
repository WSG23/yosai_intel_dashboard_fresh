import { useEffect, useRef, useState } from 'react';
import { defaultPool, HEARTBEAT_TIMEOUT } from './websocketPool';
import { eventBus } from '../eventBus';
import websocket_metrics from '../metrics/websocket_metrics';
import ExtendedWebSocket from './extendedWebSocket';


export enum WebSocketState {
  DISCONNECTED,
  RECONNECTING,
  CONNECTED,
}

interface FallbackOptions {
  /** EventSource URL to use when websocket fails repeatedly */
  fallbackPath?: string;
  /** Factory for creating EventSource instances (mainly for tests) */
  eventSourceFactory?: (url: string) => EventSource;
  /** Number of consecutive websocket failures before using EventSource */
  maxRetries?: number;
}

export const useWebSocket = (
  path: string,
  socketFactory?: (url: string) => WebSocket,
  options: FallbackOptions = {}
) => {
  const [data, setData] = useState<string | null>(null);
  const [state, setState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const wsRef = useRef<ExtendedWebSocket | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const retryTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const stoppedRef = useRef(false);

  const connectEventSource = () => {
    const fallbackUrl = options.fallbackPath
      ? options.fallbackPath.startsWith('http')
        ? options.fallbackPath
        : `${window.location.origin}${options.fallbackPath}`
      : path.startsWith('ws')
        ? path.replace(/^ws/, 'http')
        : `${window.location.origin}${path}`;
    const es = options.eventSourceFactory
      ? options.eventSourceFactory(fallbackUrl)
      : new EventSource(fallbackUrl);
    esRef.current = es;
    es.onopen = () => {
      setState(WebSocketState.CONNECTED);
      eventBus.emit('websocket_state', WebSocketState.CONNECTED);
    };
    es.onmessage = (ev: MessageEvent) => setData(ev.data as string);
    es.onerror = () => {
      setState(WebSocketState.DISCONNECTED);
      eventBus.emit('websocket_state', WebSocketState.DISCONNECTED);
    };
  };

  const connect = () => {
    const fullUrl = path.startsWith('ws')
      ? path
      : `ws://${window.location.host}${path}`;
    const ws = (socketFactory ? socketFactory(fullUrl) : defaultPool.get(fullUrl)) as ExtendedWebSocket;
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
      websocket_metrics.record_reconnect_attempt();
      const delay = Math.min(1000 * 2 ** attemptRef.current, 30000);
      attemptRef.current += 1;
      const maxRetries = options.maxRetries ?? 5;
      if (attemptRef.current >= maxRetries) {
        if (heartbeatTimeout.current) {
          clearTimeout(heartbeatTimeout.current);
        }
        connectEventSource();
        return;
      }
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
    esRef.current?.close();
  };
  useEffect(() => {
    stoppedRef.current = false;
    connect();

    return () => {
      cleanup();
    };
  }, [path, socketFactory, options.fallbackPath, options.eventSourceFactory, options.maxRetries]);

  const isConnected = state === WebSocketState.CONNECTED;
  return { data, isConnected, state, cleanup };
};

export default useWebSocket;
