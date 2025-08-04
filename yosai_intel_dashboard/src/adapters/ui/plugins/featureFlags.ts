export interface FeatureFlag {
  /** Whether the feature is globally enabled */
  enabled: boolean;
  /**
   * Percentage of users that should receive the feature. 0-100.
   * When omitted the feature is enabled for all users.
   */
  rollout?: number;
  /** Explicit allow list of user identifiers */
  users?: string[];
}

export type FeatureFlagConfig = Record<string, FeatureFlag>;

let flags: FeatureFlagConfig = {};

/**
 * Replace the current feature flag configuration. Typically loaded from the
 * server or some external data store.
 */
export const setFeatureFlags = (config: FeatureFlagConfig): void => {
  flags = config;
};

const hashUser = (user: string): number => {
  let hash = 0;
  for (let i = 0; i < user.length; i += 1) {
    hash = (hash << 5) - hash + user.charCodeAt(i);
    hash |= 0; // keep 32bit
  }
  return Math.abs(hash);
};

/**
 * Determine if a feature is enabled for a given user. Supports gradual
 * rollouts via percentage based evaluation and explicit user allow lists.
 */
export const isFeatureEnabled = (name: string, user: string): boolean => {
  const flag = flags[name];
  if (!flag || !flag.enabled) return false;
  if (flag.users && flag.users.includes(user)) return true;
  const rollout = flag.rollout ?? 100;
  return hashUser(user) % 100 < rollout;
};
