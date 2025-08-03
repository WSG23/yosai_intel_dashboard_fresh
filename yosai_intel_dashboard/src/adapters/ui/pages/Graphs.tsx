import React, { useState, useEffect, useMemo, useRef } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { LineChart as LineChartIcon } from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Brush,
} from 'recharts';
import Timeline from '../components/Timeline';
import { graphsAPI, AvailableChart } from '../api/graphs';
import { AccessibleVisualization } from '../components/accessibility';


const Graphs: React.FC = () => {
  const [availableCharts, setAvailableCharts] = useState<AvailableChart[]>([]);
  const [selectedChart, setSelectedChart] = useState('');
  const [chartData, setChartData] = useState<any>(null);
  const { variant, isMobile } = useResponsiveChart();
  const [showDetails, setShowDetails] = useState(!isMobile);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setShowDetails(!isMobile);
  }, [isMobile]);

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        setIsVisible(true);
        observer.disconnect();
      }
    });
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    return () => observer.disconnect();
  }, []);


  useEffect(() => {
    const fetchCharts = async () => {
      try {
        const charts = await graphsAPI.getAvailableCharts();
        setAvailableCharts(charts);
        if (charts.length > 0) {
          setSelectedChart(charts[0].type);
        }
      } catch (err) {
        console.error('Failed to fetch chart list', err);
      }
    };

    fetchCharts();
  }, []);

  useEffect(() => {
    if (!selectedChart) return;
    const fetchData = async () => {
      try {
        const data = await graphsAPI.getChartData(selectedChart);
        setChartData(data);
      } catch (err) {
        console.error('Failed to fetch chart data', err);
        setChartData(null);
      }
    };

    fetchData();
  }, [selectedChart]);

  const rawData = useMemo(() => {
    if (!chartData) return null;
    if (selectedChart === 'timeline') return chartData.hourly_distribution;
    return chartData.temporal_patterns?.hourly_distribution ?? null;
  }, [chartData, selectedChart]);

    if (selectedChart === 'timeline' && chartData.hourly_distribution) {
      const data = Object.entries(chartData.hourly_distribution).map(([hour, count]) => ({
        hour,
        count: Number(count),
      }));
      return (
        <AccessibleVisualization
          title="Hourly Distribution"
          summary={`Hourly distribution with ${data.length} data points.`}
          tableData={{
            headers: ['Hour', 'Count'],
            rows: data.map((d) => [d.hour, d.count]),
          }}
        >
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        </AccessibleVisualization>
      );
    }

    if (
      selectedChart === 'patterns' &&
      chartData.temporal_patterns?.hourly_distribution
    ) {
      const data = Object.entries(chartData.temporal_patterns.hourly_distribution).map(
        ([hour, count]) => ({
          hour,
          count: Number(count),
        }),
      );
      return (
        <AccessibleVisualization
          title="Temporal Patterns"
          summary={`Temporal patterns with ${data.length} data points.`}
          tableData={{
            headers: ['Hour', 'Count'],
            rows: data.map((d) => [d.hour, d.count]),
          }}
        >
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#82ca9d" />
            </LineChart>
          </ResponsiveContainer>
        </AccessibleVisualization>
      );
    }


    return (
      <ResponsiveContainer
        width="100%"
        height={300}
        onTouchStart={() => setShowDetails(true)}
      >
        <Chart data={displayData}>
          {showDetails && <CartesianGrid strokeDasharray="3 3" />}
          <XAxis dataKey="hour" />
          <YAxis />
          {showDetails && <Tooltip />}
          <Series dataKey="count" {...props} />
        </Chart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="page-container">
      <h1 className="mb-4 flex items-center space-x-2">
        <LineChartIcon size={20} />
        <span>Security Graphs</span>
      </h1>
      {availableCharts.length > 0 && (
        <select
          className="mb-4 border p-2 rounded"
          value={selectedChart}
          onChange={(e) => setSelectedChart(e.target.value)}
          aria-label="Select chart type"
        >
          {availableCharts.map((chart) => (
            <option key={chart.type} value={chart.type}>
              {chart.name}
            </option>
          ))}
        </select>
      )}
      <div role="presentation">{renderChart()}</div>

    </div>
  );
};

const GraphsPage: React.FC = () => (
  <ErrorBoundary>
    <Graphs />
  </ErrorBoundary>
);

export default GraphsPage;
