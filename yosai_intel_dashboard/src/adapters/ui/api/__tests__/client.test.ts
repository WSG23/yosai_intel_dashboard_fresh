import { apiRequest } from '../client';
import { toast } from 'react-hot-toast';

jest.mock('react-hot-toast', () => ({
  toast: { error: jest.fn() },
}));

describe('apiRequest error handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('maps known codes to friendly messages', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ code: 'invalid_input', message: 'failed' }),
    }) as any;

    await expect(apiRequest({ url: '/test', method: 'GET' })).rejects.toThrow(
      'failed'
    );
    expect(toast.error).toHaveBeenCalledWith('Request validation failed');
  });

  it('uses backend message for unknown codes', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 418,
      json: async () => ({ code: 'teapot', message: 'short and stout' }),
    }) as any;

    await expect(apiRequest({ url: '/test', method: 'GET' })).rejects.toThrow(
      'short and stout'
    );
    expect(toast.error).toHaveBeenCalledWith('short and stout');
  });
});

