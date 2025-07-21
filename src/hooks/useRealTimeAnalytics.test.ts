import { renderHook, act } from '@testing-library/react';
import { useRealTimeAnalytics } from './useRealTimeAnalytics';

jest.useFakeTimers();

class MockSocket {
  public onmessage: ((ev: { data: string }) => void) | null = null;
  public close = jest.fn();
  constructor(public url: string) {
    MockSocket.instance = this;
  }
  static instance: MockSocket | null = null;
}

describe('useRealTimeAnalytics', () => {
  it('processes websocket messages and interval updates', () => {
    const { result, unmount } = renderHook(() =>
      useRealTimeAnalytics('ws://test', 500, url => new MockSocket(url)),
    );

    act(() => {
      MockSocket.instance?.onmessage?.({ data: JSON.stringify({ a: 1 }) });
    });

    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current.data).toEqual({ a: 1 });
    expect(result.current.summary).toEqual({ a: 1 });
    expect(result.current.charts).toEqual({ a: 1 });

    unmount();
    expect(MockSocket.instance?.close).toHaveBeenCalled();
  });
});
