import { renderHook, act } from '@testing-library/react';
import { useUploadWebSocket } from './useUploadWebSocket';

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

describe('useUploadWebSocket', () => {
  beforeEach(() => {
    (global as any).WebSocket = jest.fn((url: string) => new MockSocket(url));
  });

  it('subscribes to progress and can unsubscribe', () => {
    const { result } = renderHook(() => useUploadWebSocket());
    const cb = jest.fn();

    act(() => {
      result.current.subscribeToUploadProgress('1', cb);
    });

    act(() => {
      MockSocket.instance?.onmessage?.({ data: JSON.stringify({ progress: 42 }) } as any);
    });

    expect(cb).toHaveBeenCalledWith(42);

    const firstInstance = MockSocket.instance;

    act(() => {
      result.current.unsubscribe('1');
    });

    expect(firstInstance?.close).toHaveBeenCalled();

    act(() => {
      result.current.subscribeToUploadProgress('1', cb);
    });

    expect(MockSocket.instance).not.toBe(firstInstance);
  });

  it('uses REACT_APP_WS_URL when provided', () => {
    process.env.REACT_APP_WS_URL = 'example.com:1234';
    const { result } = renderHook(() => useUploadWebSocket());

    act(() => {
      result.current.subscribeToUploadProgress('abc', jest.fn());
    });

    expect(MockSocket.instance?.url).toBe('ws://example.com:1234/ws/upload/abc');
    delete process.env.REACT_APP_WS_URL;
  });
});
