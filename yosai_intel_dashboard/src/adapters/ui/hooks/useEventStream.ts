import { useEffect, useRef, useState } from 'react';

export const useEventStream = (
  path: string,
  eventSourceFactory?: (url: string) => EventSource,
  enabled: boolean = true,
) => {
  const [data, setData] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) return;
    const fullUrl = path.startsWith('http')
      ? path
      : `${window.location.origin}${path}`;
    const es = eventSourceFactory ? eventSourceFactory(fullUrl) : new EventSource(fullUrl);
    esRef.current = es;

    es.onopen = () => setIsConnected(true);
    es.onmessage = (ev: MessageEvent) => setData(ev.data as string);
    es.onerror = () => setIsConnected(false);

    return () => {
      es.close();
    };
  }, [path, eventSourceFactory, enabled]);

  return { data, isConnected };
};

export default useEventStream;
