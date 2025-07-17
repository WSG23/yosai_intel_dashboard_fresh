/**
 * Graphs Page Component
 * Interactive charts and visualizations using data from Python backend
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, RefreshCw, AlertCircle, BarChart3, TrendingUp, Users, Monitor } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Types
interface ChartData {
  type: string;
  data: any;
  error?: string;
}

interface DataSource {
  value: string;
  label: string;
}

interface AvailableChart {
  type: string;
  name: string;
  description: string;
}

// Chart color palette
const CHART_COLORS = [
  '#3B82F6', // blue
  '#10B981', // green
  '#F59E0B', // orange
  '#EF4444', // red
  '#8B5CF6', // purple
  '#06B6D4', // cyan
  '#84CC16', // lime
  '#F97316', // amber
];

// API Functions
const graphsAPI = {
  async getChartData(chartType: string, dataSource?: string): Promise<ChartData> {
    const url = dataSource 
      ? `/api/v1/graphs/chart/${chartType}?data_source=${encodeURIComponent(dataSource)}`
      : `/api/v1/graphs/chart/${chartType}`;
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async getAvailableCharts(): Promise<{ charts: AvailableChart[] }> {
    const response = await fetch('/api/v1/graphs/available-charts');
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
  }
};

// Chart Components
const PatternsChart: React.FC<{ data: ChartData }> = ({ data }) => {
  if (data.error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-800">{data.error}</AlertDescription>
      </Alert>
    );
  }

  const { users, devices, summary } = data.data;
  
  // Prepare data for user patterns chart
  const userPatternData = [
    { name: 'Power Users', count: users.power_users?.length || 0 },
    { name: 'Regular Users', count: users.regular_users?.length || 0 },
    { name: 'Occasional Users', count: users.occasional_users?.length || 0 }
  ];

  // Prepare data for device patterns chart
  const devicePatternData = [
    { name: 'High Traffic', count: devices.high_traffic_devices?.length || 0 },
    { name: 'Moderate Traffic', count: devices.moderate_traffic_devices?.length || 0 },
    { name: 'Low Traffic', count: devices.low_traffic_devices?.length || 0 }
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>User Activity Patterns</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={userPatternData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill={CHART_COLORS[0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Device Usage Patterns</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={devicePatternData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {devicePatternData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
};

const TimelineChart: React.FC<{ data: ChartData }> = ({ data }) => {
  if (data.error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-800">{data.error}</AlertDescription>
      </Alert>
    );
  }

  const { hourly, daily, peak_hours } = data.data;
  
  // Prepare hourly distribution data
  const hourlyData = Object.entries(hourly || {}).map(([hour, count]) => ({
    hour: `${hour}:00`,
    count: count as number
  })).sort((a, b) => parseInt(a.hour) - parseInt(b.hour));

  // Prepare daily data (if available)
  const dailyData = daily ? daily.map((day: string, index: number) => ({
    day,
    activity: index + 1 // Placeholder activity level
  })) : [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Hourly Activity Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke={CHART_COLORS[1]} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {dailyData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Peak Days Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dailyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="activity" fill={CHART_COLORS[2]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

const UserActivityChart: React.FC<{ data: ChartData }> = ({ data }) => {
  if (data.error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-800">{data.error}</AlertDescription>
      </Alert>
    );
  }

  const { power_users, regular_users, occasional_users } = data.data;
  
  // Create activity distribution data
  const activityData = [
    { category: 'Power Users', count: power_users?.length || 0, color: CHART_COLORS[0] },
    { category: 'Regular Users', count: regular_users?.length || 0, color: CHART_COLORS[1] },
    { category: 'Occasional Users', count: occasional_users?.length || 0, color: CHART_COLORS[2] }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Activity Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={activityData} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="category" type="category" />
            <Tooltip />
            <Bar dataKey="count" fill={CHART_COLORS[0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

const DeviceUsageChart: React.FC<{ data: ChartData }> = ({ data }) => {
  if (data.error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-800">{data.error}</AlertDescription>
      </Alert>
    );
  }

  const { high_traffic, moderate_traffic, low_traffic } = data.data;
  
  // Create device usage data
  const deviceData = [
    { name: 'High Traffic', value: high_traffic?.length || 0 },
    { name: 'Moderate Traffic', value: moderate_traffic?.length || 0 },
    { name: 'Low Traffic', value: low_traffic?.length || 0 }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Device Usage Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={deviceData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent, value }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
              outerRadius={120}
              fill="#8884d8"
              dataKey="value"
            >
              {deviceData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Main Component
const GraphsPage: React.FC = () => {
  const [chartData, setChartData] = useState<Record<string, ChartData>>({});
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [availableCharts, setAvailableCharts] = useState<AvailableChart[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [activeTab, setActiveTab] = useState<string>('patterns');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [chartsResponse, sourcesResponse] = await Promise.all([
          graphsAPI.getAvailableCharts(),
          graphsAPI.getDataSources()
        ]);
        
        setAvailableCharts(chartsResponse.charts);
        setDataSources(sourcesResponse.sources);
      } catch (err) {
        console.error('Failed to load initial data:', err);
        setError('Failed to load initial data');
      }
    };

    loadInitialData();
  }, []);

  // Load chart data
  const loadChartData = useCallback(async (chartType: string, dataSource?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await graphsAPI.getChartData(chartType, dataSource);
      setChartData(prev => ({
        ...prev,
        [chartType]: data
      }));
    } catch (err) {
      console.error(`Failed to load ${chartType} chart:`, err);
      setChartData(prev => ({
        ...prev,
        [chartType]: { type: chartType, data: null, error: `Failed to load ${chartType} chart` }
      }));
    } finally {
      setLoading(false);
    }
  }, []);

  // Load data when source changes or tab changes
  useEffect(() => {
    if (activeTab) {
      loadChartData(activeTab, selectedSource || undefined);
    }
  }, [activeTab, selectedSource, loadChartData]);

  const handleRefresh = () => {
    if (activeTab) {
      loadChartData(activeTab, selectedSource || undefined);
    }
  };

  const handleSourceChange = (value: string) => {
    setSelectedSource(value);
  };

  const handleTabChange = (value: string) => {
    setActiveTab(value);
  };

  const renderChart = (chartType: string) => {
    const data = chartData[chartType];
    
    if (!data) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading chart data...</span>
        </div>
      );
    }

    switch (chartType) {
      case 'patterns':
        return <PatternsChart data={data} />;
      case 'timeline':
        return <TimelineChart data={data} />;
      case 'user_activity':
        return <UserActivityChart data={data} />;
      case 'device_usage':
        return <DeviceUsageChart data={data} />;
      default:
        return (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>Unknown chart type: {chartType}</AlertDescription>
          </Alert>
        );
    }
  };

  const getTabIcon = (chartType: string) => {
    switch (chartType) {
      case 'patterns':
        return <BarChart3 className="h-4 w-4" />;
      case 'timeline':
        return <TrendingUp className="h-4 w-4" />;
      case 'user_activity':
        return <Users className="h-4 w-4" />;
      case 'device_usage':
        return <Monitor className="h-4 w-4" />;
      default:
        return <BarChart3 className="h-4 w-4" />;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Graphs & Visualizations</h1>
          <p className="text-gray-600 mt-1">
            Interactive charts and data visualizations
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

      {/* Error State */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Charts Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          {availableCharts.map((chart) => (
            <TabsTrigger key={chart.type} value={chart.type} className="flex items-center space-x-2">
              {getTabIcon(chart.type)}
              <span className="hidden sm:inline">{chart.name}</span>
            </TabsTrigger>
          ))}
        </TabsList>
        
        {availableCharts.map((chart) => (
          <TabsContent key={chart.type} value={chart.type} className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  {getTabIcon(chart.type)}
                  <span>{chart.name}</span>
                </CardTitle>
                <p className="text-sm text-gray-600">{chart.description}</p>
              </CardHeader>
              <CardContent>
                {renderChart(chart.type)}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      {/* No Data State */}
      {!availableCharts.length && !loading && !error && (
        <Card>
          <CardContent className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Charts Available</h3>
            <p className="text-gray-600">
              Upload some data files to see interactive charts and visualizations.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default GraphsPage;

