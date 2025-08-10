import React from 'react';
import { render, screen } from '@testing-library/react';
import RealTimeAnalytics from '../pages/RealTimeAnalyticsPage';
import { useRealTimeAnalytics } from '../hooks/useRealTimeAnalytics';

jest.mock('../hooks/useRealTimeAnalytics', () => ({
  useRealTimeAnalytics: jest.fn(),
}));
jest.mock('../hooks/usePrefersReducedMotion', () => jest.fn(() => false));
jest.mock('../components/layout', () => ({
  ChunkGroup: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));
jest.mock('../components/ErrorBoundary', () => ({
  children,
}: {
  children: React.ReactNode;
}) => <>{children}</>);

type HookReturn = ReturnType<typeof useRealTimeAnalytics>;
const mockUseRealTimeAnalytics =
  useRealTimeAnalytics as jest.MockedFunction<typeof useRealTimeAnalytics>;

describe('RealTimeAnalyticsPage', () => {
  it('announces waiting state via polite live region', () => {
    mockUseRealTimeAnalytics.mockReturnValue({
      data: null,
      summary: null,
      charts: null,
    } as HookReturn);

    (window as any).matchMedia = jest.fn().mockImplementation(() => ({
      matches: false,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));

    render(<RealTimeAnalytics />);

    const liveRegion = screen.getByText(/waiting for analytics/i);
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');
  });
});

