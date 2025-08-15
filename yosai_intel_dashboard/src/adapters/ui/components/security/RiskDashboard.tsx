import React, { useEffect, useState, useMemo } from 'react';
import EChart from '../EChart';
import usePrefersReducedMotion from '../../hooks/usePrefersReducedMotion';
import { usePreferencesStore } from '../../state';
import { useNetworkStatus } from '../../lib/network';

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

const RiskDashboardComponent: React.FC<RiskDashboardProps> = ({
  score,
  history,
  factors,
}) => {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [displayScore, setDisplayScore] = useState(score);
  const [expanded, setExpanded] = useState(false);
  const { saveData } = usePreferencesStore();
  const network = useNetworkStatus();
  const dataSaver =
    saveData || network.saveData || ['slow-2g', '2g'].includes(network.effectiveType ?? '');

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

  const historyData = useMemo(
    () =>
      (dataSaver ? history.filter((_, i) => i % 2 === 0) : history).map(
        (h, index) => ({ index, score: h }),
      ),
    [dataSaver, history],
  );
  const factorData = useMemo(
    () => (dataSaver ? factors.slice(0, 1) : factors),
    [dataSaver, factors],
  );

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="text-lg font-semibold mb-4">Risk Dashboard</h2>
      <div className="flex flex-col md:flex-row items-center">
        <div className="relative w-40 h-40">
          <EChart
            style={{ height: '100%' }}
            option={{
              series: [
                {
                  type: 'gauge',
                  min: 0,
                  max: 100,
                  progress: { show: true },
                  detail: { formatter: '{value}' },
                  data: [{ value: displayScore }],
                },
              ],
            }}
          />
          <div className="absolute inset-0 flex items-center justify-center text-xl font-bold">
            {Math.round(displayScore)}
          </div>
        </div>
        {!dataSaver && (
          <div className="flex-1 mt-4 md:mt-0 md:ml-8 w-full h-24">
            <EChart
              style={{ height: '100%' }}
              option={{
                xAxis: { type: 'category', data: historyData.map(d => d.index.toString()) },
                yAxis: { type: 'value' },
                series: [
                  {
                    type: 'line',
                    data: historyData.map(d => d.score),
                    showSymbol: false,
                  },
                ],
              }}
            />
          </div>
        )}
      </div>
      <button
        onClick={() => setExpanded((prev) => !prev)}
        className="mt-4 text-blue-600 underline"
      >
        {expanded ? 'Hide Details' : 'Show Details'}
      </button>
      {expanded && !dataSaver && (
        <div className="mt-4" data-testid="risk-factors">
          <EChart
            style={{ height: 200 }}
            option={{
              tooltip: {},
              xAxis: { type: 'category', data: factorData.map(f => f.name) },
              yAxis: { type: 'value' },
              series: [
                {
                  type: 'bar',
                  data: factorData.map(f => f.value),
                  animation: !prefersReducedMotion,
                },
                {
                  type: 'line',
                  data: factorData.map(f => f.benchmark),
                },
              ],
            }}
          />
        </div>
      )}
      {dataSaver && (
        <p className="mt-4 text-sm text-gray-500">
          Data saver enabled: chart detail reduced
        </p>
      )}
    </div>
  );
};

export default React.memo(RiskDashboardComponent);
