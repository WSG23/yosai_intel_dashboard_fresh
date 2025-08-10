import { renderHook } from '@testing-library/react';
import { useUpload } from './useUpload';
import { api } from '../api/client';

describe('useUpload', () => {
  it('aborts polling on cancel', async () => {
    jest.useFakeTimers();
    const get = jest.spyOn(api, 'get').mockResolvedValue({ progress: 0, done: false } as any);
    const clearSpy = jest.spyOn(global, 'clearTimeout');

    const { result } = renderHook(() => useUpload());
    const promise = result.current.pollStatus('1', 'job', jest.fn());

    await Promise.resolve();
    expect(get).toHaveBeenCalledTimes(1);

    result.current.cancel('1');
    await expect(promise).rejects.toThrow();

    jest.runOnlyPendingTimers();
    expect(get).toHaveBeenCalledTimes(1);
    expect(clearSpy).toHaveBeenCalled();

    get.mockRestore();
    clearSpy.mockRestore();
    jest.useRealTimers();
  });

  it('aborts polling on unmount', async () => {
    jest.useFakeTimers();
    const get = jest.spyOn(api, 'get').mockResolvedValue({ progress: 0, done: false } as any);
    const clearSpy = jest.spyOn(global, 'clearTimeout');

    const { result, unmount } = renderHook(() => useUpload());
    const promise = result.current.pollStatus('1', 'job', jest.fn());

    await Promise.resolve();
    expect(get).toHaveBeenCalledTimes(1);

    unmount();
    await expect(promise).rejects.toThrow();

    jest.runOnlyPendingTimers();
    expect(get).toHaveBeenCalledTimes(1);
    expect(clearSpy).toHaveBeenCalled();

    get.mockRestore();
    clearSpy.mockRestore();
    jest.useRealTimers();
  });
});

