import { useState, useRef, useCallback } from 'react';

export interface ExportOptions {
  fileType: string;
  columns: string[];
  timezone: string;
  locale: string;
}

type ExportStatus = 'idle' | 'exporting' | 'completed' | 'error';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

export const useExportData = () => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<ExportStatus>('idle');
  const controllerRef = useRef<AbortController | null>(null);

  const startExport = useCallback(async (options: ExportOptions) => {
    setStatus('exporting');
    setProgress(0);
    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const response = await fetch(`${API_URL}/api/v1/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const contentLength = response.headers.get('content-length');
      const total = contentLength ? parseInt(contentLength, 10) : 0;
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Readable stream not supported');
      }
      const chunks: Uint8Array[] = [];
      let received = 0;
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (value) {
          chunks.push(value);
          received += value.length;
          if (total) {
            setProgress(Math.round((received / total) * 100));
          }
        }
      }

      // Create a blob from the chunks and trigger download
      const blob = new Blob(chunks, { type: 'application/octet-stream' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const ext = options.fileType || 'dat';
      link.download = `export.${ext}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setProgress(100);
      setStatus('completed');
    } catch (err) {
      if ((err as any)?.name === 'AbortError') {
        setStatus('idle');
      } else {
        console.error(err);
        setStatus('error');
      }
    } finally {
      controllerRef.current = null;
    }
  }, []);

  const cancelExport = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  return {
    startExport,
    progress,
    status,
    cancelExport,
  };
};

export default useExportData;
