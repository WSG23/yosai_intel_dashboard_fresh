import React, { useState, useEffect, Suspense } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { LineChart as LineChartIcon } from 'lucide-react';
import { ChunkGroup } from '../components/layout';
import ProgressiveSection from '../components/ProgressiveSection';
import EChart from '../components/EChart';
import { AccessibleVisualization } from '../components/accessibility';
import useGraphsData from '../hooks/useGraphsData';

const NetworkGraph = React.lazy(() => import('./visualizations/NetworkGraph'));
const FacilityLayout = React.lazy(
  () => import('./visualizations/FacilityLayout'),
);

interface ChartData {
  hourly_distribution?: Record<string, number | string>;
  temporal_patterns?: {
    hourly_distribution?: Record<string, number | string>;
  };
  [key: string]: unknown;
}

const Graphs: React.FC = () => {
  const {
    charts,
    data: chartData,
    isLoading,
    isError,
    selectedChart,
    selectChart,
  } = useGraphsData();
  const [showDetails, setShowDetails] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    const fetchCharts = async () => {
      setIsLoading(true);
      setIsError(false);
      try {
        const charts = await graphsAPI.getAvailableCharts();
        const extra: AvailableChart[] = [
          {
            type: 'network',
            name: 'Network Graph',
            description: 'Graph relationships',
          },
          {
            type: 'facility',
            name: 'Facility Layout',
            description: '3D facility layout',
          },
        ];
        const allCharts = [...charts, ...extra];
        setAvailableCharts(allCharts);
        if (allCharts.length > 0) {
          setSelectedChart(allCharts[0].type);
        }
      } catch (err) {
        console.error('Failed to fetch chart list', err);
        setIsError(true);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCharts();
  }, []);

  useEffect(() => {
    if (
      selectedChart === 'network' ||
      selectedChart === 'facility' ||
      !selectedChart
    ) {
      return;
    }
    const fetchData = async () => {
      setIsLoading(true);
      setIsError(false);
      try {
        const data = await graphsAPI.getChartData(selectedChart);
        setChartData(data);
      } catch (err) {
        console.error('Failed to fetch chart data', err);
        setChartData(null);
        setIsError(true);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [selectedChart]);

  const renderChart = () => {
    if (selectedChart === 'network') {
      const links = [
        { source: 'A', target: 'B' },
        { source: 'B', target: 'C' },
      ];
      return (
        <AccessibleVisualization
          title="Network Relationships"
          summary="Interactive graph showing relationships between nodes."
          tableData={{
            headers: ['Source', 'Target'],
            rows: links.map((l) => [l.source, l.target]),
          }}
        >
          <Suspense fallback={<div>Loading visualization...</div>}>
            <NetworkGraph />
          </Suspense>
        </AccessibleVisualization>
      );
    }

    if (selectedChart === 'facility') {
      const rooms = ['A', 'B', 'C'];
      return (
        <AccessibleVisualization
          title="3D Facility Layout"
          summary="Rotating 3D model of facility layout."
          tableData={{ headers: ['Room'], rows: rooms.map((r) => [r]) }}
        >
          <Suspense fallback={<div>Loading visualization...</div>}>
            <FacilityLayout />
          </Suspense>
        </AccessibleVisualization>
      );
    }

    const hourly = chartData?.hourly_distribution;
    if (selectedChart === 'timeline' && hourly) {
      const data = Object.entries(hourly).map(([hour, count]) => ({
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
          <EChart
            option={{
              tooltip: {},
              xAxis: { type: 'category', data: data.map(d => d.hour) },
              yAxis: { type: 'value' },
              series: [{ type: 'line', data: data.map(d => d.count) }],
            }}
          />
        </AccessibleVisualization>
      );
    }

    const patternHourly = chartData?.temporal_patterns?.hourly_distribution;
    if (selectedChart === 'patterns' && patternHourly) {
      const data = Object.entries(patternHourly).map(([hour, count]) => ({
        hour,
        count: Number(count),
      }));
      return (
        <AccessibleVisualization
          title="Temporal Patterns"
          summary={`Temporal patterns with ${data.length} data points.`}
          tableData={{
            headers: ['Hour', 'Count'],
            rows: data.map((d) => [d.hour, d.count]),
          }}
        >
          <EChart
            option={{
              tooltip: {},
              xAxis: { type: 'category', data: data.map(d => d.hour) },
              yAxis: { type: 'value' },
              series: [{ type: 'line', data: data.map(d => d.count) }],
            }}
          />
        </AccessibleVisualization>
      );
    }

    return null;
  };

  return (
    <div className="page-container">
      <ChunkGroup>
        <h1 className="mb-4 flex items-center space-x-2">
          <LineChartIcon size={20} />
          <span>Security Graphs</span>
        </h1>
        {charts.length > 0 && (
          <select
            className="mb-4 border p-2 rounded"
            value={selectedChart}
            onChange={(e) => selectChart(e.target.value)}
            aria-label="Select chart type"
          >
            {charts.map((chart) => (
              <option key={chart.type} value={chart.type}>
                {chart.name}
              </option>
            ))}
          </select>
        )}
        {isLoading && <p className="text-sm">Loading...</p>}
        {isError && (
          <p className="text-sm text-red-600">Failed to load chart data.</p>
        )}
        <ProgressiveSection
          title="Advanced Settings"
          id="graph-advanced-settings"
          className="mt-2"
        >
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showDetails}
              onChange={(e) => setShowDetails(e.target.checked)}
            />
            <span>Show chart details</span>
          </label>
        </ProgressiveSection>
      </ChunkGroup>
      {isLoading && (
        <div className="graphs-placeholder" role="status" aria-live="polite">
          Loading graphs...
        </div>
      )}
      {isError && (
        <div className="graphs-placeholder" role="alert">
          Failed to load graphs.
        </div>
      )}
      {!isLoading && !isError && <div role="presentation">{renderChart()}</div>}
      {!isLoading && !isError && showDetails && chartData && (
        <pre
          aria-label="chart-details"
          className="mt-4 whitespace-pre-wrap text-xs border p-2 rounded"
        >
          {JSON.stringify(chartData, null, 2)}
        </pre>
      )}
    </div>
  );
};

const GraphsPage: React.FC = () => (
  <ErrorBoundary>
    <Graphs />
  </ErrorBoundary>
);

export default GraphsPage;
