interface TipInteraction {
  id: string;
  action: 'view' | 'click';
  context?: string;
}

export const logTipInteraction = async (
  interaction: TipInteraction
): Promise<void> => {
  try {
    await fetch('/api/analytics/tip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...interaction, timestamp: Date.now() }),
    });
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Failed to log tip interaction', err);
  }
};

export const getLearningSuggestions = async (): Promise<string[]> => {
  try {
    const res = await fetch('/api/analytics/suggestions');
    if (!res.ok) {
      throw new Error('Network response was not ok');
    }
    return await res.json();
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Failed to fetch learning suggestions', err);
    return [];
  }
};
