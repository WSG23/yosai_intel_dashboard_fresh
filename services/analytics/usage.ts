import { eventBus, Listener } from '../../yosai_intel_dashboard/src/adapters/ui/eventBus';

export interface UsageSnapshot {
  adoption: Record<string, number>;
  errors: Record<string, number>;
  proficiency: Record<string, number>;
}

const adoptionCounts: Record<string, number> = {};
const errorCounts: Record<string, number> = {};
const proficiencyLevels: Record<string, number> = {};

export const snapshot = (): UsageSnapshot => ({
  adoption: { ...adoptionCounts },
  errors: { ...errorCounts },
  proficiency: { ...proficiencyLevels },
});

const publish = () => {
  eventBus.emit('usage_update', snapshot());
};

export const recordAdoption = (feature: string): void => {
  adoptionCounts[feature] = (adoptionCounts[feature] || 0) + 1;
  publish();
};

export const recordError = (feature: string): void => {
  errorCounts[feature] = (errorCounts[feature] || 0) + 1;
  publish();
};

export const recordProficiency = (userId: string, level: number): void => {
  proficiencyLevels[userId] = level;
  publish();
};

export const onUsageUpdate = (listener: Listener<UsageSnapshot>): (() => void) =>
  eventBus.on('usage_update', listener);

const usageMetrics = {
  recordAdoption,
  recordError,
  recordProficiency,
  snapshot,
  onUsageUpdate,
};

export default usageMetrics;
