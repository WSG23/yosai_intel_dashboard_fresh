import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';

class MockSocket {
  public onmessage: ((ev: { data: string }) => void) | null = null;
  public onopen: (() => void) | null = null;
  public onclose: (() => void) | null = null;
  public close = jest.fn();
  constructor(public url: string) {
    MockSocket.instance = this;
  }
  static instance: MockSocket | null = null;
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
});
