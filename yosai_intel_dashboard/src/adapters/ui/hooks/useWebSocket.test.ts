import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useWebSocket, WebSocketState } from '.';
import { eventBus } from '../eventBus';
import websocket_metrics from '../metrics/websocket_metrics';

vi.useFakeTimers();

beforeEach(() => {
  MockSocket.instances = [];
  MockSocket.instance = null;
  vi.clearAllTimers();
  websocket_metrics.reset();
});

class MockSocket {
  public onmessage: ((ev: { data: string }) => void) | null = null;
  public onopen: (() => void) | null = null;
  public onclose: (() => void) | null = null;
  public close = vi.fn();
  public pong = vi.fn();
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

class MockES {
  public onopen: (() => void) | null = null;
  public onmessage: ((ev: { data: string }) => void) | null = null;
  public onerror: (() => void) | null = null;
  public close = vi.fn();
  constructor(public url: string) {
    MockES.instance = this;
  }
  static instance: MockES | null = null;
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
      vi.advanceTimersByTime(1000);
    });

    expect(MockSocket.instances).toHaveLength(2);
    expect(events[0].websocket_reconnect_attempts_total).toBe(1);
    expect(websocket_metrics.snapshot().websocket_reconnect_attempts_total).toBe(1);

    act(() => {
      MockSocket.instances[1].onclose?.();
    });

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(MockSocket.instances).toHaveLength(2);

    act(() => {
      vi.advanceTimersByTime(1000);
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

    const countAfterClose = MockSocket.instances.length;

    act(() => {
      unmount();
      vi.advanceTimersByTime(1000);
    });

    expect(MockSocket.instances).toHaveLength(countAfterClose);
  });

  it('emits state transitions through the eventBus', () => {
    const handler = vi.fn();
    const off = eventBus.on('websocket_state', handler);
    const { unmount } = renderHook(() =>
      useWebSocket('ws://test', url => new MockSocket(url) as unknown as WebSocket),
    );

    act(() => {
      MockSocket.instance?.onopen?.();
    });
    expect(handler).toHaveBeenNthCalledWith(1, WebSocketState.CONNECTED);

    act(() => {
      MockSocket.instance?.onclose?.();
    });
    expect(handler).toHaveBeenNthCalledWith(2, WebSocketState.RECONNECTING);

    off();
    unmount();
  });

  it('responds to ping with pong and resets heartbeat', () => {

    const { unmount } = renderHook(() =>
      useWebSocket('ws://test', url => new MockSocket(url) as unknown as WebSocket)
    );

    act(() => {
      vi.advanceTimersByTime(29999);
    });
    expect(MockSocket.instance?.close).not.toHaveBeenCalled();

    act(() => {
      MockSocket.instance?.trigger('ping');
    });
    expect(MockSocket.instance?.pong).toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(29999);
    });
    expect(MockSocket.instance?.close).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(30000);
    });
    expect(MockSocket.instance?.close).toHaveBeenCalled();

    unmount();

  });

  it('falls back to EventSource after max retries', () => {
    const { result, unmount } = renderHook(() =>
      useWebSocket(
        'ws://test',
        url => new MockSocket(url) as unknown as WebSocket,
        {
          fallbackPath: '/events',
          eventSourceFactory: url => new MockES(url) as unknown as EventSource,
          maxRetries: 2,
        },
      ),
    );

    act(() => {
      // first websocket attempt fails
      MockSocket.instances[0].onclose?.();
      vi.advanceTimersByTime(1000);
      // second attempt fails triggering fallback
      MockSocket.instances[1].onclose?.();
      MockES.instance?.onopen?.();
      MockES.instance?.onmessage?.({ data: 'sse' });
    });

    expect(result.current.data).toBe('sse');

    const countAfterFallback = MockSocket.instances.length;

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(MockSocket.instances).toHaveLength(countAfterFallback);

    unmount();
    expect(MockES.instance?.close).toHaveBeenCalled();
  });
});
