import React, { useState, useEffect } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { useAnalyticsStore } from '../state/store';
import { BarChart3, Filter, Download, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import './Analytics.css';

interface AnalyticsData {
  total_records: number;
  unique_devices: number;
  date_range: {
    start: string;
    end: string;
  };
  patterns: Array<{
    pattern: string;
    count: number;
    percentage: number;
  }>;
  device_distribution: Array<{
    device: string;
    count: number;
  }>;
}

const Analytics: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { analyticsCache, setAnalytics } = useAnalyticsStore();
  const [sourceType, setSourceType] = useState('all');
  const analyticsData = analyticsCache[sourceType] || null;

  useEffect(() => {
    if (analyticsData) {
      setLoading(false);
      return;
    }
    fetchAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceType]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.get<AnalyticsData>(`/analytics/${sourceType}`);
      setAnalytics(sourceType, data);
    } catch (err) {
      console.error('Analytics fetch error:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!analyticsData) return;
    
    const csvContent = [
      ['Pattern', 'Count', 'Percentage'],
      ...analyticsData.patterns.map(p => [p.pattern, p.count, `${p.percentage}%`])
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics_${sourceType}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="analytics-container">
        <div className="loading-spinner">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-container">
        <div className="error-message">
          <AlertCircle size={24} />
          <span>{error}</span>
          <button onClick={fetchAnalytics} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h1>Security Analytics</h1>
        <div className="header-actions">
          <select 
            value={sourceType} 
            onChange={(e) => setSourceType(e.target.value)}
            className="source-select"
          >
            <option value="all">All Sources</option>
            <option value="firewall">Firewall</option>
            <option value="endpoint">Endpoint</option>
            <option value="network">Network</option>
          </select>
          <button onClick={handleExport} className="export-button">
            <Download size={20} />
            Export CSV
          </button>
        </div>
      </div>

      {analyticsData && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Records</h3>
              <p className="stat-value">{analyticsData.total_records.toLocaleString()}</p>
            </div>
            <div className="stat-card">
              <h3>Unique Devices</h3>
              <p className="stat-value">{analyticsData.unique_devices}</p>
            </div>
            <div className="stat-card">
              <h3>Date Range</h3>
              <p className="stat-value">
                {new Date(analyticsData.date_range.start).toLocaleDateString()} - 
                {new Date(analyticsData.date_range.end).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="analytics-sections">
            <section className="patterns-section">
              <h2>Top Security Patterns</h2>
              <div className="patterns-list">
                {analyticsData.patterns.map((pattern, index) => (
                  <div key={index} className="pattern-item">
                    <div className="pattern-info">
                      <span className="pattern-name">{pattern.pattern}</span>
                      <span className="pattern-count">{pattern.count} occurrences</span>
                    </div>
                    <div className="pattern-bar">
                      <div 
                        className="pattern-bar-fill"
                        style={{ width: `${pattern.percentage}%` }}
                      />
                      <span className="pattern-percentage">{pattern.percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="devices-section">
              <h2>Device Distribution</h2>
              <div className="device-grid">
                {analyticsData.device_distribution.map((device, index) => (
                  <div key={index} className="device-card">
                    <span className="device-name">{device.device}</span>
                    <span className="device-count">{device.count}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
};

const AnalyticsPage: React.FC = () => (
  <ErrorBoundary>
    <Analytics />
  </ErrorBoundary>
);

export default AnalyticsPage;
