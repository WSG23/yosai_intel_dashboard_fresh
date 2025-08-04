import { renderHook, act } from '@testing-library/react';
import useResponsiveChart from './useResponsiveChart';

describe('useResponsiveChart', () => {
  it('returns mobile configuration for small widths', () => {
    (window as any).innerWidth = 500;
    const { result } = renderHook(() => useResponsiveChart());
    expect(result.current.variant).toBe('area');
    expect(result.current.isMobile).toBe(true);
    expect(result.current.legendDensity).toBe('compact');
    expect(result.current.tooltipMode).toBe('tap');
    expect(result.current.enableGestures).toBe(true);
  });

  it('switches settings on resize', () => {
    (window as any).innerWidth = 1200;
    const { result } = renderHook(() => useResponsiveChart());
    expect(result.current.variant).toBe('line');
    expect(result.current.legendDensity).toBe('comfortable');
    expect(result.current.enableGestures).toBe(false);

    act(() => {
      (window as any).innerWidth = 800;
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current.variant).toBe('bar');
    expect(result.current.isMobile).toBe(false);
    expect(result.current.legendDensity).toBe('comfortable');
    expect(result.current.tooltipMode).toBe('hover');
    expect(result.current.enableGestures).toBe(false);

    act(() => {
      (window as any).innerWidth = 500;
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current.variant).toBe('area');
    expect(result.current.isMobile).toBe(true);
    expect(result.current.legendDensity).toBe('compact');
    expect(result.current.tooltipMode).toBe('tap');
    expect(result.current.enableGestures).toBe(true);
  });
});

