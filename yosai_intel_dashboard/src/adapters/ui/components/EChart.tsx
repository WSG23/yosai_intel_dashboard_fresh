import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export interface EChartProps {
  option: echarts.EChartsOption;
  style?: React.CSSProperties;
}

const EChart: React.FC<EChartProps> = ({ option, style }) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    chart.setOption(option);
    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [option]);

  return <div ref={ref} style={{ width: '100%', height: 300, ...style }} />;
};

export default EChart;
