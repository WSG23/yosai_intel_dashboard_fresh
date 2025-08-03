import { useEffect, useState } from 'react';

export type ChartVariant = 'line' | 'bar' | 'area';

function getVariant(width: number): ChartVariant {
  if (width < 640) return 'area';
  if (width < 1024) return 'bar';
  return 'line';
}

/**
 * Provides the preferred chart variant based on viewport size.
 * Returns the variant and a boolean indicating if the viewport is mobile.
 */
export const useResponsiveChart = () => {
  const [variant, setVariant] = useState<ChartVariant>(() => getVariant(window.innerWidth));
  const [isMobile, setIsMobile] = useState<boolean>(window.innerWidth < 640);

  useEffect(() => {
    const onResize = () => {
      const width = window.innerWidth;
      setVariant(getVariant(width));
      setIsMobile(width < 640);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return { variant, isMobile };
};

export default useResponsiveChart;

