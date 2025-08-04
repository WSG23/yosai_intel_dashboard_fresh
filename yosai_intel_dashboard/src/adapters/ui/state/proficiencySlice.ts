import { StateCreator } from 'zustand';

export interface ProficiencyMetrics {
  featureUsage: Record<string, number>;
  dwellTime: Record<string, number>;
  errors: Array<{ feature: string; error: string }>;
}

export interface ProficiencySlice {
  metrics: ProficiencyMetrics;
  level: number;
  setLevel: (lvl: number) => void;
  logFeatureUsage: (feature: string) => void;
  logDwellTime: (feature: string, ms: number) => void;
  logError: (feature: string, error: string) => void;
}

const computeLevel = (metrics: ProficiencyMetrics): number => {
  const usage = Object.values(metrics.featureUsage).reduce((a, b) => a + b, 0);
  const dwell = Object.values(metrics.dwellTime).reduce((a, b) => a + b, 0) / 1000;
  const penalty = metrics.errors.length;
  const score = usage + dwell - penalty;
  if (score > 50) return 4;
  if (score > 30) return 3;
  if (score > 15) return 2;
  if (score > 5) return 1;
  return 0;
};

export const createProficiencySlice: StateCreator<ProficiencySlice, [], [], ProficiencySlice> = (set) => ({
  metrics: { featureUsage: {}, dwellTime: {}, errors: [] },
  level: 0,
  setLevel: (lvl: number) => set({ level: Math.max(0, Math.min(4, lvl)) }),
  logFeatureUsage: (feature: string) =>
    set((state) => {
      const featureUsage = {
        ...state.metrics.featureUsage,
        [feature]: (state.metrics.featureUsage[feature] || 0) + 1,
      };
      const metrics = { ...state.metrics, featureUsage };
      return { metrics, level: computeLevel(metrics) };
    }),
  logDwellTime: (feature: string, ms: number) =>
    set((state) => {
      const dwellTime = {
        ...state.metrics.dwellTime,
        [feature]: (state.metrics.dwellTime[feature] || 0) + ms,
      };
      const metrics = { ...state.metrics, dwellTime };
      return { metrics, level: computeLevel(metrics) };
    }),
  logError: (feature: string, error: string) =>
    set((state) => {
      const metrics = {
        ...state.metrics,
        errors: [...state.metrics.errors, { feature, error }],
      };
      return { metrics, level: computeLevel(metrics) };
    }),
});

