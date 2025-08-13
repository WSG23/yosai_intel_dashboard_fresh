import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { Button } from './button.native';

it('calls onPress when pressed', () => {
  const handlePress = vi.fn();
  render(<Button onPress={handlePress}>Press me</Button>);
  fireEvent.click(screen.getByText('Press me'));
  expect(handlePress).toHaveBeenCalled();
});
