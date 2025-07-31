import React, { createContext, useContext, useState } from 'react';
import { ParsedData } from '../hooks/useFileParser';

export interface UploadFile {
  file: File;
  data?: ParsedData;
}

interface UploadState {
  files: UploadFile[];
  setFiles: React.Dispatch<React.SetStateAction<UploadFile[]>>;
}

const UploadContext = createContext<UploadState | undefined>(undefined);

export const UploadProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  return (
    <UploadContext.Provider value={{ files, setFiles }}>
      {children}
    </UploadContext.Provider>
  );
};

export const useUploadContext = () => {
  const ctx = useContext(UploadContext);
  if (!ctx) throw new Error('useUploadContext must be within UploadProvider');
  return ctx;
};
