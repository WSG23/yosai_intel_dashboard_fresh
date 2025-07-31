import { renderHook, act } from '@testing-library/react';
import { useFileParser } from './useFileParser';

const csvContent = 'device_id,name\n1,Door1';
const jsonContent = JSON.stringify([{ device: 'd1', name: 'Door1' }]);

describe('useFileParser', () => {
  it('parses csv', async () => {
    const file = new File([csvContent], 'test.csv', { type: 'text/csv' });
    const { result } = renderHook(() => useFileParser());
    let data: any;
    await act(async () => { data = await result.current.parseFile(file); });
    expect(data.columns).toContain('device_id');
    expect(data.rows.length).toBe(1);
  });

  it('parses json', async () => {
    const file = new File([jsonContent], 'test.json', { type: 'application/json' });
    const { result } = renderHook(() => useFileParser());
    let data: any;
    await act(async () => { data = await result.current.parseFile(file); });
    expect(data.rows.length).toBe(1);
  });
});
