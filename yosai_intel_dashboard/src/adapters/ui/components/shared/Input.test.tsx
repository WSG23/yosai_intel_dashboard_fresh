import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from './Input';

test('updates value on change', () => {
  const onChange = jest.fn();
  render(<Input onChange={onChange} />);
  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'a' } });
  expect(onChange).toHaveBeenCalled();
});
