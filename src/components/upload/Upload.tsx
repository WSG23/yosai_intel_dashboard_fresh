import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload as UploadIcon, X, FileText, AlertCircle } from 'lucide-react';
import { FilePreview } from './FilePreview';
import ProcessingStatus from './ProcessingStatus';
import { ColumnMappingModal } from './ColumnMappingModal';
import { DeviceMappingModal } from './DeviceMappingModal';
import { UploadedFile, ProcessingStatus as Status } from './types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8050';

const Upload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [showColumnMapping, setShowColumnMapping] = useState(false);
  const [showDeviceMapping, setShowDeviceMapping] = useState(false);
  const [currentFile, setCurrentFile] = useState<UploadedFile | null>(null);
  const [fileData, setFileData] = useState<any>(null);
  const [devices, setDevices] = useState<string[]>([]);

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

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    multiple: true,
  });

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const uploadFile = async (uploadedFile: UploadedFile) => {
    const formData = new FormData();
    formData.append('file', uploadedFile.file);

    try {
      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadedFile.id
            ? { ...f, status: 'completed' as Status, progress: 100 }
            : f
        )
      );

      // Show mapping modal based on file type
      if (data.requiresColumnMapping) {
        setCurrentFile(uploadedFile);
        setFileData(data.fileData || {});
        setShowColumnMapping(true);
      } else if (data.requiresDeviceMapping) {
        setCurrentFile(uploadedFile);
        setDevices(data.devices || []);
        setShowDeviceMapping(true);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadedFile.id
            ? { ...f, status: 'error' as Status, error: (error as Error).message || "Unknown error" }
            : f
        )
      );
    }
  };

  const uploadAllFiles = async () => {
    setUploading(true);
    const pendingFiles = files.filter((f) => f.status === 'pending');
    
    for (const file of pendingFiles) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === file.id
            ? { ...f, status: 'uploading' as Status }
            : f
        )
      );
      await uploadFile(file);
    }
    
    setUploading(false);
  };

  const handleColumnMappingConfirm = (mappings: Record<string, string>) => {
    console.log('Column mappings confirmed:', mappings);
    setShowColumnMapping(false);
    setCurrentFile(null);
  };

  const handleDeviceMappingConfirm = (mappings: Record<string, any>) => {
    console.log('Device mappings confirmed:', mappings);
    setShowDeviceMapping(false);
    setCurrentFile(null);
  };

  return (
    <div className="p-6 bg-background">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Upload Files</h1>
        
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}`}
        >
          <input {...getInputProps()} />
          <UploadIcon className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-lg mb-2">
            {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
          </p>
          <p className="text-sm text-muted-foreground">
            or click to select files (CSV, XLS, XLSX)
          </p>
        </div>

        {files.length > 0 && (
          <div className="mt-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Files ({files.length})</h2>
              <button
                onClick={uploadAllFiles}
                disabled={uploading || files.every((f) => f.status !== 'pending')}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Uploading...' : 'Upload All'}
              </button>
            </div>
            
            <div className="space-y-3">
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
          filename={currentFile?.name || ''}
          onConfirm={handleDeviceMappingConfirm}
        />
      </div>
    </div>
  );
};

export default Upload;
