import { render } from '@testing-library/react';
import Spinner from './Spinner';

test('renders spinner element', () => {
  const { container } = render(<Spinner />);
  expect(container.firstChild).toHaveClass('animate-spin');
});
