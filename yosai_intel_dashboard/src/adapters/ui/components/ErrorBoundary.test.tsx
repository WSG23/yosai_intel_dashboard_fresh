import { render, screen } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

test('renders children when no error', () => {
  render(
    <ErrorBoundary>
      <div>content</div>
    </ErrorBoundary>
  );
  expect(screen.getByText('content')).toBeInTheDocument();
});
