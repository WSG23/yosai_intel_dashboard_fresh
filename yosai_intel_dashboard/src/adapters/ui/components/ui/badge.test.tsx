import { render, screen } from '@testing-library/react';
import { Badge } from './badge';

test('renders badge content', () => {
  render(<Badge>label</Badge>);
  expect(screen.getByText('label')).toBeInTheDocument();
});
