import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadPage from '../Upload';
import { api } from '../../api/client';

jest.mock('../../api/client');

const mockPost = api.post as jest.MockedFunction<typeof api.post>;
const mockGet = api.get as jest.MockedFunction<typeof api.get>;

beforeEach(() => {
  jest.clearAllMocks();
});

describe('Upload page', () => {
  it('allows drag and drop to add a file', async () => {
    const { container } = render(<UploadPage />);
    const dropzone = screen.getByRole('button', { name: /file upload drop zone/i });
    const file = new File(['content'], 'sample.csv', { type: 'text/csv' });

    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] },
    });
    expect(await screen.findByText('sample.csv')).toBeInTheDocument();
  });

  it('opens file dialog on keyboard activation', async () => {
    const { container } = render(<UploadPage />);
    const dropzone = screen.getByRole('button', { name: /file upload drop zone/i });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = jest.spyOn(input, 'click');

    fireEvent.keyDown(dropzone, { key: 'Enter' });
    expect(clickSpy).toHaveBeenCalled();
  });

  it('shows progress updates while uploading', async () => {
    jest.useFakeTimers();
    const { container } = render(<UploadPage />);
    const file = new File(['data'], 'prog.csv', { type: 'text/csv' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });
    await screen.findByText('prog.csv');

    mockPost.mockResolvedValue({ job_id: '1' } as any);
    mockGet
      .mockResolvedValueOnce({ progress: 25, done: false } as any)
      .mockResolvedValueOnce({ progress: 100, done: true } as any);

    const btn = screen.getByRole('button', { name: /upload all/i });
    await userEvent.click(btn);

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });
    await waitFor(() =>
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '25'),
    );

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });
    await waitFor(() =>
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100'),
    );
    jest.useRealTimers();
  });

  it('allows canceling a file', async () => {
    const { container } = render(<UploadPage />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['data'], 'remove.csv', { type: 'text/csv' });
    fireEvent.change(input, { target: { files: [file] } });
    await screen.findByText('remove.csv');
    fireEvent.click(screen.getByText(/remove/i));
    expect(screen.queryByText('remove.csv')).not.toBeInTheDocument();
  });

  it('displays error message when upload fails', async () => {
    const { container } = render(<UploadPage />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['data'], 'err.csv', { type: 'text/csv' });
    fireEvent.change(input, { target: { files: [file] } });
    await screen.findByText('err.csv');

    mockPost.mockRejectedValue(new Error('fail'));

    const btn = screen.getByRole('button', { name: /upload all/i });
    await userEvent.click(btn);

    await waitFor(() =>
      expect(screen.getByText('fail')).toBeInTheDocument(),
    );
  });
});
