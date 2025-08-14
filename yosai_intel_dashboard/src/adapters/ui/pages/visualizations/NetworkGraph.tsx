import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

const NetworkGraph: React.FC = () => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const option: echarts.EChartsOption = {
      tooltip: {},
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          data: [
            { name: 'A' },
            { name: 'B' },
            { name: 'C' }
          ],
          edges: [
            { source: 'A', target: 'B' },
            { source: 'B', target: 'C' }
          ]
        }
      ]
    };
    chart.setOption(option);
    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, []);

  return (
    <div
      ref={ref}
      style={{ width: '100%', height: 300 }}
      role="img"
      aria-label="Relationship graph showing security entity connections"
    />
  );
};

export default NetworkGraph;
