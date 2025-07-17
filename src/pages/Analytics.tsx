/**
 * Analytics Page Component
 * Displays analytics data from Python AnalyticsService
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Loader2, RefreshCw, AlertCircle, TrendingUp, Users, Activity, Shield } from 'lucide-react';

// Types
interface DataSource {
  value: string;
  label: string;
}

interface AnalyticsSummary {
  total_records: number;
  unique_users: number;
  unique_devices: number;
  date_range: {
    start: string;
    end: string;
    span_days: number;
  };
}

interface UserPatterns {
  power_users: string[];
  regular_users: string[];
  occasional_users: string[];
}

interface DevicePatterns {
  high_traffic_devices: string[];
  moderate_traffic_devices: string[];
  low_traffic_devices: string[];
}

interface AnalyticsData {
  status: string;
  data_summary: AnalyticsSummary;
  user_patterns: UserPatterns;
  device_patterns: DevicePatterns;
  interaction_patterns: {
    total_unique_interactions: number;
  };
  temporal_patterns: {
    peak_hours: string[];
    peak_days: string[];
    hourly_distribution: Record<string, number>;
  };
  access_patterns: {
    overall_success_rate: number;
    users_with_low_success: number;
    devices_with_low_success: number;
  };
  recommendations: string[];
}

interface AnalyticsAPIResponse {
  status: string;
  data?: AnalyticsData;
  error?: string;
}

// API Functions
const analyticsAPI = {
  async getPatterns(dataSource?: string): Promise<AnalyticsAPIResponse> {
    const url = dataSource 
      ? `/api/v1/analytics/patterns?data_source=${encodeURIComponent(dataSource)}`
      : '/api/v1/analytics/patterns';
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async getDataSources(): Promise<{ sources: DataSource[] }> {
    const response = await fetch('/api/v1/analytics/sources');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async getHealth(): Promise<{ status: string; message?: string }> {
    const response = await fetch('/api/v1/analytics/health');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
};

// Components
const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'blue' | 'green' | 'orange' | 'red';
}> = ({ title, value, subtitle, icon, color = 'blue' }) => {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    orange: 'text-orange-600 bg-orange-50',
    red: 'text-red-600 bg-red-50'
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold">{typeof value === 'number' ? value.toLocaleString() : value}</p>
            {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const PatternsList: React.FC<{
  title: string;
  items: string[];
  badgeColor?: 'blue' | 'green' | 'orange';
}> = ({ title, items, badgeColor = 'blue' }) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800'
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {items.length > 0 ? (
            items.map((item, index) => (
              <Badge key={index} className={colorClasses[badgeColor]}>
                {item}
              </Badge>
            ))
          ) : (
            <p className="text-gray-500">No data available</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const AnalyticsPage: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Load data sources on component mount
  useEffect(() => {
    const loadDataSources = async () => {
      try {
        const { sources } = await analyticsAPI.getDataSources();
        setDataSources(sources);
      } catch (err) {
        console.error('Failed to load data sources:', err);
        setError('Failed to load data sources');
      }
    };

    loadDataSources();
  }, []);

  // Load analytics data
  const loadAnalyticsData = useCallback(async (dataSource?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await analyticsAPI.getPatterns(dataSource);
      
      if (response.status === 'success' && response.data) {
        setAnalyticsData(response.data);
        setLastUpdated(new Date());
      } else if (response.status === 'no_data') {
        setError('No data available for analysis');
        setAnalyticsData(null);
      } else {
        setError(response.error || 'Failed to load analytics data');
        setAnalyticsData(null);
      }
    } catch (err) {
      console.error('Analytics data loading failed:', err);
      setError('Failed to load analytics data');
      setAnalyticsData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load data on component mount and when source changes
  useEffect(() => {
    loadAnalyticsData(selectedSource || undefined);
  }, [selectedSource, loadAnalyticsData]);

  const handleRefresh = () => {
    loadAnalyticsData(selectedSource || undefined);
  };

  const handleSourceChange = (value: string) => {
    setSelectedSource(value);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Deep insights from your access control data
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Select value={selectedSource} onValueChange={handleSourceChange}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select data source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Sources</SelectItem>
              {dataSources.map((source) => (
                <SelectItem key={source.value} value={source.value}>
                  {source.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={handleRefresh}
            disabled={loading}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Last Updated */}
      {lastUpdated && (
        <p className="text-sm text-gray-500">
          Last updated: {lastUpdated.toLocaleString()}
        </p>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading analytics data...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Analytics Data */}
      {analyticsData && !loading && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total Records"
              value={analyticsData.data_summary.total_records}
              subtitle={`${analyticsData.data_summary.date_range.span_days} days`}
              icon={<Activity className="h-6 w-6" />}
              color="blue"
            />
            <StatCard
              title="Unique Users"
              value={analyticsData.data_summary.unique_users}
              subtitle="Active users"
              icon={<Users className="h-6 w-6" />}
              color="green"
            />
            <StatCard
              title="Unique Devices"
              value={analyticsData.data_summary.unique_devices}
              subtitle="Access points"
              icon={<Shield className="h-6 w-6" />}
              color="orange"
            />
            <StatCard
              title="Success Rate"
              value={`${(analyticsData.access_patterns.overall_success_rate * 100).toFixed(1)}%`}
              subtitle="Overall access success"
              icon={<TrendingUp className="h-6 w-6" />}
              color="green"
            />
          </div>

          {/* User Patterns */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <PatternsList
              title="Power Users"
              items={analyticsData.user_patterns.power_users}
              badgeColor="green"
            />
            <PatternsList
              title="Regular Users"
              items={analyticsData.user_patterns.regular_users}
              badgeColor="blue"
            />
            <PatternsList
              title="Occasional Users"
              items={analyticsData.user_patterns.occasional_users}
              badgeColor="orange"
            />
          </div>

          {/* Device Patterns */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <PatternsList
              title="High Traffic Devices"
              items={analyticsData.device_patterns.high_traffic_devices}
              badgeColor="green"
            />
            <PatternsList
              title="Moderate Traffic Devices"
              items={analyticsData.device_patterns.moderate_traffic_devices}
              badgeColor="blue"
            />
            <PatternsList
              title="Low Traffic Devices"
              items={analyticsData.device_patterns.low_traffic_devices}
              badgeColor="orange"
            />
          </div>

          {/* Temporal Patterns */}
          <Card>
            <CardHeader>
              <CardTitle>Temporal Patterns</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-2">Peak Hours</h4>
                  <div className="flex flex-wrap gap-2">
                    {analyticsData.temporal_patterns.peak_hours.map((hour, index) => (
                      <Badge key={index} className="bg-blue-100 text-blue-800">
                        {hour}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Peak Days</h4>
                  <div className="flex flex-wrap gap-2">
                    {analyticsData.temporal_patterns.peak_days.map((day, index) => (
                      <Badge key={index} className="bg-green-100 text-green-800">
                        {day}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          {analyticsData.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {analyticsData.recommendations.map((recommendation, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* No Data State */}
      {!analyticsData && !loading && !error && (
        <Card>
          <CardContent className="text-center py-12">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Analytics Data</h3>
            <p className="text-gray-600">
              Upload some data files to see analytics insights.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AnalyticsPage;

