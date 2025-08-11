import { renderHook, act } from '@testing-library/react';
import { useUpload } from '../hooks/useUpload';

describe('useUpload', () => {
  it('adds and removes files', () => {
    const { result } = renderHook(() => useUpload());
    const file = new File(['content'], 'test.csv', { type: 'text/csv' });

    act(() => {
      result.current.onDrop([file]);
    });

    expect(result.current.files).toHaveLength(1);
    const id = result.current.files[0].id;

    act(() => {
      result.current.removeFile(id);
    });

    expect(result.current.files).toHaveLength(0);
  });
});
