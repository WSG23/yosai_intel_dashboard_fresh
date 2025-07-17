export interface AnalyticsResponse {
  status: string;
  data_summary: {
    total_records: number;
    unique_users: number;
    unique_devices: number;
    date_range: {
      start: string;
      end: string;
      span_days: number;
    };
  };
  user_patterns: {
    power_users: string[];
    regular_users: string[];
    occasional_users: string[];
  };
  // ... other fields
}

export interface ChartData {
  type: string;
  data: any;
  error?: string;
}

export interface ExportFormat {
  type: string;
  name: string;
  description: string;
  mimeType: string;
  extension: string;
}
