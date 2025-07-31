import { parseCSV } from './pages/Upload';

describe('parseCSV', () => {
  it('handles quoted commas and newlines', () => {
    const content = 'Name,Note\n"Doe, John","Hello"\n"Jane","Multi\nLine"';
    const result = parseCSV(content);
    expect(result.columns).toEqual(['Name', 'Note']);
    expect(result.rows.length).toBe(2);
    expect(result.rows[0]['Name']).toBe('Doe, John');
    expect(result.rows[1]['Note']).toBe('Multi\nLine');
  });
});
