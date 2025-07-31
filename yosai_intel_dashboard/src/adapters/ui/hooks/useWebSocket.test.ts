import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';

jest.useFakeTimers();

beforeEach(() => {
  MockSocket.instances = [];
  MockSocket.instance = null;
  jest.clearAllTimers();
});

class MockSocket {
  public onmessage: ((ev: { data: string }) => void) | null = null;
  public onopen: (() => void) | null = null;
  public onclose: (() => void) | null = null;
  public close = jest.fn();
  constructor(public url: string) {
    MockSocket.instance = this;
    MockSocket.instances.push(this);
  }
  static instance: MockSocket | null = null;
  static instances: MockSocket[] = [];
}

describe('useWebSocket', () => {
  it('receives websocket messages', () => {
    const { result, unmount } = renderHook(() =>
      useWebSocket('ws://test', url => new MockSocket(url) as unknown as WebSocket)
    );

    act(() => {
      MockSocket.instance?.onmessage?.({ data: JSON.stringify({ a: 1 }) });
    });

    expect(result.current.data).toEqual(JSON.stringify({ a: 1 }));

    unmount();
    expect(MockSocket.instance?.close).toHaveBeenCalled();
  });

  it('reconnects with exponential backoff', () => {
    const { unmount } = renderHook(() =>
      useWebSocket('ws://test', url => new MockSocket(url) as unknown as WebSocket)
    );

    act(() => {
      MockSocket.instances[0].onclose?.();
    });

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(MockSocket.instances).toHaveLength(2);

    act(() => {
      MockSocket.instances[1].onclose?.();
    });

    act(() => {
      jest.advanceTimersByTime(1000);
    });
    expect(MockSocket.instances).toHaveLength(2);

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(MockSocket.instances).toHaveLength(3);

    unmount();
  });

  it('stops retries after cleanup', () => {
    const { unmount } = renderHook(() =>
      useWebSocket('ws://test', url => new MockSocket(url) as unknown as WebSocket)
    );

    act(() => {
      MockSocket.instances[0].onclose?.();
    });

    unmount();

    act(() => {
      jest.runOnlyPendingTimers();
    });

    expect(MockSocket.instances).toHaveLength(1);
  });
});
