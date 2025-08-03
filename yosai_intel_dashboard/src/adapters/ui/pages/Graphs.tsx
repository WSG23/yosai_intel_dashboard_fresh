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
} from 'recharts';
import { graphsAPI, AvailableChart } from '../api/graphs';
import useResponsiveChart from '../hooks/useResponsiveChart';

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

  const data = useMemo(() => {
    if (!rawData) return [];
    return Object.entries(rawData).map(([hour, count]) => ({
      hour,
      count: Number(count),
    }));
  }, [rawData]);

  const maxPoints = isMobile ? 30 : 100;
  const displayData = useMemo(() => {
    if (data.length <= maxPoints) return data;
    const step = Math.ceil(data.length / maxPoints);
    return data.filter((_, idx) => idx % step === 0);
  }, [data, maxPoints]);

  const renderChart = () => {
    if (!rawData) return <p>No data available for this chart.</p>;

    const color = selectedChart === 'timeline' ? '#8884d8' : '#82ca9d';
    const chartMap = {
      line: { Chart: LineChart, Series: Line, props: { type: 'monotone', stroke: color } },
      bar: { Chart: BarChart, Series: Bar, props: { fill: color } },
      area: {
        Chart: AreaChart,
        Series: Area,
        props: { type: 'monotone', stroke: color, fill: color, fillOpacity: 0.3 },
      },
    } as const;
    const { Chart, Series, props } = chartMap[variant];

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
        >
          {availableCharts.map((chart) => (
            <option key={chart.type} value={chart.type}>
              {chart.name}
            </option>
          ))}
        </select>
      )}
      <div ref={containerRef}>{isVisible && renderChart()}</div>
    </div>
  );
};

const GraphsPage: React.FC = () => (
  <ErrorBoundary>
    <Graphs />
  </ErrorBoundary>
);

export default GraphsPage;
