import { render, screen, fireEvent } from '@testing-library/react';
import { Select } from '../select/Select';

const options = [{ value: '1', label: 'One' }];

test('renders accessible combobox', () => {
  render(<Select value="" onChange={() => {}} options={options} />);
  const input = screen.getByRole('combobox');
  fireEvent.focus(input);
  const listbox = screen.getByRole('listbox');
  expect(input).toHaveAttribute('aria-controls', listbox.id);
  expect(screen.getAllByRole('option')).toHaveLength(1);
});
