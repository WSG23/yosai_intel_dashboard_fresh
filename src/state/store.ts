import { create } from 'zustand';
import { createSessionSlice, SessionSlice } from './sessionSlice';
import { createAnalyticsSlice, AnalyticsSlice } from './analyticsSlice';

export type BoundState = SessionSlice & AnalyticsSlice;

export const useBoundStore = create<BoundState>()((...a) => ({
  ...createSessionSlice(...a),
  ...createAnalyticsSlice(...a),
}));

export const useSessionStore = () => useBoundStore((state) => ({
  sessionId: state.sessionId,
  setSessionId: state.setSessionId,
}));

export const useAnalyticsStore = () => useBoundStore((state) => ({
  analyticsCache: state.analyticsCache,
  setAnalytics: state.setAnalytics,
}));
