import { render } from '@testing-library/react';
import { Separator } from './separator';

test('renders separator element', () => {
  const { container } = render(<Separator />);
  expect(container.querySelector('hr')).toBeInTheDocument();
});
