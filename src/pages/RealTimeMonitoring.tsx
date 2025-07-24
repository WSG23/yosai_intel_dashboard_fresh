import React, { useEffect, useState } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Activity, Users, DoorOpen, AlertCircle } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useEventStream } from '../hooks/useEventStream';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface AccessEvent {
  eventId: string;
  personName: string;
  doorName: string;
  timestamp: string;
  decision: 'GRANTED' | 'DENIED';
  processingTime: number;
}

interface Metrics {
  eventsPerSecond: number;
  averageLatency: number;
  activeUsers: number;
  anomaliesDetected: number;
}

const MetricCard: React.FC<{
  title: string;
  value: string;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'good' | 'warning' | 'alert' | 'stable';
}> = ({ title, value, icon: Icon, trend }) => {
  const trendColor =
    trend === 'up'
      ? 'text-green-600'
      : trend === 'down'
        ? 'text-red-600'
        : trend === 'alert'
          ? 'text-red-600'
          : trend === 'warning'
            ? 'text-yellow-600'
            : 'text-gray-600';
  return (
    <Card className="text-center p-4">
      <CardHeader>
        <Icon className="mx-auto mb-2" size={20} />
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <span className={`text-xl font-semibold ${trendColor}`}>{value}</span>
      </CardContent>
    </Card>
  );
};

const EventRow: React.FC<{ event: AccessEvent }> = ({ event }) => (
  <div className="flex items-center justify-between py-2 border-b text-sm">
    <span className="font-medium">{event.personName}</span>
    <span className="text-gray-500">{event.doorName}</span>
    <span className={event.decision === 'GRANTED' ? 'text-green-600' : 'text-red-600'}>
      {event.decision}
    </span>
    <span className="text-gray-400">
      {new Date(event.timestamp).toLocaleTimeString()}
    </span>
  </div>
);

export const RealTimeMonitoring: React.FC = () => {
  const [events, setEvents] = useState<AccessEvent[]>([]);
  const [metrics, setMetrics] = useState<Metrics>({
    eventsPerSecond: 0,
    averageLatency: 0,
    activeUsers: 0,
    anomaliesDetected: 0,
  });

  const { data: wsData, isConnected } = useWebSocket('/ws/events');
  const { data: sseData } = useEventStream('/events/stream', undefined, !isConnected);

  const activeData = isConnected ? wsData : sseData;

  useEffect(() => {
    if (activeData) {
      const event = JSON.parse(activeData) as AccessEvent;
      setEvents((prev) => [event, ...prev].slice(0, 100));
      updateMetrics(event);
    }
  }, [activeData]);

  const updateMetrics = (event: AccessEvent) => {
    setMetrics((prev) => ({
      ...prev,
      averageLatency: prev.averageLatency * 0.9 + event.processingTime * 0.1,
      eventsPerSecond: prev.eventsPerSecond + 1,
    }));
  };

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Events/Second"
          value={metrics.eventsPerSecond.toFixed(1)}
          icon={Activity}
          trend={metrics.eventsPerSecond > 100 ? 'up' : 'stable'}
        />
        <MetricCard
          title="Avg Latency"
          value={`${metrics.averageLatency.toFixed(1)}ms`}
          icon={Activity}
          trend={metrics.averageLatency < 100 ? 'good' : 'warning'}
        />
        <MetricCard
          title="Active Users"
          value={metrics.activeUsers.toString()}
          icon={Users}
        />
        <MetricCard
          title="Anomalies"
          value={metrics.anomaliesDetected.toString()}
          icon={AlertCircle}
          trend={metrics.anomaliesDetected > 0 ? 'alert' : 'good'}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Live Access Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-96 overflow-y-auto">
            {events.map((event) => (
              <EventRow key={event.eventId} event={event} />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const RealTimeMonitoringPage: React.FC = () => (
  <ErrorBoundary>
    <RealTimeMonitoring />
  </ErrorBoundary>
);

export default RealTimeMonitoringPage;
