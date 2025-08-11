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
});
