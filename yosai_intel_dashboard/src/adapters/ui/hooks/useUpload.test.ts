import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import useUpload from './useUpload';
import { api } from '../api/client';

vi.useFakeTimers();

describe('useUpload cleanup', () => {
  it('stops polling after unmount', async () => {
    const postSpy = vi.spyOn(api, 'post').mockResolvedValue({ job_id: 'job1' });
    const getSpy = vi.spyOn(api, 'get').mockResolvedValue({ progress: 0, done: false });

    const { result, unmount } = renderHook(() => useUpload());

    const file = new File(['content'], 'test.csv', { type: 'text/csv' });

    act(() => {
      result.current.onDrop([file]);
    });

    await act(async () => {
      await result.current.uploadAllFiles();
    });

    unmount();

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(getSpy).not.toHaveBeenCalled();

    postSpy.mockRestore();
    getSpy.mockRestore();
  });
});
