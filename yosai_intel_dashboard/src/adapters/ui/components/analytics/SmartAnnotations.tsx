import React, { useEffect, useState } from 'react';

export interface DataPoint {
  timestamp: string;
  value: number;
}

interface Annotation {
  id: number;
  title: string;
  description: string;
}

interface SmartAnnotationsProps {
  /**
   * Series of data points that will be analysed for anomalies. The component
   * performs a simple statistical analysis to highlight points that deviate
   * from the mean by more than two standard deviations. These are surfaced as
   * "AI" generated annotations for demo purposes.
   */
  series: DataPoint[];
  className?: string;
}

/**
 * SmartAnnotations analyses a time‑series and renders callouts explaining
 * detected anomalies. The logic is intentionally lightweight so it can run in
 * the browser without external dependencies.
 */
const SmartAnnotations: React.FC<SmartAnnotationsProps> = ({ series, className = '' }) => {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);

  useEffect(() => {
    if (!series || series.length === 0) {
      setAnnotations([]);
      return;
    }

    const values = series.map((p) => p.value);
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    const anns: Annotation[] = [];
    series.forEach((point, idx) => {
      const diff = Math.abs(point.value - mean);
      if (diff > 2 * stdDev) {
        const direction = point.value > mean ? 'Spike' : 'Drop';
        const percent = ((diff / mean) * 100).toFixed(1);
        const desc =
          `Value ${point.value.toFixed(2)} deviates ${percent}% ` +
          `from average (${mean.toFixed(2)}) on ${new Date(point.timestamp).toLocaleString()}.`;
        anns.push({
          id: idx,
          title: `${direction} detected`,
          description: desc,
        });
      }
    });

    setAnnotations(anns);
  }, [series]);

  if (annotations.length === 0) {
    return null;
  }

  return (
    <div className={`smart-annotations ${className}`}>
      {annotations.map((a) => (
        <div key={a.id} className="annotation border rounded p-2 my-2 bg-yellow-50">
          <strong>{a.title}</strong>
          <p className="text-sm mt-1">{a.description}</p>
        </div>
      ))}
    </div>
  );
};

export default SmartAnnotations;
