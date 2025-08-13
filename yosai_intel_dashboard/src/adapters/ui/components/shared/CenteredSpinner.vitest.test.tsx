import { render } from '@testing-library/react';
import CenteredSpinner from './CenteredSpinner';

test('centers the spinner and forwards size', () => {
  const { container } = render(<CenteredSpinner sizeClass="h-4 w-4" />);
  expect(container.firstChild).toHaveClass('flex items-center justify-center');
  const spinner = container.querySelector('div > div > div');
  expect(spinner).toHaveClass('h-4 w-4');
});
