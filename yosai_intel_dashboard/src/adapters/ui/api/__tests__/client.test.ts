import { beforeEach, describe, expect, it, vi } from 'vitest';

// Minimal DOM polyfills
const listeners: Record<string, Array<(e: any) => void>> = {};
(global as any).window = {
  addEventListener: (event: string, cb: (e: any) => void) => {
    (listeners[event] = listeners[event] || []).push(cb);
  },
  dispatchEvent: (e: any) => {
    (listeners[e.type] || []).forEach((cb) => cb(e));
    return true;
  },
  location: { href: '' },
} as any;
(global as any).navigator = { onLine: true } as any;
(global as any).document = { cookie: '' } as any;
(global as any).Event = class {
  type: string;
  constructor(type: string) {
    this.type = type;
  }
} as any;

vi.mock('react-hot-toast', () => ({
  toast: { error: vi.fn() },
}));

let apiRequest: any;
let toast: any;

beforeAll(async () => {
  const clientMod = await import('../client.ts');
  apiRequest = clientMod.apiRequest;
  toast = (await import('react-hot-toast')).toast;
});

describe('apiRequest error handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps known codes to friendly messages', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ code: 'invalid_input', message: 'failed' }),
    }) as any;

    await expect(apiRequest({ url: '/test', method: 'GET' })).rejects.toThrow(
      'failed',
    );
    expect(toast.error).toHaveBeenCalledWith('Request validation failed');
  });

  it('uses backend message for unknown codes', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 418,
      json: async () => ({ code: 'teapot', message: 'short and stout' }),
    }) as any;

    await expect(apiRequest({ url: '/test', method: 'GET' })).rejects.toThrow(
      'short and stout',
    );
    expect(toast.error).toHaveBeenCalledWith('short and stout');
  });
});

describe('request queue bounds', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('limits offline queue to 50 requests', async () => {
    window.dispatchEvent(new Event('offline'));
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const fetchMock = vi.fn().mockRejectedValue(new Error('network')) as any;
    global.fetch = fetchMock;

    const requests = Array.from({ length: 55 }, () =>
      apiRequest({ url: '/test', method: 'GET' }).catch(() => {}),
    );
    await Promise.allSettled(requests);

    fetchMock.mockClear();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'success', data: {} }),
    } as any);

    window.dispatchEvent(new Event('online'));
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(fetchMock).toHaveBeenCalledTimes(50);
    expect(warnSpy).toHaveBeenCalledTimes(5);
    warnSpy.mockRestore();
  });
});

it('adds traceparent header to requests', async () => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ status: 'success', data: {} }),
  }) as any;
  await apiRequest({ url: '/trace', method: 'GET' });
  const headers = (global.fetch as any).mock.calls[0][1].headers;
  expect(headers.traceparent).toMatch(/^00-\w{32}-\w{16}-01$/);
});
