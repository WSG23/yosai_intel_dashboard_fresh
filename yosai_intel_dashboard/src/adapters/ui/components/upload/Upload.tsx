import React, { useState } from "react";
import { Upload as UploadIcon } from "lucide-react";
import { FilePreview } from "./FilePreview";
import { ColumnMappingModal } from "./ColumnMappingModal";
import { DeviceMappingModal } from "./DeviceMappingModal";
import {
  FileData,
  UploadedFile,
} from "./types";
import useUpload from "../../hooks/useUpload";

const Upload: React.FC = () => {

  const [showColumnMapping, setShowColumnMapping] = useState(false);
  const [showDeviceMapping, setShowDeviceMapping] = useState(false);
  const [currentFile, setCurrentFile] = useState<UploadedFile | null>(null);
  const [fileData, setFileData] = useState<FileData | null>(null);
  const [devices, setDevices] = useState<string[]>([]);

  const {
    files,
    getRootProps,
    getInputProps,
    isDragActive,
    removeFile,
    uploadAllFiles,
    uploading,
    cancelUpload,
  } = useUpload();

  const handleColumnMappingConfirm = (_mappings: Record<string, string>) => {
    setShowColumnMapping(false);
    setCurrentFile(null);
  };

  const handleDeviceMappingConfirm = (_mappings: Record<string, unknown>) => {
    setShowDeviceMapping(false);
    setCurrentFile(null);
  };

  return (
    <div className="p-6 bg-background">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Upload Files</h1>

        <div
          {...getRootProps({
            role: "button",
            "aria-label": "File upload drop zone",
            "aria-describedby": "upload-desc",
            className: `border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50"
            }`,
          })}
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
                  onCancel={() => cancelUpload(file.id)}
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
