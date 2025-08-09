import React, { useEffect, useRef, useState } from 'react';
import { FixedSizeList as List } from 'react-window';
import ErrorBoundary from '../components/ErrorBoundary';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Activity, Users, AlertCircle } from 'lucide-react';
import { useWebSocket } from '../hooks';
import { useEventStream } from '../hooks/useEventStream';
import useResponsiveChart from '../hooks/useResponsiveChart';
import { ChunkGroup } from '../components/layout';

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
      ? 'text-green-700'
      : trend === 'down'
        ? 'text-red-700'
        : trend === 'alert'
          ? 'text-white'
          : trend === 'warning'
            ? 'text-black'
            : 'text-gray-600';
  const cardStyle =
    trend === 'alert'
      ? 'bg-red-700 text-white'
      : trend === 'warning'
        ? 'bg-yellow-400 text-black'
        : '';
  return (
    <Card className={`text-center p-4 ${cardStyle}`}>
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

const EventRow: React.FC<{ event: AccessEvent; showDetails: boolean }> = ({
  event,
  showDetails,
}) => (
  <div className="flex items-center justify-between py-2 border-b text-sm">
    <span className="font-medium">{event.personName}</span>
    {showDetails && <span className="text-gray-500">{event.doorName}</span>}
    <span className={event.decision === 'GRANTED' ? 'text-green-700' : 'bg-red-700 text-white p-1 rounded'}>
      {event.decision}
    </span>
    {showDetails && (
      <span className="text-gray-400">
        {new Date(event.timestamp).toLocaleTimeString()}
      </span>
    )}
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

  const [paused, setPaused] = useState(false);
  const bufferRef = useRef<AccessEvent[]>([]);
  const [pending, setPending] = useState(0);
  const scheduler =
    (typeof window !== 'undefined' && (window as any).requestIdleCallback)
      ? (window as any).requestIdleCallback
      : (fn: Function) => setTimeout(fn, 0);

  const { isMobile } = useResponsiveChart();
  const listRef = useRef<HTMLDivElement | null>(null);
  const [listVisible, setListVisible] = useState(true);
  const [showDetails, setShowDetails] = useState(!isMobile);

  const filterOptions = ['ALL', 'GRANTED', 'DENIED'] as const;
  const [filter, setFilter] = useState<(typeof filterOptions)[number]>('ALL');
  const filterRefs = useRef<Array<HTMLButtonElement | null>>([]);

  
  useEffect(() => {
    if (activeData) {
      const event = JSON.parse(activeData) as AccessEvent;
      if (paused) {
        bufferRef.current.push(event);
        setPending(bufferRef.current.length);
      } else {
        setEvents((prev) => [event, ...prev].slice(0, 1000));
        updateMetrics(event);
      }
    }
  }, [activeData, paused]);


  const updateMetrics = (event: AccessEvent) => {
    setMetrics((prev) => ({
      ...prev,
      averageLatency: prev.averageLatency * 0.9 + event.processingTime * 0.1,
      eventsPerSecond: prev.eventsPerSecond + 1,
    }));
  };

  const processBuffered = () => {
    const next = bufferRef.current.shift();
    if (!next) {
      setPending(0);
      return;
    }
    setEvents((prev) => [next, ...prev].slice(0, 1000));
    updateMetrics(next);
    if (bufferRef.current.length > 0) {
      scheduler(processBuffered);
    } else {
      setPending(0);
    }
  };

  const resume = () => {
    setPaused(false);
    processBuffered();
  };

  const replay = () => processBuffered();

  useEffect(() => {
    if (!listRef.current) return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => setListVisible(entry.isIntersecting));
    });
    observer.observe(listRef.current);
    return () => observer.disconnect();
  }, []);

  const handleFilterKeyDown = (
    e: React.KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) => {
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const next = (index + 1) % filterOptions.length;
      filterRefs.current[next]?.focus();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prev = (index - 1 + filterOptions.length) % filterOptions.length;
      filterRefs.current[prev]?.focus();
    }
  };

  const filteredEvents = events.filter(
    (e) => filter === 'ALL' || e.decision === filter,
  );

  return (
    <div className="p-6 space-y-6">
      <ChunkGroup className="grid grid-cols-1 md:grid-cols-4 gap-4" limit={9}>
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
      </ChunkGroup>

      <Card>
        <CardHeader>
          <ChunkGroup className="flex items-center justify-between">
            <ChunkGroup className="flex items-center space-x-2">
              <CardTitle>Live Access Events</CardTitle>
              {!paused && (
                <Badge className="bg-green-700 text-white">Live</Badge>
              )}
              {paused && (
                <Badge className="bg-red-700 text-white" aria-live="polite">
                  Paused{pending ? ` (${pending})` : ''}
                </Badge>
              )}
            </ChunkGroup>
            <ChunkGroup className="space-x-2">
              {!paused ? (
                <Button size="sm" onClick={() => setPaused(true)}>
                  Pause
                </Button>
              ) : (
                <>
                  <Button size="sm" onClick={resume}>
                    Resume
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={pending === 0}
                    onClick={replay}
                  >
                    Replay
                  </Button>
                </>
              )}
            </ChunkGroup>
          </ChunkGroup>
        </CardHeader>
        <CardContent ref={listRef} onTouchStart={() => setShowDetails(true)}>
          <div
            role="group"
            aria-label="Filter events by decision"
            className="flex space-x-2 mb-4"
          >
            {filterOptions.map((opt, idx) => (
              <Button
                key={opt}
                ref={(el) => (filterRefs.current[idx] = el)}
                tabIndex={0}
                aria-label={`Filter events: ${opt.toLowerCase()}`}
                aria-pressed={filter === opt}
                onKeyDown={(e) => handleFilterKeyDown(e, idx)}
                onClick={() => setFilter(opt)}
                className={
                  filter === opt
                    ? 'bg-blue-700 text-white'
                    : 'bg-gray-200 text-gray-700'
                }
              >
                {opt}
              </Button>
            ))}
          </div>
          {listVisible && (
            <List
              height={384}
              itemCount={filteredEvents.length}
              itemSize={48}
              width="100%"
            >
              {({ index, style }) => (
                <div style={style} key={filteredEvents[index].eventId}>
                  <EventRow
                    event={filteredEvents[index]}
                    showDetails={showDetails}
                  />
                </div>
              )}
            </List>
          )}
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
