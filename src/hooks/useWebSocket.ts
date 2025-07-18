import { useRef } from 'react';

interface ProgressCallback {
  (progress: number): void;
}

export const useWebSocket = () => {
  const sockets = useRef<Record<string, WebSocket>>({});

  const subscribeToUploadProgress = (taskId: string, cb: ProgressCallback) => {
    if (sockets.current[taskId]) return;
    const ws = new WebSocket(`ws://localhost:8050/ws/upload/${taskId}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.progress !== undefined) {
        cb(data.progress);
      }
    };
    ws.onclose = () => {
      delete sockets.current[taskId];
    };
    sockets.current[taskId] = ws;
  };

  return { subscribeToUploadProgress };
};
