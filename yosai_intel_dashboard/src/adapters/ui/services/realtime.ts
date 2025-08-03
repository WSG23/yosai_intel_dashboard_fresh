export interface AccessEvent {
  id: string;
  lng: number;
  lat: number;
  count: number;
  timestamp: string;
  anomaly?: boolean;
}

/**
 * Subscribes to the server-sent event stream for access events.
 * Returns an unsubscribe function that closes the connection.
 */
export const subscribeToAccessStream = (
  onEvent: (evt: AccessEvent) => void,
  url: string = '/api/realtime/access',
): (() => void) => {
  const es = new EventSource(url);
  es.onmessage = (ev: MessageEvent) => {
    try {
      const data = JSON.parse(ev.data);
      onEvent(data as AccessEvent);
    } catch {
      // ignore malformed events
    }
  };
  return () => es.close();
};

export default subscribeToAccessStream;
