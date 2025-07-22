import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './button';

test('handles click', () => {
  const onClick = jest.fn();
  render(<Button onClick={onClick}>click</Button>);
  fireEvent.click(screen.getByText('click'));
  expect(onClick).toHaveBeenCalled();
});
