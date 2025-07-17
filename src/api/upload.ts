import { api } from './client';

export const uploadAPI = {
  async uploadFile(file: File): Promise<{ taskId: string; data: any }> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<{ task_id: string; data: any }>('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return { taskId: response.task_id, data: response.data };
  },

  async waitForProcessing(taskId: string): Promise<any> {
    return api.get(`/upload/status/${taskId}`);
  },

  async applyColumnMappings(filename: string, mappings: Record<string, string>): Promise<any> {
    return api.post(`/upload/${filename}/columns`, { mappings });
  },

  async saveDeviceMappings(filename: string, devices: Record<string, any>): Promise<any> {
    return api.post(`/upload/${filename}/devices`, { devices });
  },
};
