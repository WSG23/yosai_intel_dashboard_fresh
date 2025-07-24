import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Upload from './Upload';
import { ZustandProvider } from '../../state';
import axios from 'axios/dist/node/axios.cjs';

describe('Upload error handling', () => {
  beforeEach(() => {
    jest.spyOn(axios, 'post').mockRejectedValue(new Error('Server Error'));
  });

  afterEach(() => {
    (axios.post as jest.Mock).mockRestore();
  });

  it('shows error when upload fails', async () => {
    const { container } = render(
      <ZustandProvider>
        <Upload />
      </ZustandProvider>
    );
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const big = new File([new Array(1024 * 1024).fill('a').join('')], 'large.csv', { type: 'text/csv' });
    fireEvent.change(input, { target: { files: [big] } });
    await screen.findByText('large.csv');
    const btn = screen.getByRole('button', { name: /upload all/i });
    fireEvent.click(btn);
    await waitFor(() => {
      expect(screen.getByText('Server Error')).toBeInTheDocument();
    });
  });
});
