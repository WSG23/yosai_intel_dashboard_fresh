import { render, screen } from '@testing-library/react';
import { Alert, AlertDescription } from './Alert';

test('renders alert description', () => {
  render(
    <Alert>
      <AlertDescription>text</AlertDescription>
    </Alert>
  );
  expect(screen.getByText('text')).toBeInTheDocument();
});
