import { uploadAPI, saveColumnMappings, saveDeviceMappings } from './upload';
import { api } from './client';

jest.mock('./client', () => ({
  api: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

describe('uploadAPI', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.post as jest.Mock).mockResolvedValue({ task_id: '1', data: { ok: true } });
    (api.get as jest.Mock).mockResolvedValue({ status: 'done' });
  });

  it('uploadFile posts form data', async () => {
    const file = new File(['a'], 'test.csv', { type: 'text/csv' });
    const result = await uploadAPI.uploadFile(file);
    expect(api.post).toHaveBeenCalledWith(
      '/upload',
      expect.any(FormData),
      expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } })
    );
    expect(result.taskId).toBe('1');
    expect(result.data).toEqual({ ok: true });
  });

  it('waitForProcessing calls api.get', async () => {
    const res = await uploadAPI.waitForProcessing('123');
    expect(api.get).toHaveBeenCalledWith('/upload/status/123');
    expect(res).toEqual({ status: 'done' });
  });

  it('applyColumnMappings posts to endpoint', async () => {
    await uploadAPI.applyColumnMappings('file.csv', { a: 'b' });
    expect(api.post).toHaveBeenCalledWith('/upload/file.csv/columns', { mappings: { a: 'b' } });
  });
});

describe('mapping helpers', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.post as jest.Mock).mockResolvedValue(undefined);
  });

  it('saveColumnMappings posts mapping', async () => {
    await saveColumnMappings('id1', { c: 'd' });
    expect(api.post).toHaveBeenCalledWith('/mappings/columns', { file_id: 'id1', mappings: { c: 'd' } });
  });

  it('saveDeviceMappings posts mapping', async () => {
    await saveDeviceMappings('id1', { dev: 1 });
    expect(api.post).toHaveBeenCalledWith('/mappings/devices', { file_id: 'id1', mappings: { dev: 1 } });
  });
});
