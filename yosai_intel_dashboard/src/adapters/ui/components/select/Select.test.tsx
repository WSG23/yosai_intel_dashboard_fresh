import { render, screen, fireEvent } from '@testing-library/react';
import { Select } from './Select';

const options = [
  { value: 'a', label: 'A' },
  { value: 'b', label: 'B' }
];

test('calls onChange with selected value', () => {
  const onChange = jest.fn();
  render(<Select value="" onChange={onChange} options={options} />);
  const input = screen.getByRole('combobox');
  fireEvent.focus(input);
  const option = screen.getByRole('option', { name: 'A' });
  fireEvent.mouseDown(option);
  expect(onChange).toHaveBeenCalledWith('a');
});

test('handles multiple selection', () => {
  const onChange = jest.fn();
  render(<Select value={[]} onChange={onChange} options={options} multiple />);
  const input = screen.getByRole('combobox');
  fireEvent.focus(input);
  fireEvent.mouseDown(screen.getByRole('option', { name: 'A' }));
  fireEvent.mouseDown(screen.getByRole('option', { name: 'B' }));
  expect(onChange).toHaveBeenLastCalledWith(['a', 'b']);
});

test('manages aria attributes', () => {
  render(<Select value="" onChange={() => {}} options={options} />);
  const input = screen.getByRole('combobox');
  expect(input).toHaveAttribute('aria-expanded', 'false');
  fireEvent.focus(input);
  const listbox = screen.getByRole('listbox');
  expect(input).toHaveAttribute('aria-controls', listbox.id);
  fireEvent.keyDown(input, { key: 'ArrowDown' });
  const firstOption = screen.getByRole('option', { name: 'A' });
  expect(input).toHaveAttribute('aria-activedescendant', firstOption.id);
});

test('sets aria-multiselectable when multiple', () => {
  render(<Select value={[]} onChange={() => {}} options={options} multiple />);
  const input = screen.getByRole('combobox');
  fireEvent.focus(input);
  const listbox = screen.getByRole('listbox');
  expect(listbox).toHaveAttribute('aria-multiselectable', 'true');
});

test('announces number of results', () => {
  render(<Select value="" onChange={() => {}} options={options} />);
  const status = screen.getByRole('status');
  expect(status).toHaveTextContent('2 results available');
  const input = screen.getByRole('combobox');
  fireEvent.change(input, { target: { value: 'A' } });
  expect(status).toHaveTextContent('1 results available');
});
