import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ExportPage from '../Export';

// helper to build a mock ReadableStream from string chunks
function createMockStream(chunks: string[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(controller) {
      chunks.forEach((chunk) => controller.enqueue(new TextEncoder().encode(chunk)));
      controller.close();
    },
  });
}

describe('Export page', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.resetAllMocks();
  });

  it('shows progress bar reaching 100% after successful export', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: createMockStream(['{"progress":50}', '{"progress":100}']),
    } as unknown as Response);

    render(<ExportPage />);
    await userEvent.click(screen.getByRole('button', { name: /start export/i }));

    const progress = await screen.findByRole('progressbar');
    await waitFor(() => expect(progress).toHaveAttribute('aria-valuenow', '100'));
    expect(progress).toHaveStyle('width: 100%');
  });

  it('aborts export on cancel and shows canceled status', async () => {
    const abortSpy = jest.fn();
    global.fetch = jest.fn((_url, opts: RequestInit = {}) => {
      opts.signal?.addEventListener('abort', abortSpy);
      return new Promise(() => {});
    }) as unknown as typeof fetch;

    render(<ExportPage />);
    await userEvent.click(screen.getByRole('button', { name: /start export/i }));
    const cancel = await screen.findByRole('button', { name: /cancel/i });
    await userEvent.click(cancel);

    await waitFor(() => expect(abortSpy).toHaveBeenCalled());
    expect(screen.getByText(/export cancelled/i)).toBeInTheDocument();
  });
});
