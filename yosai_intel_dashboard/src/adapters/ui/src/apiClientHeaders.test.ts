import { api } from '../api/client';

describe('api helper headers', () => {
  it('includes auth and CSRF headers in requests', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'success', data: {} }),
    }) as any;

    await api.patch('/test', {}, {
      headers: { Authorization: 'Bearer t', 'X-CSRF-Token': 'c' },
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: 'PATCH',
        headers: expect.objectContaining({
          Authorization: 'Bearer t',
          'X-CSRF-Token': 'c',
        }),
      })
    );
  });
});
