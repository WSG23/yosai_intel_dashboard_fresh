import { createStore } from 'zustand';
import { useStore } from 'zustand';
import { createSessionSlice, SessionSlice } from './sessionSlice';
import { createAnalyticsSlice, AnalyticsSlice } from './analyticsSlice';

export type BoundState = SessionSlice & AnalyticsSlice;

export const boundStore = createStore<BoundState>()((...a) => ({
  ...createSessionSlice(...a),
  ...createAnalyticsSlice(...a),
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
