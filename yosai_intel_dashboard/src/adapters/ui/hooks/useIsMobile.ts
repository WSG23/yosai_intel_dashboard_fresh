import { useMemo } from 'react';

export const MOBILE_BREAKPOINT = 768;

export const useIsMobile = (): boolean =>
  useMemo(
    () =>
      typeof window !== 'undefined'
        ? window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches
        : false,
    [],
  );

export default useIsMobile;
