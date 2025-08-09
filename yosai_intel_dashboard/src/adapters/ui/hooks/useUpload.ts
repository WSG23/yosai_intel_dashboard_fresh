import { useEffect, useRef } from 'react';
import { api } from '../api/client';

interface ProgressResponse {
  progress?: number;
  done: boolean;
}

export const useUpload = () => {
  const controllers = useRef<Record<string, AbortController>>({});
  const timeouts = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const pollStatus = async (
    id: string,
    jobId: string,
    onProgress: (p: number) => void,
  ): Promise<void> => {
    const controller = new AbortController();
    controllers.current[id] = controller;
    const signal = controller.signal;
    let timeout: ReturnType<typeof setTimeout> | undefined;

    const poll = async (): Promise<void> => {
      const res = await api.get<ProgressResponse>(
        `/api/v1/upload/status/${jobId}`,
        { signal },
      );
      onProgress(res.progress ?? 0);
      if (!res.done) {
        await new Promise<void>((resolve, reject) => {
          timeout = setTimeout(resolve, 1000);
          timeouts.current[id] = timeout!;
          const onAbort = () => {
            if (timeout) clearTimeout(timeout);
            reject(new DOMException('Aborted', 'AbortError'));
          };
          if (signal.aborted) {
            onAbort();
          } else {
            signal.addEventListener('abort', onAbort, { once: true });
          }
        });
        await poll();
      }
    };

    try {
      await poll();
    } finally {
      if (timeout) clearTimeout(timeout);
      delete timeouts.current[id];
      delete controllers.current[id];
    }
  };

  const cancel = (id: string) => {
    controllers.current[id]?.abort();
  };

  useEffect(() => {
    return () => {
      Object.values(controllers.current).forEach((c) => c.abort());
      Object.values(timeouts.current).forEach((t) => clearTimeout(t));
    };
  }, []);

  return { pollStatus, cancel };
};

export default useUpload;

