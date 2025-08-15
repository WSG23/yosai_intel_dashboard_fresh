import React, { useEffect, useRef } from 'react';
import type { EChartsOption } from 'echarts';

export interface EChartProps {
  option: EChartsOption;
  style?: React.CSSProperties;
}

const EChart: React.FC<EChartProps> = ({ option, style }) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let chart: any;
    let resize: (() => void) | undefined;
    let mounted = true;

    import('echarts').then((echarts) => {
      if (!mounted || !ref.current) return;
      chart = echarts.init(ref.current);
      chart.setOption(option);
      resize = () => chart.resize();
      window.addEventListener('resize', resize);
    });

    return () => {
      mounted = false;
      if (resize) window.removeEventListener('resize', resize);
      if (chart) chart.dispose();
    };
  }, [option]);

  return <div ref={ref} style={{ width: '100%', height: 300, ...style }} />;
};

export default React.memo(EChart);
