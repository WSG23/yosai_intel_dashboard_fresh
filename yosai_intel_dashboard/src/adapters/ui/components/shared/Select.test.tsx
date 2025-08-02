import { render, screen, fireEvent } from '@testing-library/react';
import { Select } from './Select';

const options = [
  { value: 'a', label: 'A' },
  { value: 'b', label: 'B' }
];

test('calls onChange with selected value and manages aria attributes', () => {
  const onChange = jest.fn();
  render(<Select id="test" value="" onChange={onChange} options={options} placeholder="pick" />);
  const select = screen.getByRole('combobox');

  // aria-expanded toggles on focus/blur
  expect(select).toHaveAttribute('aria-expanded', 'false');
  fireEvent.focus(select);
  expect(select).toHaveAttribute('aria-expanded', 'true');

  fireEvent.change(select, { target: { value: 'a' } });
  expect(onChange).toHaveBeenCalledWith('a');
  expect(select).toHaveAttribute('aria-activedescendant', 'test-option-a');

  fireEvent.blur(select);
  expect(select).toHaveAttribute('aria-expanded', 'false');
});

test('applies listbox role and aria-multiselectable for multiple select', () => {
  const onChange = jest.fn();
  render(<Select id="multi" value={[]} onChange={onChange} options={options} multiple />);
  const listbox = screen.getByRole('listbox');
  expect(listbox).toHaveAttribute('aria-multiselectable', 'true');
  expect(screen.getAllByRole('option')).toHaveLength(options.length);
});
