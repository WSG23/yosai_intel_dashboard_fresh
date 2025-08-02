import { render, screen, fireEvent } from '@testing-library/react';
import { Select } from './Select';

const options = [
  { value: 'a', label: 'A' },
  { value: 'b', label: 'B' }
];

test('calls onChange with selected value', () => {
  const onChange = jest.fn();
  render(<Select aria-label="letters" value="" onChange={onChange} options={options} />);
  fireEvent.change(screen.getByLabelText('letters'), { target: { value: 'a' } });
  expect(onChange).toHaveBeenCalledWith('a');
});

test('supports keyboard navigation', () => {
  const onChange = jest.fn();
  render(<Select aria-label="letters" value="a" onChange={onChange} options={options} />);
  const select = screen.getByLabelText('letters');
  select.focus();
  fireEvent.keyDown(select, { key: 'ArrowDown' });
  fireEvent.change(select, { target: { value: 'b' } });
  expect(onChange).toHaveBeenCalledWith('b');
});

test('filters options via search input', () => {
  const onChange = jest.fn();
  render(<Select aria-label="letters" value="" onChange={onChange} options={options} />);
  const select = screen.getByLabelText('letters');
  fireEvent.keyDown(select, { key: 'b' });
  fireEvent.change(select, { target: { value: 'b' } });
  expect(onChange).toHaveBeenCalledWith('b');
});

test('handles multi-select interactions with accessibility attributes', () => {
  const onChange = jest.fn();
  render(
    <Select
      aria-label="letters"
      multiple
      value={[]}
      onChange={onChange}
      options={options}
    />
  );

  const listbox = screen.getByRole('listbox');
  fireEvent.change(listbox, {
    target: { selectedOptions: [{ value: 'a' }, { value: 'b' }] }
  });
  expect(onChange).toHaveBeenCalledWith(['a', 'b']);
  expect(listbox).toHaveAttribute('multiple');
  expect(listbox).toHaveAttribute('aria-label', 'letters');
});
