import { useRef } from 'react';

interface ProgressCallback {
  (progress: number): void;
}

export const useUploadWebSocket = () => {
  const sockets = useRef<Record<string, WebSocket>>({});

  const subscribeToUploadProgress = (taskId: string, cb: ProgressCallback) => {
    if (sockets.current[taskId]) return;
    const ws = new WebSocket(`ws://localhost:5001/ws/upload/${taskId}`);
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

  const unsubscribe = (taskId: string) => {
    const ws = sockets.current[taskId];
    if (ws) {
      ws.close();
      delete sockets.current[taskId];
    }
  };

  return { subscribeToUploadProgress, unsubscribe };
};

export default useUploadWebSocket;
