import { request } from './api';
import { log } from './logger';

jest.mock('./logger', () => ({ log: jest.fn() }));

describe('request', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  test('returns parsed JSON on success', async () => {
    const data = { ok: true };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(data),
    }) as any;

    await expect(request('/test')).resolves.toEqual(data);
    expect(global.fetch).toHaveBeenCalledWith('/test', undefined);
  });

  test('throws ServiceError and logs on failure', async () => {
    const error = { code: 'fail', message: 'nope' };
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.resolve(error),
    }) as any;

    await expect(request('/test')).rejects.toEqual(error);
    expect(log).toHaveBeenCalledWith(
      'error',
      'API request failed',
      expect.objectContaining({ code: 'fail' })
    );
  });
});
