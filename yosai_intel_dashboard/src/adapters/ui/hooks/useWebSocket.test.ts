import { renderHook, act } from '@testing-library/react';
import { useWebSocket, WebSocketState } from './useWebSocket';
import { eventBus } from '../eventBus';
import websocket_metrics from '../metrics/websocket_metrics';

jest.useFakeTimers();

beforeEach(() => {
  MockSocket.instances = [];
  MockSocket.instance = null;
  jest.clearAllTimers();
  websocket_metrics.reset();
});

class MockSocket {
  public onmessage: ((ev: { data: string }) => void) | null = null;
  public onopen: (() => void) | null = null;
  public onclose: (() => void) | null = null;
  public close = jest.fn();
  public pong = jest.fn();
  private handlers: Record<string, Function> = {};
  constructor(public url: string) {
    MockSocket.instance = this;
    MockSocket.instances.push(this);
  }
  on(evt: string, handler: Function) {
    this.handlers[evt] = handler;
  }
  trigger(evt: string) {
    this.handlers[evt]?.();
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
      MockSocket.instance?.onopen?.();
      MockSocket.instance?.onmessage?.({ data: JSON.stringify({ a: 1 }) });
    });

    expect(result.current.data).toEqual(JSON.stringify({ a: 1 }));

    unmount();
    expect(MockSocket.instance?.close).toHaveBeenCalled();
  });

  it('reconnects with exponential backoff', () => {
    const events: any[] = [];
    const off = eventBus.on('metrics_update', e => events.push(e));
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
    expect(events[0].websocket_reconnect_attempts_total).toBe(1);
    expect(websocket_metrics.snapshot().websocket_reconnect_attempts_total).toBe(1);

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

    off();
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

  it('responds to ping with pong and resets heartbeat', () => {

    const { unmount } = renderHook(() =>
      useWebSocket('ws://test', url => new MockSocket(url) as unknown as WebSocket)
    );

    act(() => {
      jest.advanceTimersByTime(29999);
    });
    expect(MockSocket.instance?.close).not.toHaveBeenCalled();

    act(() => {
      MockSocket.instance?.trigger('ping');
    });
    expect(MockSocket.instance?.pong).toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(29999);
    });
    expect(MockSocket.instance?.close).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(30000);
    });
    expect(MockSocket.instance?.close).toHaveBeenCalled();

    unmount();

  });
});
