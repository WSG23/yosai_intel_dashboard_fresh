jest.mock('axios', () => require('axios/dist/node/axios.cjs'));
import { apiClient } from '../client';
import { toast } from 'react-hot-toast';

jest.mock('react-hot-toast', () => ({
  toast: { error: jest.fn() },
}));

describe('apiClient error interceptor', () => {
  const handler = apiClient.interceptors.response.handlers[0].rejected!;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('maps known codes to friendly messages', async () => {
    const error = {
      config: { url: '/test', headers: {} },
      response: {
        status: 400,
        data: { code: 'invalid_input', message: 'failed' },
        config: {},
        headers: {},
      },
    } as any;

    jest.spyOn(console, 'error').mockImplementation(() => {});
    await expect(handler(error)).rejects.toBe(error);
    expect(toast.error).toHaveBeenCalledWith('Request validation failed');
  });

  it('uses backend message for unknown codes', async () => {
    const error = {
      config: { url: '/test', headers: {} },
      response: {
        status: 418,
        data: { code: 'teapot', message: 'short and stout' },
        config: {},
        headers: {},
      },
    } as any;

    jest.spyOn(console, 'error').mockImplementation(() => {});
    await expect(handler(error)).rejects.toBe(error);
    expect(toast.error).toHaveBeenCalledWith('short and stout');
  });
});
