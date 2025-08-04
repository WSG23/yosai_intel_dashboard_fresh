import { createStore } from 'zustand';
import { useStore } from 'zustand';
import { createSessionSlice, SessionSlice } from './sessionSlice';
import { createAnalyticsSlice, AnalyticsSlice } from './analyticsSlice';
import { createUploadSlice, UploadSlice } from './uploadSlice';
import { createSelectionSlice, SelectionSlice } from './selectionSlice';
import { createProficiencySlice, ProficiencySlice } from './proficiencySlice';

export type BoundState =
  SessionSlice &
  AnalyticsSlice &
  UploadSlice &
  SelectionSlice &
  ProficiencySlice;

export const boundStore = createStore<BoundState>()((...a) => ({
  ...createSessionSlice(...a),
  ...createAnalyticsSlice(...a),
  ...createUploadSlice(...a),
  ...createSelectionSlice(...a),
  ...createProficiencySlice(...a),
}));

export const useBoundStore = <T,>(selector: (state: BoundState) => T) =>
  useStore(boundStore, selector);

export const useSessionStore = () => useBoundStore((state) => ({
  sessionId: state.sessionId,
  setSessionId: state.setSessionId,
}));

export const useAnalyticsStore = () => useBoundStore((state) => ({
  analyticsCache: state.analyticsCache,
  setAnalytics: state.setAnalytics,
}));

export const useUploadStore = () =>
  useBoundStore((state) => ({
    uploadedFiles: state.uploadedFiles,
    setUploadedFiles: state.setUploadedFiles,
  }));

export const useSelectionStore = () =>
  useBoundStore((state) => ({
    selectedThreats: state.selectedThreats,
    setSelectedThreats: state.setSelectedThreats,
    selectedRange: state.selectedRange,
    setSelectedRange: state.setSelectedRange,
  }));

export const useProficiencyStore = () =>
  useBoundStore((state) => ({
    metrics: state.metrics,
    level: state.level,
    setLevel: state.setLevel,
    logFeatureUsage: state.logFeatureUsage,
    logDwellTime: state.logDwellTime,
    logError: state.logError,
  }));
