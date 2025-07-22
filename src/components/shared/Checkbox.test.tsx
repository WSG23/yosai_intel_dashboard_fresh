import { render, screen, fireEvent } from '@testing-library/react';
import { Checkbox } from './Checkbox';

test('calls onChange when toggled', () => {
  const onChange = jest.fn();
  render(<Checkbox label="check" checked={false} onChange={onChange} />);
  fireEvent.click(screen.getByLabelText('check'));
  expect(onChange).toHaveBeenCalledWith(true);
});
