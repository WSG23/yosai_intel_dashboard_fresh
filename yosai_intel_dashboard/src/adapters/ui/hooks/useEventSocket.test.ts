import { renderHook, act } from '@testing-library/react';
import { useEventSocket, EventSocketState } from './useEventSocket';
import { eventBus } from '../eventBus';

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

describe('useEventSocket', () => {
  it('receives websocket messages', () => {
    const { result, unmount } = renderHook(() =>
      useEventSocket('ws://test', url => new MockSocket(url) as unknown as WebSocket)
    );

    act(() => {
      MockSocket.instance?.onopen?.();
      MockSocket.instance?.onmessage?.({ data: JSON.stringify({ a: 1 }) });
    });

    expect(result.current.data).toEqual(JSON.stringify({ a: 1 }));

    unmount();
    expect(MockSocket.instance?.close).toHaveBeenCalled();
  });

  it('emits state changes via EventBus', () => {
    const states: EventSocketState[] = [];
    const unsubscribe = eventBus.on('event_socket_state', (s: EventSocketState) => {
      states.push(s);
    });

    const { unmount } = renderHook(() =>
      useEventSocket('ws://test', url => new MockSocket(url) as unknown as WebSocket)
    );

    act(() => {
      MockSocket.instance?.onopen?.();
    });

    unmount();
    unsubscribe();

    expect(states).toEqual([
      EventSocketState.CONNECTING,
      EventSocketState.CONNECTED,
      EventSocketState.DISCONNECTED,
    ]);
  });
});
