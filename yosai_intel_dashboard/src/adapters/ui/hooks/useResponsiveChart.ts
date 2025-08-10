import { useEffect, useState } from 'react';
import useIsMobile from './useIsMobile';

export type ChartVariant = 'line' | 'bar' | 'area';
export type LegendDensity = 'compact' | 'comfortable' | 'expanded';
export type TooltipMode = 'hover' | 'tap';

const isTouchDevice = (): boolean => {
  return (
    (typeof navigator !== 'undefined' && navigator.maxTouchPoints > 0) ||
    (typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(pointer: coarse)').matches)
  );
};

function getVariant(width: number): ChartVariant {
  if (width < 640) return 'area';
  if (width < 1024) return 'bar';
  return 'line';
}

function getLegendDensity(width: number): LegendDensity {
  if (width < 600) return 'compact';
  if (width < 1024) return 'comfortable';
  return 'expanded';
}

function getTooltipMode(width: number, touch: boolean): TooltipMode {
  return width < 600 || touch ? 'tap' : 'hover';
}

function getEnableGestures(width: number, touch: boolean): boolean {
  return touch && width < 1024;
}

/**
 * Provides the preferred chart configuration based on viewport size.
 * Returns sizing info along with legend, tooltip and gesture settings.
 */
export const useResponsiveChart = () => {
  const initialWidth = typeof window !== 'undefined' ? window.innerWidth : 0;
  const touch = isTouchDevice();
  const [variant, setVariant] = useState<ChartVariant>(() =>
    getVariant(initialWidth),
  );
  const [legendDensity, setLegendDensity] = useState<LegendDensity>(() =>
    getLegendDensity(initialWidth),
  );
  const [tooltipMode, setTooltipMode] = useState<TooltipMode>(() =>
    getTooltipMode(initialWidth, touch),
  );
  const [enableGestures, setEnableGestures] = useState<boolean>(() =>
    getEnableGestures(initialWidth, touch),
  );

  useEffect(() => {
    const onResize = () => {
      const width = window.innerWidth;
      const touch = isTouchDevice();
      setVariant(getVariant(width));
      setLegendDensity(getLegendDensity(width));
      setTooltipMode(getTooltipMode(width, touch));
      setEnableGestures(getEnableGestures(width, touch));
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const isMobile = useIsMobile();
  return { variant, isMobile, legendDensity, tooltipMode, enableGestures };
};

export default useResponsiveChart;

