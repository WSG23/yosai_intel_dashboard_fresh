import { useCallback, useEffect, useRef, useState } from 'react';
import { graphsAPI, AvailableChart } from '../api/graphs';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/v1';

// In-memory cache for chart data
const chartCache = new Map<string, any>();

export interface UseGraphsDataResult {
  charts: AvailableChart[];
  data: any;
  isLoading: boolean;
  isError: boolean;
  selectedChart: string;
  selectChart: (chart: string) => void;
}

const extraCharts: AvailableChart[] = [
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

const useGraphsData = (): UseGraphsDataResult => {
  const [charts, setCharts] = useState<AvailableChart[]>([]);
  const [selectedChart, setSelectedChart] = useState('');
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);

  const controllerRef = useRef<AbortController | null>(null);

  const fetchCharts = useCallback(async (signal: AbortSignal) => {
    setIsLoading(true);
    setIsError(false);
    try {
      const charts = await graphsAPI.getAvailableCharts();
      if (signal.aborted) return;
      const allCharts = [...charts, ...extraCharts];
      setCharts(allCharts);
      if (!selectedChart && allCharts.length > 0) {
        setSelectedChart(allCharts[0].type);
      }
    } catch (err) {
      if (!signal.aborted) {
        setIsError(true);
      }
    } finally {
      if (!signal.aborted) {
        setIsLoading(false);
      }
    }
  }, [selectedChart]);

  const fetchChartData = useCallback(
    async (chart: string, signal: AbortSignal) => {
      setIsLoading(true);
      setIsError(false);
      try {
        // Prefer cached data
        if (chartCache.has(chart)) {
          setData(chartCache.get(chart));
          setIsLoading(false);
          return;
        }
        const res = await fetch(`${API_BASE_URL}/graphs/chart/${chart}`, {
          signal,
          credentials: 'include',
        });
        if (!res.ok) {
          throw new Error('Failed to fetch chart data');
        }
        const payload = await res.json();
        const chartData = payload.data ? payload.data : payload;
        chartCache.set(chart, chartData);
        if (!signal.aborted) {
          setData(chartData);
        }
      } catch (err) {
        if (!signal.aborted) {
          setIsError(true);
          setData(null);
        }
      } finally {
        if (!signal.aborted) {
          setIsLoading(false);
        }
      }
    },
    []
  );

  useEffect(() => {
    const controller = new AbortController();
    controllerRef.current?.abort();
    controllerRef.current = controller;
    fetchCharts(controller.signal);
    return () => controller.abort();
  }, [fetchCharts]);

  useEffect(() => {
    if (!selectedChart || selectedChart === 'network' || selectedChart === 'facility') {
      setData(null);
      return;
    }
    const controller = new AbortController();
    controllerRef.current?.abort();
    controllerRef.current = controller;
    fetchChartData(selectedChart, controller.signal);
    return () => controller.abort();
  }, [selectedChart, fetchChartData]);

  const selectChart = (chart: string) => setSelectedChart(chart);

  return { charts, data, isLoading, isError, selectedChart, selectChart };
};

export default useGraphsData;
