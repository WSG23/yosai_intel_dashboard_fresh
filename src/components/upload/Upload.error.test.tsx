import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Upload from './Upload';

describe('Upload error handling', () => {
  beforeEach(() => {
    jest.spyOn(global, 'fetch').mockImplementation(() =>
      Promise.resolve({ ok: false, statusText: 'Server Error' } as Response)
    );
  });

  afterEach(() => {
    (global.fetch as jest.Mock).mockRestore();
  });

  it('shows error when upload fails', async () => {
    const { container } = render(<Upload />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const big = new File([new Array(1024 * 1024).fill('a').join('')], 'large.csv', { type: 'text/csv' });
    fireEvent.change(input, { target: { files: [big] } });
    await screen.findByText('large.csv');
    const btn = screen.getByRole('button', { name: /upload all/i });
    fireEvent.click(btn);
    await waitFor(() => {
      expect(screen.getByText('Upload failed: Server Error')).toBeInTheDocument();
    });
  });
});
