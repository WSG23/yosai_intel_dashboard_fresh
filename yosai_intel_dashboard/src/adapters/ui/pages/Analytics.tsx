import React, { useState, Suspense } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { Download, AlertCircle } from 'lucide-react';
import { ChunkGroup } from '../components/layout';
import ProgressiveSection from '../components/ProgressiveSection';
const RiskDashboard = React.lazy(
  () => import('../components/security/RiskDashboard'),
);
import {
  HoverPreview,
  ClickExpand,
} from '../components/interaction/ContextDisclosure';
import './Analytics.css';
import useAnalyticsData from '../hooks/useAnalyticsData';

const Analytics: React.FC = () => {
  const [sourceType, setSourceType] = useState('all');
  const { data: analyticsData, loading, error, refresh } = useAnalyticsData(sourceType);
  const [alertsEnabled, setAlertsEnabled] = useState(false);

  const riskData = {
    score: 72,
    history: [55, 60, 58, 65, 70, 72],
    factors: [
      { name: 'Malware', value: 80, benchmark: 60 },
      { name: 'Phishing', value: 65, benchmark: 50 },
      { name: 'Vulnerabilities', value: 55, benchmark: 45 },
    ],
  };

  const handleExport = () => {
    if (!analyticsData) return;

    const csvContent = [
      ['Pattern', 'Count', 'Percentage'],
      ...analyticsData.patterns.map((p) => [
        p.pattern,
        p.count,
        `${p.percentage}%`,
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

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
          <button onClick={refresh} className="retry-button">
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
        <ChunkGroup className="header-actions">
          <select
            aria-label="Select data source"
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="source-select"
          >
            <option value="all">All Sources</option>
            <option value="firewall">Firewall</option>
            <option value="endpoint">Endpoint</option>
            <option value="network">Network</option>
          </select>
          <button
            aria-label="Export analytics as CSV"
            onClick={handleExport}
            className="export-button"
          >
            <Download size={20} />
            Export CSV
          </button>
        </ChunkGroup>
      </div>

      <HoverPreview preview={<div>Risk dashboard preview</div>}>
        <Suspense fallback={<div>Loading risk dashboard...</div>}>
          <RiskDashboard
            score={riskData.score}
            history={riskData.history}
            factors={riskData.factors}
          />
        </Suspense>
      </HoverPreview>

      {analyticsData && (
        <ClickExpand
          preview={
            <div className="analytics-preview">Click to view analytics</div>
          }
        >
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Records</h3>
              <p className="stat-value">
                {analyticsData.total_records.toLocaleString()}
              </p>
            </div>
            <div className="stat-card">
              <h3>Unique Devices</h3>
              <p className="stat-value">{analyticsData.unique_devices}</p>
            </div>
            <div className="stat-card">
              <h3>Date Range</h3>
              <p className="stat-value">
                {new Date(analyticsData.date_range.start).toLocaleDateString()}{' '}
                -{new Date(analyticsData.date_range.end).toLocaleDateString()}
              </p>
            </div>
          </div>

          <ProgressiveSection
            title="Drill-down Metrics"
            id="drilldown-metrics"
            className="analytics-sections"
          >
            <section className="patterns-section">
              <h2>Top Security Patterns</h2>
              <ChunkGroup className="patterns-list" limit={9}>
                {analyticsData.patterns.map((pattern) => (
                  <div key={pattern.pattern} className="pattern-item">
                    <div className="pattern-info">
                      <span className="pattern-name">{pattern.pattern}</span>
                      <span className="pattern-count">
                        {pattern.count} occurrences
                      </span>
                    </div>
                    <div className="pattern-bar">
                      <div
                        className="pattern-bar-fill"
                        style={{ width: `${pattern.percentage}%` }}
                      />
                      <span className="pattern-percentage">
                        {pattern.percentage}%
                      </span>
                    </div>
                  </div>
                ))}
              </ChunkGroup>
            </section>

            <section className="devices-section">
              <h2>Device Distribution</h2>
              <ChunkGroup className="device-grid" limit={9}>
                {analyticsData.device_distribution.map((device) => (
                  <div key={device.device} className="device-card">
                    <span className="device-name">{device.device}</span>
                    <span className="device-count">{device.count}</span>
                  </div>
                ))}
              </ChunkGroup>
            </section>
          </ProgressiveSection>
          <ProgressiveSection
            title="Advanced Settings"
            id="analytics-advanced-settings"
            className="analytics-sections mt-4"
          >
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={alertsEnabled}
                onChange={(e) => setAlertsEnabled(e.target.checked)}
              />
              <span>Enable anomaly alerts</span>
            </label>
            {alertsEnabled && (
              <div className="text-sm mt-2">
                Anomaly alerts are enabled
              </div>
            )}
          </ProgressiveSection>
        </ClickExpand>
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
