import { renderHook, act } from '@testing-library/react';
import useResponsiveChart from './useResponsiveChart';

describe('useResponsiveChart', () => {
  it('returns area chart for mobile widths', () => {
    (window as any).innerWidth = 500;
    const { result } = renderHook(() => useResponsiveChart());
    expect(result.current.variant).toBe('area');
    expect(result.current.isMobile).toBe(true);
  });

  it('switches variants on resize', () => {
    (window as any).innerWidth = 1200;
    const { result } = renderHook(() => useResponsiveChart());
    expect(result.current.variant).toBe('line');

    act(() => {
      (window as any).innerWidth = 800;
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current.variant).toBe('bar');
    expect(result.current.isMobile).toBe(false);

    act(() => {
      (window as any).innerWidth = 500;
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current.variant).toBe('area');
    expect(result.current.isMobile).toBe(true);
  });
});

