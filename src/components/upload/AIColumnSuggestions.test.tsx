import { render, screen } from '@testing-library/react';
import AIColumnSuggestions from './AIColumnSuggestions';
import { ParsedData } from '../../hooks/useFileParser';

test('lists columns', () => {
  const data: ParsedData = { rows: [], columns: ['a', 'b'], devices: [] };
  render(<AIColumnSuggestions data={data} />);
  expect(screen.getByText('a')).toBeInTheDocument();
  expect(screen.getByText('b')).toBeInTheDocument();
});
