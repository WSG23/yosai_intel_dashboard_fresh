import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Brush,
  ResponsiveContainer,
} from 'recharts';
import { usePreferencesStore } from '../state';
import { useNetworkStatus } from '../lib/network';

export interface TimelineDatum {
  time: string | number;
  value: number;
}

interface TimelineProps {
  data: TimelineDatum[];
  onRangeChange?: (range: { start: TimelineDatum; end: TimelineDatum }) => void;
}

const Timeline: React.FC<TimelineProps> = ({ data, onRangeChange }) => {
  const { saveData } = usePreferencesStore();
  const network = useNetworkStatus();
  const dataSaver =
    saveData || network.saveData || ['slow-2g', '2g'].includes(network.effectiveType ?? '');
  const [range, setRange] = useState<{ startIndex: number; endIndex: number }>({
    startIndex: 0,
    endIndex: data.length - 1,
  });

  const handleBrushChange = (r: any) => {
    if (!r) return;
    const { startIndex, endIndex } = r;
    setRange({ startIndex, endIndex });
    if (onRangeChange) {
      const start = data[startIndex];
      const end = data[endIndex];
      if (start && end) {
        onRangeChange({ start, end });
      }
    }
  };

  const chartData = dataSaver ? data.filter((_, i) => i % 2 === 0) : data;

  return (
    <div style={{ width: '100%', height: 300, touchAction: 'none' }}>
      <ResponsiveContainer>
        <LineChart data={chartData}>
          {!dataSaver && <CartesianGrid strokeDasharray="3 3" />}
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#8884d8"
            dot={!dataSaver}
          />
          {!dataSaver && (
            <Brush
              dataKey="time"
              startIndex={range.startIndex}
              endIndex={range.endIndex}
              onChange={handleBrushChange}
              travellerWidth={12}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Timeline;
