import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AnalyticsPage from '../Analytics';
import useAnalyticsData from '../../hooks/useAnalyticsData';

jest.mock('../../hooks/useAnalyticsData');

// simple stub to show empty state when no children
jest.mock('../../components/layout', () => ({
  ChunkGroup: ({ children }: { children: React.ReactNode }) => (
    <div>{React.Children.count(children) ? children : <div role="status">No data available</div>}</div>
  ),
}));

type AnalyticsHookReturn = ReturnType<typeof useAnalyticsData>;
const mockUseAnalyticsData = useAnalyticsData as jest.MockedFunction<typeof useAnalyticsData>;

const sampleData = {
  total_records: 100,
  unique_devices: 10,
  date_range: { start: '2023-01-01', end: '2023-01-02' },
  patterns: [{ pattern: 'p1', count: 1, percentage: 100 }],
  device_distribution: [{ device: 'd1', count: 1 }],
};

describe('Analytics page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows loading spinner initially', async () => {
    mockUseAnalyticsData.mockReturnValue({ data: null, loading: true, error: null, refresh: jest.fn() } as AnalyticsHookReturn);
    render(<AnalyticsPage />);
    expect(await screen.findByText(/loading analytics/i)).toBeInTheDocument();
  });

  it('displays error state with retry button that refreshes', async () => {
    const refresh = jest.fn();
    mockUseAnalyticsData.mockReturnValue({ data: null, loading: false, error: 'error', refresh } as AnalyticsHookReturn);
    render(<AnalyticsPage />);
    const retry = await screen.findByRole('button', { name: /retry/i });
    await userEvent.click(retry);
    await waitFor(() => expect(refresh).toHaveBeenCalled());
  });

  it('renders empty state component for empty dataset', async () => {
    mockUseAnalyticsData.mockReturnValue({
      data: { ...sampleData, patterns: [], device_distribution: [] },
      loading: false,
      error: null,
      refresh: jest.fn(),
    } as AnalyticsHookReturn);
    render(<AnalyticsPage />);
    await userEvent.click(await screen.findByText(/click to view analytics/i));
    expect(await screen.findByRole('status')).toHaveTextContent(/no data available/i);
  });

  it('has accessible controls', async () => {
    mockUseAnalyticsData.mockReturnValue({ data: sampleData, loading: false, error: null, refresh: jest.fn() } as AnalyticsHookReturn);
    render(<AnalyticsPage />);
    expect(await screen.findByRole('combobox', { name: /select data source/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /export csv/i })).toBeInTheDocument();
  });

  it('triggers CSV export when export button clicked', async () => {
    mockUseAnalyticsData.mockReturnValue({ data: sampleData, loading: false, error: null, refresh: jest.fn() } as AnalyticsHookReturn);
    const clickSpy = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const createSpy = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock');
    const revokeSpy = jest.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});

    render(<AnalyticsPage />);
    const exportBtn = await screen.findByRole('button', { name: /export csv/i });
    await userEvent.click(exportBtn);

    expect(createSpy).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(revokeSpy).toHaveBeenCalled();

    clickSpy.mockRestore();
    createSpy.mockRestore();
    revokeSpy.mockRestore();
  });
});

