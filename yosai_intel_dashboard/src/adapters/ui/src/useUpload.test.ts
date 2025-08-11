import { renderHook, act } from '@testing-library/react';
import useUpload from '../hooks/useUpload';

describe('useUpload', () => {
  beforeAll(() => {
    Object.defineProperty(global, 'crypto', {
      value: { randomUUID: () => 'test-id' },
    });
  });

  it('assigns a string id to dropped files', () => {
    const { result } = renderHook(() => useUpload());
    const file = new File(['data'], 'test.csv', { type: 'text/csv' });
    act(() => {
      result.current.onDrop([file]);
    });

    expect(typeof result.current.files[0].id).toBe('string');
  });

  it('updates file status to error on cancel', () => {
    const { result } = renderHook(() => useUpload());
    const file = new File(['data'], 'test.csv', { type: 'text/csv' });
    act(() => {
      result.current.onDrop([file]);
    });
    const id = result.current.files[0].id;
    act(() => {
      result.current.cancelUpload(id);
    });
    expect(result.current.files[0].status).toBe('error');
    expect(result.current.files[0].error).toBe('Cancelled');
  });
});
