import { StateCreator } from 'zustand';

export interface PreferencesSlice {
  saveData: boolean;
  setSaveData: (value: boolean) => void;
}

export const createPreferencesSlice: StateCreator<PreferencesSlice, [], [], PreferencesSlice> = (set) => ({
  saveData: false,
  setSaveData: (value: boolean) => set({ saveData: value }),
});
