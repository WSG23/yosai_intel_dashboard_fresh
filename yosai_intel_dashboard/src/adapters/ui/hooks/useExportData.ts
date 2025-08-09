import { useCallback, useState } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/v1';

const useExportData = () => {
  const [exporting, setExporting] = useState(false);

  const exportData = useCallback(
    async (format: 'csv' | 'excel' | 'json', dataSource?: string) => {
      setExporting(true);
      const worker = new Worker(
        new URL('../utils/exportWorker.ts', import.meta.url),
        { type: 'module' }
      );

      try {
        const params = new URLSearchParams({ format });
        if (dataSource) params.append('data_source', dataSource);

        const response = await fetch(
          `${API_BASE_URL}/analytics/export?${params.toString()}`,
          { credentials: 'include' }
        );

        const contentType =
          response.headers.get('Content-Type') || 'application/octet-stream';
        const disposition = response.headers.get('Content-Disposition') || '';
        let filename = `export.${format}`;
        const match = disposition.match(/filename="?([^";]+)"?/);
        if (match && match[1]) {
          filename = match[1];
        }

        worker.onmessage = (ev: MessageEvent<{ blob: Blob }>) => {
          const { blob } = ev.data;
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          worker.terminate();
          setExporting(false);
        };

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Streaming not supported');
        }

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value) {
            worker.postMessage({ chunk: value });
          }
        }
        worker.postMessage({ done: true, mimeType: contentType });
      } catch (err) {
        worker.terminate();
        setExporting(false);
        throw err;
      }
    },
    []
  );

  return { exportData, exporting } as const;
};

export default useExportData;
