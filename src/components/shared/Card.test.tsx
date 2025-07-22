import { render, screen } from '@testing-library/react';
import { Card } from './Card';

test('renders card children', () => {
  render(<Card>inside</Card>);
  expect(screen.getByText('inside')).toBeInTheDocument();
});
