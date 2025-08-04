import { create } from 'zustand';

interface DataEnhancerState {
  uploadedData: string | null;
  columnSuggestions: string[];
  enhancedData: string | null;
  uploadStatus: string;
  aiStatus: string;
  enhanceStatus: string;
  setUploadedData: (data: string, status: string) => void;
  setColumnSuggestions: (suggestions: string[], status: string) => void;
  setEnhancedData: (data: string, status: string) => void;
}

export const useDataEnhancerStore = create<DataEnhancerState>((set) => ({
  uploadedData: null,
  columnSuggestions: [],
  enhancedData: null,
  uploadStatus: '',
  aiStatus: '',
  enhanceStatus: '',
  setUploadedData: (data, status) => set({ uploadedData: data, uploadStatus: status }),
  setColumnSuggestions: (suggestions, status) =>
    set({ columnSuggestions: suggestions, aiStatus: status }),
  setEnhancedData: (data, status) => set({ enhancedData: data, enhanceStatus: status }),
}));
