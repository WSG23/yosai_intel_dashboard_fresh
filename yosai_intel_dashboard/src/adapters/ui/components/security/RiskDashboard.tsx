import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  LineChart,
  Line,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

interface RiskFactor {
  name: string;
  value: number;
  benchmark: number;
}

interface RiskDashboardProps {
  score: number;
  history: number[];
  factors: RiskFactor[];
}

const RiskDashboard: React.FC<RiskDashboardProps> = ({
  score,
  history,
  factors
}) => {
  const [displayScore, setDisplayScore] = useState(score);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let start = displayScore;
    const diff = score - start;
    const steps = 20;
    let current = 0;
    const interval = setInterval(() => {
      current += 1;
      setDisplayScore(start + (diff * current) / steps);
      if (current >= steps) {
        clearInterval(interval);
      }
    }, 30);
    return () => clearInterval(interval);
  }, [score]);

  const radialData = [{ name: 'risk', value: displayScore }];
  const historyData = history.map((h, index) => ({ index, score: h }));

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="text-lg font-semibold mb-4">Risk Dashboard</h2>
      <div className="flex flex-col md:flex-row items-center">
        <div className="relative w-40 h-40">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              innerRadius="70%"
              outerRadius="100%"
              data={radialData}
              startAngle={90}
              endAngle={450}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
              <RadialBar
                background
                clockWise
                dataKey="value"
                cornerRadius={10}
                fill="#ef4444"
              />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex items-center justify-center text-xl font-bold">
            {Math.round(displayScore)}
          </div>
        </div>
        <div className="flex-1 mt-4 md:mt-0 md:ml-8 w-full h-24">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData}>
              <Line
                type="monotone"
                dataKey="score"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      <button
        onClick={() => setExpanded((prev) => !prev)}
        className="mt-4 text-blue-600 underline"
      >
        {expanded ? 'Hide Details' : 'Show Details'}
      </button>
      {expanded && (
        <div className="mt-4" data-testid="risk-factors">
          <ResponsiveContainer width="100%" height={200}>
            <ComposedChart data={factors}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" barSize={20} fill="#3b82f6" />
              <Line type="monotone" dataKey="benchmark" stroke="#ef4444" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default RiskDashboard;
