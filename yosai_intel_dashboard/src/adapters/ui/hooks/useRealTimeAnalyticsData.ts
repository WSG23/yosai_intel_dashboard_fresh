export interface RealTimeAnalyticsEvent {
  total_events?: number;
  active_users?: number;
  unique_users?: number;
  active_doors?: number;
  unique_doors?: number;
  top_users?: {
    user_id: string;
    count: number;
  }[];
  top_doors?: {
    door_id: string;
    count: number;
  }[];
  access_patterns?: Record<string, number>;
  [key: string]: any;
}

