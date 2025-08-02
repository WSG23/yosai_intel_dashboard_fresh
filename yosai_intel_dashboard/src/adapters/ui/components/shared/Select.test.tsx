import { render, screen, fireEvent } from '@testing-library/react';
import { Select, Option } from './Select';

const options: Option<string>[] = [
  { value: 'a', label: 'A' },
  { value: 'b', label: 'B' }
];

test('calls onChange with selected value', () => {
  const onChange = jest.fn();
  render(<Select<string> value="" onChange={onChange} options={options} />);
  fireEvent.change(screen.getByRole('combobox'), { target: { value: 'a' } });
  expect(onChange).toHaveBeenCalledWith('a');
});
