import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface AnalyticsData {
  total_records: number;
  unique_devices: number;
  date_range: { start: string; end: string };
  patterns: Array<{ pattern: string; count: number; percentage: number }>;
  device_distribution: Array<{ device: string; count: number }>;
}

export interface AnalyticsState {
  analyticsCache: Record<string, AnalyticsData>;
}

const initialState: AnalyticsState = {
  analyticsCache: {},
};

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    setAnalytics(
      state,
      action: PayloadAction<{ key: string; data: AnalyticsData }>,
    ) {
      const { key, data } = action.payload;
      state.analyticsCache[key] = data;
    },
  },
});

export const { setAnalytics } = analyticsSlice.actions;
export default analyticsSlice.reducer;
