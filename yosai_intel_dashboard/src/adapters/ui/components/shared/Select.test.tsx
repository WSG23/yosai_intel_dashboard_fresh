import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Select } from './Select';

const options = [
  { value: 'a', label: 'A' },
  { value: 'b', label: 'B' },
  { value: 'c', label: 'C' }
];

test('calls onChange when option clicked', async () => {
  const user = userEvent.setup();
  const onChange = jest.fn();
  render(<Select value="" onChange={onChange} options={options} />);
  await user.click(screen.getByText('A'));
  expect(onChange).toHaveBeenCalledWith('a');
});

test('supports keyboard navigation and selection', async () => {
  const user = userEvent.setup();
  const onChange = jest.fn();
  render(<Select value="" onChange={onChange} options={options} />);

  const listbox = screen.getByRole('listbox');
  listbox.focus();

  await user.keyboard('{ArrowDown}{ArrowDown}{Enter}');
  expect(onChange).toHaveBeenCalledWith('c');

  onChange.mockClear();
  await user.keyboard('{Home}{Enter}');
  expect(onChange).toHaveBeenCalledWith('a');

  onChange.mockClear();
  await user.keyboard('{End}{Enter}');
  expect(onChange).toHaveBeenCalledWith('c');

  onChange.mockClear();
  await user.keyboard('{ArrowUp}{Escape}{Enter}');
  expect(onChange).not.toHaveBeenCalled();
});

