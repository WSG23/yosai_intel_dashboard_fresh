import React, { useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from 'recharts';
import { usePreferencesStore } from '../../state';
import { useNetworkStatus } from '../../lib/network';

export interface SeriesPoint {
  x: string;
  value: number;
}

interface ComparisonViewProps {
  seriesA: SeriesPoint[];
  seriesB: SeriesPoint[];
  /** Optional labels for the two series */
  labels?: [string, string];
}

/**
 * ComparisonView renders two data series either side-by-side or overlaid. It
 * also computes simple statistical indicators (mean and difference between
 * series) to aid comparison.
 */
const ComparisonView: React.FC<ComparisonViewProps> = ({
  seriesA,
  seriesB,
  labels = ['Series A', 'Series B'],
}) => {
  const [mode, setMode] = useState<'overlay' | 'side-by-side'>('overlay');
  const { saveData } = usePreferencesStore();
  const network = useNetworkStatus();
  const dataSaver =
    saveData || network.saveData || ['slow-2g', '2g'].includes(network.effectiveType ?? '');

  const merged = useMemo(() => {
    const map: Record<string, { a?: number; b?: number }> = {};
    seriesA.forEach((p) => {
      if (!map[p.x]) map[p.x] = {};
      map[p.x].a = p.value;
    });
    seriesB.forEach((p) => {
      if (!map[p.x]) map[p.x] = {};
      map[p.x].b = p.value;
    });
    return Object.entries(map).map(([x, { a = 0, b = 0 }]) => ({ x, a, b }));
  }, [seriesA, seriesB]);

  const stats = useMemo(() => {
    const mean = (arr: number[]) =>
      arr.length ? arr.reduce((acc, v) => acc + v, 0) / arr.length : 0;
    const aVals = seriesA.map((p) => p.value);
    const bVals = seriesB.map((p) => p.value);
    return {
      meanA: mean(aVals),
      meanB: mean(bVals),
    };
  }, [seriesA, seriesB]);

  return (
    <div className="comparison-view">
      <div className="flex space-x-2 mb-2">
        <button
          className={`px-2 py-1 border rounded ${mode === 'overlay' ? 'bg-gray-200' : ''}`}
          onClick={() => setMode('overlay')}
        >
          Overlay
        </button>
        <button
          className={`px-2 py-1 border rounded ${mode === 'side-by-side' ? 'bg-gray-200' : ''}`}
          onClick={() => setMode('side-by-side')}
        >
          Side by Side
        </button>
      </div>

      {mode === 'overlay' ? (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={merged}>
            {!dataSaver && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis dataKey="x" />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="a"
              stroke="#8884d8"
              name={labels[0]}
              dot={!dataSaver}
            />
            <Line
              type="monotone"
              dataKey="b"
              stroke="#82ca9d"
              name={labels[1]}
              dot={!dataSaver}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex space-x-4" style={{ height: 300 }}>
          <ResponsiveContainer width="50%" height="100%">
            <LineChart data={dataSaver ? seriesA.filter((_, i) => i % 2 === 0) : seriesA}>
              {!dataSaver && <CartesianGrid strokeDasharray="3 3" />}
              <XAxis dataKey="x" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#8884d8"
                name={labels[0]}
                dot={!dataSaver}
              />
            </LineChart>
          </ResponsiveContainer>
          <ResponsiveContainer width="50%" height="100%">
            <LineChart data={dataSaver ? seriesB.filter((_, i) => i % 2 === 0) : seriesB}>
              {!dataSaver && <CartesianGrid strokeDasharray="3 3" />}
              <XAxis dataKey="x" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#82ca9d"
                name={labels[1]}
                dot={!dataSaver}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-4 text-sm">
        <p>
          Mean {labels[0]}: {stats.meanA.toFixed(2)} | Mean {labels[1]}:{' '}
          {stats.meanB.toFixed(2)} | Δ {(stats.meanA - stats.meanB).toFixed(2)}
        </p>
      </div>
    </div>
  );
};

export default ComparisonView;
