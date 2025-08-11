import { useState, useCallback, useRef } from 'react';
import { api } from '../api/client';
import {
  UploadedFile,
  ProcessingStatus as Status,
} from '../components/upload/types';

const CONCURRENCY_LIMIT = parseInt(
  process.env.REACT_APP_UPLOAD_CONCURRENCY || '3',
  10,
);

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

export const useUpload = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const controllers = useRef<Record<string, AbortController>>({});
  const polls = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending' as Status,
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const abortTransfer = useCallback((id: string) => {
    controllers.current[id]?.abort();
    delete controllers.current[id];
    if (polls.current[id]) {
      clearInterval(polls.current[id]);
      delete polls.current[id];
    }
  }, []);

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
    abortTransfer(id);
  }, [abortTransfer]);

  const uploadFile = useCallback(async (uploadedFile: UploadedFile) => {
    const formData = new FormData();
    formData.append('file', uploadedFile.file);

    setFiles((prev) =>
      prev.map((f) =>
        f.id === uploadedFile.id
          ? {
              ...f,
              status: 'uploading' as Status,
              progress: 0,
              error: undefined,
            }
          : f,
      ),
    );

    const controller = new AbortController();
    controllers.current[uploadedFile.id] = controller;

    try {
      const response = await api.post<{ job_id: string }>(
        `${API_URL}/api/v1/upload`,
        formData,
        { signal: controller.signal },
      );
      const { job_id } = response;

      const poll = setInterval(async () => {
        try {
          const res = await api.get<{ progress?: number; done: boolean }>(
            `${API_URL}/api/v1/upload/status/${job_id}`,
            { signal: controller.signal },
          );
          const progress = res.progress ?? 0;
          setFiles((prev) =>
            prev.map((f) =>
              f.id === uploadedFile.id ? { ...f, progress } : f,
            ),
          );
          if (res.done) {
            clearInterval(poll);
            delete polls.current[uploadedFile.id];
            delete controllers.current[uploadedFile.id];
            setFiles((prev) =>
              prev.map((f) =>
                f.id === uploadedFile.id
                  ? { ...f, status: 'completed' as Status, progress: 100 }
                  : f,
              ),
            );
          }
        } catch (err) {
          clearInterval(poll);
          delete polls.current[uploadedFile.id];
          if (controller.signal.aborted) {
            // cancellation handled separately
          } else {
            delete controllers.current[uploadedFile.id];
            setFiles((prev) =>
              prev.map((f) =>
                f.id === uploadedFile.id
                  ? {
                      ...f,
                      status: 'error' as Status,
                      error: 'Processing failed',
                    }
                  : f,
              ),
            );
          }
        }
      }, 1000);
      polls.current[uploadedFile.id] = poll;
    } catch (err: unknown) {
      delete controllers.current[uploadedFile.id];
      const message = controller.signal.aborted
        ? 'Cancelled'
        : err instanceof Error
          ? err.message
          : 'Unknown error';
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadedFile.id
            ? { ...f, status: 'error' as Status, error: message }
            : f,
        ),
      );
    }
  }, []);

  const uploadAllFiles = useCallback(async () => {
    setUploading(true);
    const pendingFiles = files.filter(
      (f) => f.status === 'pending' || f.status === 'error',
    );
    let index = 0;

    const uploadNext = async (): Promise<void> => {
      if (index >= pendingFiles.length) return;
      const next = pendingFiles[index++];
      await uploadFile(next);
      await uploadNext();
    };

    const workers = Array.from(
      { length: Math.min(CONCURRENCY_LIMIT, pendingFiles.length) },
      () => uploadNext(),
    );
    await Promise.all(workers);
    setUploading(false);
  }, [files, uploadFile]);

  const cancelUpload = useCallback(
    (id: string) => {
      abortTransfer(id);
      setFiles((prev) =>
        prev.map((f) =>
          f.id === id
            ? { ...f, status: 'error' as Status, error: 'Cancelled' }
            : f,
        ),
      );
    },
    [abortTransfer],
  );

  return {
    files,
    onDrop,
    removeFile,
    uploadAllFiles,
    uploading,
    cancelUpload,
  };
};

export default useUpload;
