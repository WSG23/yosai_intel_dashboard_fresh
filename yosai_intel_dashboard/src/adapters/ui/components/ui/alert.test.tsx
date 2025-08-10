import { render, screen } from '@testing-library/react';
import { Alert, AlertDescription } from './alert';

test('renders alert description', () => {
  render(
    <Alert>
      <AlertDescription>text</AlertDescription>
    </Alert>
  );
  expect(screen.getByText('text')).toBeInTheDocument();
  const alert = screen.getByRole('alert');
  expect(alert).toHaveAttribute('aria-live', 'assertive');
});
