export interface UserCount {
  user_id: string;
  count: number;
}

export interface DoorCount {
  door_id: string;
  count: number;
}

export interface PatternCount {
  pattern: string;
  count: number;
}

export interface RealTimeAnalyticsPayload {
  total_events?: number;
  active_users?: number;
  unique_users?: number;
  active_doors?: number;
  unique_doors?: number;
  top_users?: UserCount[];
  top_doors?: DoorCount[];
  access_patterns?: PatternCount[];
  [key: string]: unknown;
}

