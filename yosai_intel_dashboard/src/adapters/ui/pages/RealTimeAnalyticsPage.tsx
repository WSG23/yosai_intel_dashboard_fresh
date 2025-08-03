import React, { useState } from 'react';
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
  Brush,
} from 'recharts';
import { useRealTimeAnalytics } from '../hooks/useRealTimeAnalytics';
import { useSelection } from '../core/interaction/SelectionContext';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300'];

const RealTimeAnalyticsPage: React.FC = () => {
  const { data } = useRealTimeAnalytics();
  const { selections, select } = useSelection();

  if (!data) {
    return <div>Waiting for analytics...</div>;
  }

  const topUsers = Array.isArray(data.top_users) ? data.top_users : [];
  const topDoors = Array.isArray(data.top_doors) ? data.top_doors : [];
  const filteredTopUsers = selections.door
    ? topUsers.filter((u: any) => (u as any).door_id === selections.door)
    : topUsers;
  const filteredTopDoors = selections.user
    ? topDoors.filter((d: any) => (d as any).user_id === selections.user)
    : topDoors;
  const [userRange, setUserRange] = useState({ startIndex: 0, endIndex: 9 });
  const [doorRange, setDoorRange] = useState({ startIndex: 0, endIndex: 9 });
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

      {filteredTopUsers.length > 0 && (
        <div className="mb-4" style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={filteredTopUsers.slice(userRange.startIndex, userRange.endIndex + 1)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="user_id" />
              <YAxis />
              <Tooltip />
              <Brush
                dataKey="user_id"
                height={20}
                stroke="#8884d8"
                startIndex={userRange.startIndex}
                endIndex={userRange.endIndex}
                onChange={(range) => setUserRange(range as any)}
              />
              <Bar
                dataKey="count"
                fill="#8884d8"
                onClick={(data: any) => select('user', data.user_id)}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {filteredTopDoors.length > 0 && (
        <div className="mb-4" style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={filteredTopDoors.slice(doorRange.startIndex, doorRange.endIndex + 1)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="door_id" />
              <YAxis />
              <Tooltip />
              <Brush
                dataKey="door_id"
                height={20}
                stroke="#82ca9d"
                startIndex={doorRange.startIndex}
                endIndex={doorRange.endIndex}
                onChange={(range) => setDoorRange(range as any)}
              />
              <Bar
                dataKey="count"
                fill="#82ca9d"
                onClick={(data: any) => select('door', data.door_id)}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {patterns.length > 0 && (
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
