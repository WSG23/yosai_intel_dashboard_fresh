import { renderHook, act } from '@testing-library/react';
import useResponsiveChart from './useResponsiveChart';

beforeEach(() => {
  (window as any).matchMedia = (query: string) => ({
    matches: window.innerWidth <= parseInt(query.match(/\d+/)?.[0] || '0', 10),
    media: query,
    onchange: null,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  });
});

describe('useResponsiveChart', () => {
  afterEach(() => {
    Object.defineProperty(navigator, 'maxTouchPoints', {
      value: 0,
      configurable: true,
    });
  });

  it('returns mobile configuration for touch devices', () => {
    Object.defineProperty(navigator, 'maxTouchPoints', {
      value: 1,
      configurable: true,
    });
    (window as any).innerWidth = 500;
    const { result } = renderHook(() => useResponsiveChart());
    expect(result.current.variant).toBe('area');
    expect(result.current.isMobile).toBe(true);
    expect(result.current.legendDensity).toBe('compact');
    expect(result.current.tooltipMode).toBe('tap');
    expect(result.current.enableGestures).toBe(true);
  });

  it('switches settings on resize', () => {
    Object.defineProperty(navigator, 'maxTouchPoints', {
      value: 0,
      configurable: true,
    });
    (window as any).innerWidth = 1200;
    const { result } = renderHook(() => useResponsiveChart());
    expect(result.current.variant).toBe('line');
    expect(result.current.legendDensity).toBe('expanded');
    expect(result.current.enableGestures).toBe(false);

    act(() => {
      (window as any).innerWidth = 800;
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current.variant).toBe('bar');
    expect(result.current.legendDensity).toBe('comfortable');
    expect(result.current.tooltipMode).toBe('hover');
    expect(result.current.enableGestures).toBe(false);

    act(() => {
      Object.defineProperty(navigator, 'maxTouchPoints', {
        value: 1,
        configurable: true,
      });
      (window as any).innerWidth = 500;
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current.variant).toBe('area');
    expect(result.current.legendDensity).toBe('compact');
    expect(result.current.tooltipMode).toBe('tap');
    expect(result.current.enableGestures).toBe(true);
  });
});

