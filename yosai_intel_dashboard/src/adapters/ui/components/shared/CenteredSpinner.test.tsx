import { render } from '@testing-library/react';
import CenteredSpinner from './CenteredSpinner';

test('centers the spinner', () => {
  const { container } = render(<CenteredSpinner />);
  expect(container.firstChild).toHaveClass('flex items-center justify-center');
});
