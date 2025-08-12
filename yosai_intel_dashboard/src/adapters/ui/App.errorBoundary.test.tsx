import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';

vi.mock('react-router-dom', () => ({
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  useLocation: () => ({ pathname: '/' }),
  useNavigate: () => vi.fn(),
}), { virtual: true });

vi.mock('lucide-react', () => ({
  Shield: () => <div />, Menu: () => <div />, Sun: () => <div />, Moon: () => <div />,
  Upload: () => <div />, BarChart3: () => <div />, TrendingUp: () => <div />,
  Download: () => <div />, Settings: () => <div />, Database: () => <div />,
  Activity: () => <div />, LayoutDashboard: () => <div />,
}), { virtual: true });

vi.mock('./state/store', () => ({
  useProficiencyStore: () => ({ level: 0, logFeatureUsage: vi.fn() }),
}), { virtual: true });

vi.mock('./components/upload', () => ({
  Upload: () => {
    throw new Error('load failure');
  },
}));

import App from './App';

describe('App error boundary', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    global.fetch = vi.fn().mockResolvedValue({ ok: true }) as any;
  });

  afterEach(() => {
    (console.error as any).mockRestore();
    (global.fetch as any).mockClear();
  });

  it('displays fallback when upload fails', async () => {
    render(<App />);
    expect(await screen.findByText('Something went wrong.')).toBeInTheDocument();
    expect(screen.getByText('Report Issue')).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith('/api/error-report', expect.any(Object));
  });
});
