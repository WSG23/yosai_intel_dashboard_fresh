import { render, screen, fireEvent } from '@testing-library/react';
import { Select } from './Select';

const options = [
  { value: 'a', label: 'A' },
  { value: 'b', label: 'B' }
];

test('calls onChange with selected value', () => {
  const onChange = jest.fn();
  render(<Select value="" onChange={onChange} options={options} />);
  fireEvent.change(screen.getByRole('combobox'), { target: { value: 'a' } });
  expect(onChange).toHaveBeenCalledWith('a');
});

test('handles multiple selection', () => {
  const onChange = jest.fn();
  render(<Select value={[]} onChange={onChange} options={options} multiple />);
  const select = screen.getByRole('listbox');
  fireEvent.change(select, {
    target: { selectedOptions: [{ value: 'a' }, { value: 'b' }] }
  });
  expect(onChange).toHaveBeenCalledWith(['a', 'b']);
});

test('filters options and selects via keyboard', () => {
  const onChange = jest.fn();
  render(
    <Select value="" onChange={onChange} options={options} searchable placeholder="Search" />
  );
  const input = screen.getByRole('combobox');
  fireEvent.change(input, { target: { value: 'b' } });
  expect(screen.getByRole('option')).toHaveTextContent('B');
  fireEvent.keyDown(input, { key: 'ArrowDown' });
  fireEvent.keyDown(input, { key: 'Enter' });
  expect(onChange).toHaveBeenCalledWith('b');
});
