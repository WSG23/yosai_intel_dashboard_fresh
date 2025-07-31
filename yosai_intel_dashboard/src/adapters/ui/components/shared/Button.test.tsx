import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

test('fires click handler', () => {
  const onClick = jest.fn();
  render(<Button onClick={onClick}>btn</Button>);
  fireEvent.click(screen.getByText('btn'));
  expect(onClick).toHaveBeenCalled();
});
