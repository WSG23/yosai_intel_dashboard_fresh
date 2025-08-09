import React from 'react';
import { FileText } from 'lucide-react';
import { ProgressBar } from '../shared/ProgressBar';

interface Props {
  file: {
    id: string;
    file: File;
    status: string;
    progress: number;
    error?: string;
  };
  onRemove: () => void;
  onCancel?: () => void;
}

export const FilePreview: React.FC<Props> = ({ file, onRemove, onCancel }) => {
  return (
    <div className="flex items-center gap-4 p-4 border rounded-md bg-white dark:bg-gray-800">
      <FileText className="h-6 w-6 text-gray-400" />
      <div className="flex-1">
        <div className="flex justify-between">
          <span className="font-medium text-sm">{file.file.name}</span>
          <div className="flex gap-2">
            {file.status === 'uploading' && onCancel && (
              <button onClick={onCancel} className="text-red-500 text-xs">
                Cancel
              </button>
            )}
            <button onClick={onRemove} className="text-red-500 text-xs">Remove</button>
          </div>
        </div>
        <ProgressBar progress={file.progress} className="mt-2" />
        {file.error && <p className="text-xs text-red-500 mt-1">{file.error}</p>}
      </div>
    </div>
  );
};
