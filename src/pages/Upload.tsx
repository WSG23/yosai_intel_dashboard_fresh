import React, { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { uploadAPI } from '../api/upload';
import { ColumnMappingModal } from '../components/upload/ColumnMappingModal';
import { DeviceMappingModal } from '../components/upload/DeviceMappingModal';
import { FilePreview } from '../components/upload/FilePreview';
import { ProgressBar } from '../components/shared/ProgressBar';
import { Card } from '../components/shared/Card';
import { useWebSocket } from '../hooks/useWebSocket';

interface UploadFile {
  id: string;
  file: File;
  status: 'pending' | 'uploading' | 'processing' | 'column_mapping' | 'device_mapping' | 'complete' | 'error';
  progress: number;
  data?: any;
  columnMappings?: Record<string, string>;
  deviceMappings?: Record<string, any>;
  error?: string;
}

interface ProcessingStage {
  stage: 'upload' | 'columns' | 'devices' | 'complete';
  file: UploadFile;
}

export const Upload: React.FC = () => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [processingStage, setProcessingStage] = useState<ProcessingStage | null>(null);
  const [showColumnModal, setShowColumnModal] = useState(false);
  const [showDeviceModal, setShowDeviceModal] = useState(false);
  const processingRef = useRef<boolean>(false);
  
  const { subscribeToUploadProgress } = useWebSocket();

  // Handle file drop
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadFile[] = acceptedFiles.map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      status: 'pending',
      progress: 0,
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    
    // Auto-start processing if not already running
    if (!processingRef.current) {
      processNextFile([...files, ...newFiles]);
    }
  }, [files]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    multiple: true,
  });

  // Process next file in queue
  const processNextFile = async (fileList: UploadFile[]) => {
    const nextFile = fileList.find(f => f.status === 'pending');
    if (!nextFile) {
      processingRef.current = false;
      return;
    }

    processingRef.current = true;
    await processFile(nextFile);
    
    // Process next file
    processNextFile(files);
  };

  // Process individual file through all stages
  const processFile = async (uploadFile: UploadFile) => {
    try {
      // Stage 1: Upload
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id ? { ...f, status: 'uploading' } : f
      ));

      const { taskId, data } = await uploadAPI.uploadFile(uploadFile.file);
      
      // Subscribe to progress updates
      subscribeToUploadProgress(taskId, (progress) => {
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id ? { ...f, progress } : f
        ));
      });

      // Wait for processing to complete
      const processed = await uploadAPI.waitForProcessing(taskId);
      
      // Update file with processed data
      const updatedFile: UploadFile = {
        ...uploadFile,
        status: 'processing',
        data: processed,
        progress: 100,
      };
      
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id ? updatedFile : f
      ));

      // Stage 2: Column Mapping
      setProcessingStage({ stage: 'columns', file: updatedFile });
      setShowColumnModal(true);
      
    } catch (error: any) {
      console.error('Processing error:', error);
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id 
          ? { ...f, status: 'error', error: error.message } 
          : f
      ));
      toast.error(`Failed to process ${uploadFile.file.name}`);
    }
  };

  // Handle column mapping confirmation
  const handleColumnMappingConfirm = async (mappings: Record<string, string>) => {
    if (!processingStage) return;

    const { file } = processingStage;
    
    // Update file with column mappings
    const updatedFile: UploadFile = {
      ...file,
      columnMappings: mappings,
      status: 'column_mapping',
    };
    
    setFiles(prev => prev.map(f => 
      f.id === file.id ? updatedFile : f
    ));
    
    // Close column modal and open device modal
    setShowColumnModal(false);
    
    // Apply column mappings and get device list
    const devicesData = await uploadAPI.applyColumnMappings(
      file.data.filename,
      mappings
    );
    
    updatedFile.data = { ...updatedFile.data, ...devicesData };
    
    // Stage 3: Device Mapping
    setProcessingStage({ stage: 'devices', file: updatedFile });
    setShowDeviceModal(true);
  };

  // Handle device mapping confirmation
  const handleDeviceMappingConfirm = async (deviceMappings: Record<string, any>) => {
    if (!processingStage) return;

    const { file } = processingStage;
    
    // Save device mappings
    await uploadAPI.saveDeviceMappings(
      file.data.filename,
      deviceMappings
    );
    
    // Update file status to complete
    const completedFile: UploadFile = {
      ...file,
      deviceMappings,
      status: 'complete',
    };
    
    setFiles(prev => prev.map(f => 
      f.id === file.id ? completedFile : f
    ));
    
    toast.success(`${file.file.name} processed successfully!`);
    
    // Close modal and reset
    setShowDeviceModal(false);
    setProcessingStage(null);
    processingRef.current = false;
    
    // Process next file if any
    processNextFile(files);
  };

  // Calculate overall progress
  const overallProgress = files.length > 0
    ? files.reduce((sum, f) => sum + f.progress, 0) / files.length
    : 0;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          File Upload & Processing
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Upload CSV, JSON, or Excel files for AI-powered analysis and device mapping
        </p>
      </div>

      {/* Upload Zone */}
      <Card>
        <div
          {...getRootProps()}
          className={`
            relative p-12 text-center cursor-pointer
            border-2 border-dashed rounded-lg
            transition-all duration-200
            ${isDragActive 
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
            }
          `}
        >
          <input {...getInputProps()} />
          
          <CloudArrowUpIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
          
          <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {isDragActive
              ? 'Drop files here...'
              : 'Drag & drop files here, or click to browse'}
          </p>
          
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Supports CSV, JSON, XLS, and XLSX files up to 100MB
          </p>
          
          <div className="mt-6 flex items-center justify-center gap-6 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <CheckCircleIcon className="h-4 w-4 text-green-500" />
              AI Column Matching
            </span>
            <span className="flex items-center gap-1">
              <CheckCircleIcon className="h-4 w-4 text-green-500" />
              Smart Device Mapping
            </span>
            <span className="flex items-center gap-1">
              <CheckCircleIcon className="h-4 w-4 text-green-500" />
              Learning System
            </span>
          </div>
        </div>
      </Card>

      {/* Overall Progress */}
      {files.length > 0 && (
        <Card>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">Overall Progress</h3>
              <span className="text-sm text-gray-500">
                {files.filter(f => f.status === 'complete').length} of {files.length} complete
              </span>
            </div>
            <ProgressBar progress={overallProgress} />
          </div>
        </Card>
      )}

      {/* File List */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            <h3 className="text-lg font-medium">Processing Queue</h3>
            
            {files.map(file => (
              <FilePreview
                key={file.id}
                file={file}
                onRemove={() => setFiles(prev => prev.filter(f => f.id !== file.id))}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Column Mapping Modal */}
      {processingStage && (
        <ColumnMappingModal
          isOpen={showColumnModal}
          onClose={() => setShowColumnModal(false)}
          fileData={processingStage.file.data}
          onConfirm={handleColumnMappingConfirm}
        />
      )}

      {/* Device Mapping Modal */}
      {processingStage && (
        <DeviceMappingModal
          isOpen={showDeviceModal}
          onClose={() => setShowDeviceModal(false)}
          devices={processingStage.file.data?.devices || []}
          filename={processingStage.file.data?.filename}
          onConfirm={handleDeviceMappingConfirm}
        />
      )}
    </div>
  );
};
