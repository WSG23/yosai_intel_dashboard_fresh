import { createStore } from 'zustand';
import { useStore } from 'zustand';
import { createSessionSlice, SessionSlice } from './sessionSlice';
import { createAnalyticsSlice, AnalyticsSlice } from './analyticsSlice';
import { createUploadSlice, UploadSlice } from './uploadSlice';

export type BoundState = SessionSlice & AnalyticsSlice & UploadSlice;

export const boundStore = createStore<BoundState>()((...a) => ({
  ...createSessionSlice(...a),
  ...createAnalyticsSlice(...a),
  ...createUploadSlice(...a),
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
