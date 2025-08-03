import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useRealTimeAnalytics } from '../hooks/useRealTimeAnalytics';
import { AccessibleVisualization } from '../components/accessibility';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300'];

const RealTimeAnalyticsPage: React.FC = () => {
  const { data } = useRealTimeAnalytics();

  if (!data) {
    return <div>Waiting for analytics...</div>;
  }

  const topUsers = Array.isArray(data.top_users) ? data.top_users : [];
  const topDoors = Array.isArray(data.top_doors) ? data.top_doors : [];
  const patterns = data.access_patterns
    ? Object.entries(data.access_patterns).map(([pattern, count]) => ({
        pattern,
        count: Number(count),
      }))
    : [];

  return (
    <div className="p-3">
      <h2 className="mb-3">Real-Time Analytics</h2>
      <div className="mb-4 space-y-1">
        <div>Total Events: {data.total_events ?? 0}</div>
        <div>
          Active Users:{' '}
          {data.active_users ?? data.unique_users ?? topUsers.length}
        </div>
        <div>
          Active Doors:{' '}
          {data.active_doors ?? data.unique_doors ?? topDoors.length}
        </div>
      </div>

      {topUsers.length > 0 && (
        <AccessibleVisualization
          title="Top Users"
          summary={`Top users chart with ${topUsers.length} entries.`}
          tableData={{
            headers: ['User ID', 'Count'],
            rows: topUsers.slice(0, 10).map((u) => [u.user_id, u.count]),
          }}
        >
          <div className="mb-4" style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={topUsers.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="user_id" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </AccessibleVisualization>
      )}

      {topDoors.length > 0 && (
        <AccessibleVisualization
          title="Top Doors"
          summary={`Top doors chart with ${topDoors.length} entries.`}
          tableData={{
            headers: ['Door ID', 'Count'],
            rows: topDoors.slice(0, 10).map((d) => [d.door_id, d.count]),
          }}
        >
          <div className="mb-4" style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <BarChart data={topDoors.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="door_id" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </AccessibleVisualization>
      )}

      {patterns.length > 0 && (
        <AccessibleVisualization
          title="Access Patterns"
          summary={`Access patterns chart with ${patterns.length} entries.`}
          tableData={{
            headers: ['Pattern', 'Count'],
            rows: patterns.map((p) => [p.pattern, p.count]),
          }}
        >
          <div className="mb-4" style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={patterns} dataKey="count" nameKey="pattern" label>
                  {patterns.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </AccessibleVisualization>
      )}
    </div>
  );
};

const RealTimeAnalyticsWrapper: React.FC = () => (
  <ErrorBoundary>
    <RealTimeAnalyticsPage />
  </ErrorBoundary>
);

export default RealTimeAnalyticsWrapper;
