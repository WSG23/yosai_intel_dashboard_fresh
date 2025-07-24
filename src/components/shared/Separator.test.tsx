import { render } from '@testing-library/react';
import { Separator } from './Separator';

test('renders separator element', () => {
  const { container } = render(<Separator />);
  expect(container.querySelector('hr')).toBeInTheDocument();
});
