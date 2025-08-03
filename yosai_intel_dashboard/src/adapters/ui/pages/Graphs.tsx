import React, { useState, useEffect } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { LineChart as LineChartIcon } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Brush,
} from 'recharts';
import { graphsAPI, AvailableChart } from '../api/graphs';
import { useSelection } from '../core/interaction/SelectionContext';

const Graphs: React.FC = () => {
  const [availableCharts, setAvailableCharts] = useState<AvailableChart[]>([]);
  const [selectedChart, setSelectedChart] = useState('');
  const [chartData, setChartData] = useState<any>(null);
  const { select } = useSelection();
  const [timelineRange, setTimelineRange] = useState({ startIndex: 0, endIndex: 23 });
  const [patternsRange, setPatternsRange] = useState({ startIndex: 0, endIndex: 23 });

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

  const renderChart = () => {
    if (!chartData) return null;

    if (selectedChart === 'timeline' && chartData.hourly_distribution) {
      const data = Object.entries(chartData.hourly_distribution).map(([hour, count]) => ({
        hour,
        count: Number(count),
      }));
      return (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.slice(timelineRange.startIndex, timelineRange.endIndex + 1)}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Brush
              dataKey="hour"
              height={20}
              stroke="#8884d8"
              startIndex={timelineRange.startIndex}
              endIndex={timelineRange.endIndex}
              onChange={(range) => setTimelineRange(range as any)}
            />
            <Line
              type="monotone"
              dataKey="count"
              stroke="#8884d8"
              onClick={(d: any) => select('hour', d.hour)}
            />
          </LineChart>
        </ResponsiveContainer>
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
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.slice(patternsRange.startIndex, patternsRange.endIndex + 1)}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Brush
              dataKey="hour"
              height={20}
              stroke="#82ca9d"
              startIndex={patternsRange.startIndex}
              endIndex={patternsRange.endIndex}
              onChange={(range) => setPatternsRange(range as any)}
            />
            <Line
              type="monotone"
              dataKey="count"
              stroke="#82ca9d"
              onClick={(d: any) => select('hour', d.hour)}
            />
          </LineChart>
        </ResponsiveContainer>
      );
    }

    return <p>No data available for this chart.</p>;
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
      <div>{renderChart()}</div>
    </div>
  );
};

const GraphsPage: React.FC = () => (
  <ErrorBoundary>
    <Graphs />
  </ErrorBoundary>
);

export default GraphsPage;
