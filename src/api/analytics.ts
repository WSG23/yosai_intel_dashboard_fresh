import { api } from './client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export interface AnalyticsSummary {
  total_events: number;
  unique_users: number;
  unique_doors: number;
  success_rate: number;
  analysis_focus?: string;
  data_summary?: {
    total_records: number;
    date_range?: {
      start: string;
      end: string;
    };
  };
  patterns?: {
    power_users: string[];
    high_traffic_doors: string[];
    peak_hours: number[];
  };
}

export interface DataSource {
  label: string;
  value: string;
  type: 'upload' | 'service';
  available: boolean;
  metadata?: {
    filename?: string;
    exists?: boolean;
    rows?: number;
    columns?: number;
  };
}

export interface PatternAnalysis {
  status: string;
  data_summary: {
    total_records: number;
    unique_users: number;
    unique_devices: number;
    date_span_days: number;
  };
  user_patterns: {
    power_users: string[];
    regular_users: string[];
    occasional_users: string[];
  };
  device_patterns: {
    high_traffic: string[];
    moderate_traffic: string[];
    low_traffic: string[];
  };
  temporal_patterns?: {
    peak_hours: number[];
    peak_days: string[];
  };
}

export interface AnalysisRequest {
  data_source: string;
  analysis_type: 'summary' | 'security' | 'trends' | 'behavior' | 'anomaly' | 'ai_suggest' | 'quality';
  date_range?: {
    start: string;
    end: string;
  };
  filters?: Record<string, any>;
}

export const analyticsAPI = {
  async getSummary(dataSource: string = 'uploaded'): Promise<AnalyticsSummary> {
    return api.get<AnalyticsSummary>('/analytics/summary', {
      params: { data_source: dataSource },
    });
  },

  async getDataSources(): Promise<DataSource[]> {
    const response = await api.get<{ sources: DataSource[] }>('/analytics/sources');
    return response.sources;
  },

  async getPatterns(dataSource?: string, forceRefresh = false): Promise<PatternAnalysis> {
    return api.get<PatternAnalysis>('/analytics/patterns', {
      params: { data_source: dataSource, force_refresh: forceRefresh },
    });
  },

  async analyze(request: AnalysisRequest): Promise<any> {
    return api.post('/analytics/analyze', request);
  },

  async exportData(format: 'csv' | 'excel' | 'json', dataSource?: string): Promise<Blob> {
    const response = await api.get('/analytics/export', {
      params: { format, data_source: dataSource },
      responseType: 'blob',
    });
    return response as unknown as Blob;
  },

  async getRealtimeMetrics(): Promise<any> {
    return api.get('/analytics/realtime');
  },

  async getHistoricalData(metric: string, timeRange: string, granularity: 'hour' | 'day' | 'week' | 'month'): Promise<any> {
    return api.get('/analytics/historical', {
      params: { metric, time_range: timeRange, granularity },
    });
  },
};

export const useAnalyticsSummary = (dataSource: string) =>
  useQuery({
    queryKey: ['analytics', 'summary', dataSource],
    queryFn: () => analyticsAPI.getSummary(dataSource),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

export const useDataSources = () =>
  useQuery({
    queryKey: ['analytics', 'sources'],
    queryFn: analyticsAPI.getDataSources,
    staleTime: 30 * 60 * 1000,
  });

export const usePatternAnalysis = (dataSource?: string) =>
  useQuery({
    queryKey: ['analytics', 'patterns', dataSource],
    queryFn: () => analyticsAPI.getPatterns(dataSource),
    enabled: !!dataSource,
  });

export const useAnalyze = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: analyticsAPI.analyze,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });
};
