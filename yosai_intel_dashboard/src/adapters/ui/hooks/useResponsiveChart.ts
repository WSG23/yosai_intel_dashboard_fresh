import { useEffect, useState } from 'react';

export type ChartVariant = 'line' | 'bar' | 'area';
export type LegendDensity = 'compact' | 'comfortable';
export type TooltipMode = 'hover' | 'tap';

function getVariant(width: number): ChartVariant {
  if (width < 640) return 'area';
  if (width < 1024) return 'bar';
  return 'line';
}

function getLegendDensity(width: number): LegendDensity {
  return width < 640 ? 'compact' : 'comfortable';
}

function getTooltipMode(width: number): TooltipMode {
  return width < 640 ? 'tap' : 'hover';
}

/**
 * Provides the preferred chart configuration based on viewport size.
 * Returns sizing info along with legend, tooltip and gesture settings.
 */
export const useResponsiveChart = () => {
  const [variant, setVariant] = useState<ChartVariant>(() =>
    getVariant(window.innerWidth),
  );
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 640);
  const [legendDensity, setLegendDensity] = useState<LegendDensity>(() =>
    getLegendDensity(window.innerWidth),
  );
  const [tooltipMode, setTooltipMode] = useState<TooltipMode>(() =>
    getTooltipMode(window.innerWidth),
  );
  const [enableGestures, setEnableGestures] = useState<boolean>(
    window.innerWidth < 640,
  );

  useEffect(() => {
    const onResize = () => {
      const width = window.innerWidth;
      setVariant(getVariant(width));
      const mobile = width < 640;
      setIsMobile(mobile);
      setLegendDensity(getLegendDensity(width));
      setTooltipMode(getTooltipMode(width));
      setEnableGestures(mobile);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return { variant, isMobile, legendDensity, tooltipMode, enableGestures };
};

export default useResponsiveChart;

