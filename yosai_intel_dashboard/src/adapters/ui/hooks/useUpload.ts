import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadedFile, ProcessingStatus as Status } from "../components/upload/types";
import { api } from "../api/client";

const CONCURRENCY_LIMIT = parseInt(
  process.env.REACT_APP_UPLOAD_CONCURRENCY || "3",
  10,
);

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5001";

export const useUpload = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: "pending" as Status,
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
    },
    multiple: true,
  });

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const uploadFile = async (uploadedFile: UploadedFile) => {
    const formData = new FormData();
    formData.append("file", uploadedFile.file);

    setFiles((prev) =>
      prev.map((f) =>
        f.id === uploadedFile.id
          ? { ...f, status: "uploading" as Status, progress: 0, error: undefined }
          : f,
      ),
    );

    try {
      const response = await api.post<{ job_id: string }>(
        `${API_URL}/api/v1/upload`,
        formData,
      );
      const { job_id } = response;

      const poll = setInterval(async () => {
        try {
          const res = await api.get<{ progress?: number; done: boolean }>(
            `${API_URL}/api/v1/upload/status/${job_id}`,
          );
          const progress = res.progress ?? 0;
          setFiles((prev) =>
            prev.map((f) =>
              f.id === uploadedFile.id ? { ...f, progress } : f,
            ),
          );
          if (res.done) {
            clearInterval(poll);
            setFiles((prev) =>
              prev.map((f) =>
                f.id === uploadedFile.id
                  ? { ...f, status: "completed" as Status, progress: 100 }
                  : f,
              ),
            );
          }
        } catch (err) {
          clearInterval(poll);
          setFiles((prev) =>
            prev.map((f) =>
              f.id === uploadedFile.id
                ? {
                    ...f,
                    status: "error" as Status,
                    error: "Processing failed",
                  }
                : f,
            ),
          );
        }
      }, 1000);
    } catch (error) {
      console.error("Upload error:", error);
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadedFile.id
            ? {
                ...f,
                status: "error" as Status,
                error: (error as Error).message || "Unknown error",
              }
            : f,
        ),
      );
    }
  };

  const uploadAllFiles = async () => {
    setUploading(true);
    const pendingFiles = files.filter(
      (f) => f.status === "pending" || f.status === "error",
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
  };

  return {
    files,
    uploading,
    getRootProps,
    getInputProps,
    isDragActive,
    removeFile,
    uploadAllFiles,
  };
};

export default useUpload;
