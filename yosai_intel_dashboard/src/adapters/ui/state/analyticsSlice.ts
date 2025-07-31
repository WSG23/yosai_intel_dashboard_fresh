import { StateCreator } from 'zustand';

export interface AnalyticsData {
  total_records: number;
  unique_devices: number;
  date_range: { start: string; end: string };
  patterns: Array<{ pattern: string; count: number; percentage: number }>;
  device_distribution: Array<{ device: string; count: number }>;
}

export interface AnalyticsSlice {
  analyticsCache: Record<string, AnalyticsData>;
  setAnalytics: (key: string, data: AnalyticsData) => void;
}

export const createAnalyticsSlice: StateCreator<AnalyticsSlice, [], [], AnalyticsSlice> = (set) => ({
  analyticsCache: {},
  setAnalytics: (key: string, data: AnalyticsData) =>
    set((state) => ({ analyticsCache: { ...state.analyticsCache, [key]: data } })),
});
