import { useEffect, useRef, useState } from 'react';

/**
 * Simple deep merge that treats `null` values as delete operations.
 */
const mergeDeep = (target: any, patch: any): any => {
  if (typeof patch !== 'object' || patch === null) {
    return patch;
  }
  const output = Array.isArray(target) ? [...target] : { ...(target || {}) };
  for (const key of Object.keys(patch)) {
    const value = patch[key];
    if (value === null) {
      delete output[key];
    } else if (typeof value === 'object') {
      output[key] = mergeDeep(target ? target[key] : undefined, value);
    } else {
      output[key] = value;
    }
  }
  return output;
};

export const useEventStream = (
  path: string,
  eventSourceFactory?: (url: string) => EventSource,
  enabled: boolean = true,
  debounce: number = 100,
) => {
  const [data, setData] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);
  const bufferRef = useRef<any[]>([]);
  const stateRef = useRef<any>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const flush = () => {
    timeoutRef.current = null;
    if (bufferRef.current.length === 0) return;
    let next = stateRef.current;
    for (const patch of bufferRef.current) {
      if (typeof patch === 'string') {
        next = patch;
      } else {
        next = mergeDeep(typeof next === 'object' ? next : {}, patch);
      }
    }
    bufferRef.current = [];
    stateRef.current = next;
    setData(next);
  };

  const schedule = () => {
    if (timeoutRef.current) return;
    timeoutRef.current = setTimeout(flush, debounce);
  };

  useEffect(() => {
    if (!enabled) return;
    const fullUrl = path.startsWith('http')
      ? path
      : `${window.location.origin}${path}`;
    const es = eventSourceFactory ? eventSourceFactory(fullUrl) : new EventSource(fullUrl);
    esRef.current = es;

    es.onopen = () => setIsConnected(true);
    es.onmessage = (ev: MessageEvent) => {
      try {
        bufferRef.current.push(JSON.parse(ev.data));
      } catch {
        bufferRef.current.push(ev.data);
      }
      schedule();
    };
    es.onerror = () => setIsConnected(false);

    return () => {
      es.close();
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      bufferRef.current = [];
    };
  }, [path, eventSourceFactory, enabled, debounce]);

  return { data, isConnected };
};

export default useEventStream;
