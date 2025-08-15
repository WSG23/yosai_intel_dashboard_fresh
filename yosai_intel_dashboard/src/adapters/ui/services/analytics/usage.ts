import { fetchJson } from '../../utils/fetchJson';

interface TipInteraction {
  id: string;
  action: 'view' | 'click';
  context?: string;
}

export const logTipInteraction = async (
  interaction: TipInteraction,
): Promise<void> => {
  try {
    await fetchJson('/api/analytics/tip', {
      method: 'POST',
      body: JSON.stringify({ ...interaction, timestamp: Date.now() }),
    });
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Failed to log tip interaction', err);
  }
};

export const getLearningSuggestions = async (): Promise<string[]> => {
  try {
    return await fetchJson<string[]>('/api/analytics/suggestions');
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Failed to fetch learning suggestions', err);
    return [];
  }
};
