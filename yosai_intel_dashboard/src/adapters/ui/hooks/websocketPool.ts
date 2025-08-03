export const HEARTBEAT_TIMEOUT = 30000;

type Factory = (url: string) => WebSocket;

export class WebSocketPool {
  private sockets = new Map<string, WebSocket>();

  constructor(private factory: Factory = url => new WebSocket(url)) {}

  get(url: string): WebSocket {
    let ws = this.sockets.get(url);
    if (!ws || ws.readyState === WebSocket.CLOSING || ws.readyState === WebSocket.CLOSED) {
      ws = this.factory(url);
      this.sockets.set(url, ws);
      this.setupHeartbeat(ws, url);
      ws.addEventListener?.('close', () => {
        this.sockets.delete(url);
      });
    }
    return ws;
  }

  private setupHeartbeat(ws: any, url: string) {
    if (ws.__hbListener) return;
    ws.__hbListener = true;
    const reset = () => {
      clearTimeout(ws.__hbTimeout);
      ws.__hbTimeout = setTimeout(() => ws.close(), HEARTBEAT_TIMEOUT);
    };
    reset();
    if (typeof ws.on === 'function') {
      ws.on('ping', () => {
        ws.pong?.();
        reset();
      });
    }
  }
}

export const defaultPool = new WebSocketPool();
