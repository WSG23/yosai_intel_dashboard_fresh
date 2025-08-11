export interface ExtendedWebSocket extends WebSocket {
  on?: (event: string, listener: (...args: unknown[]) => void) => void;
  pong?: () => void;
}

export default ExtendedWebSocket;

