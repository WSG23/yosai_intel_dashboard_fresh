import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '..';
import { useEventStream } from '../useEventStream';

const useWithFallback = (
  wsFactory: (url: string) => WebSocket,
  esFactory: (url: string) => EventSource,
) => {
  const { data: wsData, isConnected } = useWebSocket('ws://test', wsFactory);
  const { data: esData } = useEventStream('/events', esFactory, !isConnected);
  return { data: isConnected ? wsData : esData };
};

class MockWS {
  public onopen: (() => void) | null = null;
  public onclose: (() => void) | null = null;
  public onmessage: ((ev: { data: string }) => void) | null = null;
  public close = jest.fn();
  constructor(public url: string) {
    MockWS.instance = this;
  }
  static instance: MockWS | null = null;
}

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

describe('websocket fallback', () => {
  it('uses SSE when websocket fails to connect', () => {
    const { result, unmount } = renderHook(() =>
      useWithFallback(
        url => new MockWS(url) as unknown as WebSocket,
        url => new MockES(url) as unknown as EventSource,
      ),
    );

    act(() => {
      MockES.instance?.onmessage?.({ data: 'sse' });
    });

    expect(result.current.data).toBe('sse');

    unmount();
    expect(MockES.instance?.close).toHaveBeenCalled();
  });
});
