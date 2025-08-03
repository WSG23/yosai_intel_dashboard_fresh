import { renderHook, act } from '@testing-library/react';
import { useEventStream } from './useEventStream';

jest.useFakeTimers();

class MockES {
  public onopen: (() => void) | null = null;
  public onmessage: ((ev: { data: string }) => void) | null = null;
  public onerror: (() => void) | null = null;
  public close = jest.fn();
  constructor(public url: string) {
    MockES.instance = this;
  }
  static instance: MockES | null = null;
}

describe('useEventStream', () => {
  it('debounces and merges incoming patches', () => {
    const { result } = renderHook(() =>
      useEventStream('/events', url => new MockES(url) as unknown as EventSource, true, 100),
    );

    act(() => {
      MockES.instance?.onmessage?.({ data: JSON.stringify({ a: 1 }) });
      MockES.instance?.onmessage?.({ data: JSON.stringify({ b: 2 }) });
    });

    act(() => {
      jest.advanceTimersByTime(99);
    });
    expect(result.current.data).toBeNull();

    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(result.current.data).toEqual({ a: 1, b: 2 });
  });
});
