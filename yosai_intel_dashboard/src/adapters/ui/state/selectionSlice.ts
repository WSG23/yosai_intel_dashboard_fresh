import { StateCreator } from 'zustand';

export interface SelectionSlice {
  selectedThreats: string[];
  selectedRange: [number, number] | null;
  setSelectedThreats: (ids: string[]) => void;
  setSelectedRange: (range: [number, number] | null) => void;
}

export const createSelectionSlice: StateCreator<SelectionSlice, [], [], SelectionSlice> = (set) => ({
  selectedThreats: [],
  selectedRange: null,
  setSelectedThreats: (ids) => set({ selectedThreats: ids }),
  setSelectedRange: (range) => set({ selectedRange: range }),
});

