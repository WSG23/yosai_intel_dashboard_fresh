import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload as UploadIcon } from "lucide-react";
import { FilePreview } from "./FilePreview";
import { ColumnMappingModal } from "./ColumnMappingModal";
import { DeviceMappingModal } from "./DeviceMappingModal";
import { UploadedFile, ProcessingStatus as Status, FileData } from "./types";
import { api } from "../../api/client";


const CONCURRENCY_LIMIT = parseInt(
  process.env.REACT_APP_UPLOAD_CONCURRENCY || "3",
  10,
);

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5001";

const Upload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [showColumnMapping, setShowColumnMapping] = useState(false);
  const [showDeviceMapping, setShowDeviceMapping] = useState(false);
  const [currentFile, setCurrentFile] = useState<UploadedFile | null>(null);
  const [fileData, setFileData] = useState<FileData | null>(null);
  const [devices, setDevices] = useState<string[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
      id: crypto.randomUUID(),
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
          ? {
              ...f,
              status: "uploading" as Status,
              progress: 0,
              error: undefined,
            }
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

  const handleColumnMappingConfirm = (mappings: Record<string, string>) => {
    console.log("Column mappings confirmed:", mappings);
    setShowColumnMapping(false);
    setCurrentFile(null);
  };

  const handleDeviceMappingConfirm = (mappings: Record<string, any>) => {
    console.log("Device mappings confirmed:", mappings);
    setShowDeviceMapping(false);
    setCurrentFile(null);
  };

  return (
    <div className="p-6 bg-background">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Upload Files</h1>

        <div
          {...getRootProps()}
          role="button"
          aria-label="File upload drop zone"
          aria-describedby="upload-desc"
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}
        >
          <input {...getInputProps({ 'aria-label': 'Upload files' })} />
          <UploadIcon
            className="w-12 h-12 mx-auto mb-4 text-muted-foreground"
            aria-hidden="true"
          />
          <p className="text-lg mb-2">
            {isDragActive ? "Drop files here..." : "Drag & drop files here"}
          </p>
          <p id="upload-desc" className="text-sm text-muted-foreground">
            or click to select files (CSV, XLS, XLSX)
          </p>
        </div>

        {files.length > 0 && (
          <div className="mt-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Files ({files.length})</h2>
              <button
                onClick={uploadAllFiles}
                disabled={
                  uploading || files.every((f) => f.status !== "pending")
                }
                aria-busy={uploading}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? "Uploading..." : "Upload All"}
              </button>
            </div>

            <div className="space-y-3" aria-live="polite">
              {files.map((file) => (
                <FilePreview
                  key={file.id}
                  file={file}
                  onRemove={() => removeFile(file.id)}
                />
              ))}
            </div>
          </div>
        )}

        <ColumnMappingModal
          isOpen={showColumnMapping}
          onClose={() => {
            setShowColumnMapping(false);
            setCurrentFile(null);
          }}
          fileData={fileData}
          onConfirm={handleColumnMappingConfirm}
        />

        <DeviceMappingModal
          isOpen={showDeviceMapping}
          onClose={() => {
            setShowDeviceMapping(false);
            setCurrentFile(null);
          }}
          devices={devices}
          filename={currentFile?.name || ""}
          onConfirm={handleDeviceMappingConfirm}
        />
      </div>
    </div>
  );
};

export default Upload;
