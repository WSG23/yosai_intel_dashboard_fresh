import { render, screen } from '@testing-library/react';
import { Badge } from './Badge';

test('renders badge text', () => {
  render(<Badge>hello</Badge>);
  expect(screen.getByText('hello')).toBeInTheDocument();
});
