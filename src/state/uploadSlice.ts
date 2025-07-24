import { StateCreator } from 'zustand';
import { UploadedFile } from '../components/upload/types';

export interface UploadSlice {
  uploadedFiles: UploadedFile[];
  setUploadedFiles: (files: UploadedFile[]) => void;
}

export const createUploadSlice: StateCreator<UploadSlice, [], [], UploadSlice> = (set) => ({
  uploadedFiles: [],
  setUploadedFiles: (files: UploadedFile[]) => set({ uploadedFiles: files }),
});
