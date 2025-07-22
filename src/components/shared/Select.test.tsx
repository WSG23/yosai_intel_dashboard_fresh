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
