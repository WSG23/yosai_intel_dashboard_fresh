import { api, ApiHeaders } from './client';

export interface UserSettings {
  theme: string;
  itemsPerPage: number;
}

export const settingsAPI = {
  async get(signal?: AbortSignal): Promise<UserSettings> {
    return api.get<UserSettings>('/settings', { signal });
  },
  async update(settings: UserSettings, headers?: ApiHeaders): Promise<void> {
    await api.patch('/settings', settings, { headers });
  },
};

export default settingsAPI;
