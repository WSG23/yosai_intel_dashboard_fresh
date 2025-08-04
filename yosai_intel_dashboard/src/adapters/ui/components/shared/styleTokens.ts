export type Priority = 'low' | 'medium' | 'high' | 'critical';

export const priorityLevels: Priority[] = ['low', 'medium', 'high', 'critical'];

export const colorTokens: Record<Priority, string> = {
  low: '#16a34a', // green-600
  medium: '#facc15', // yellow-400
  high: '#fb923c', // orange-400
  critical: '#dc2626', // red-600
};

export const priorityColor = (priority: Priority): string => colorTokens[priority];
