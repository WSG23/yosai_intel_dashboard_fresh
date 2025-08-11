import { renderHook, act, waitFor } from '@testing-library/react';
import { useUpload } from './useUpload';
import { api } from '../api/client';

describe('useUpload', () => {
  it('sets file status to error when cancelled', async () => {
    const postMock = jest
      .spyOn(api, 'post')
      // never resolve to keep upload in progress
      .mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useUpload());
    const file = new File(['data'], 'file.csv');

    act(() => {
      result.current.onDrop([file]);
    });

    const id = result.current.files[0].id;

    act(() => {
      result.current.uploadAllFiles();
    });

    await waitFor(() => expect(postMock).toHaveBeenCalled());

    act(() => {
      result.current.cancelUpload(id);
    });

    await waitFor(() => {
      const f = result.current.files[0];
      expect(f.status).toBe('error');
      expect(f.error).toBe('Cancelled');
    });

    postMock.mockRestore();
  });
});
