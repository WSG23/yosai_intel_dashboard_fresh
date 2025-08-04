import { StateCreator } from 'zustand';

export type TableDensity = 'compact' | 'comfortable' | 'spacious';

export interface UiSlice {
  tableDensity: TableDensity;
  setTableDensity: (d: TableDensity) => void;
}

export const createUiSlice: StateCreator<UiSlice, [], [], UiSlice> = (set) => ({
  tableDensity: 'comfortable',
  setTableDensity: (d) => set({ tableDensity: d }),
});
