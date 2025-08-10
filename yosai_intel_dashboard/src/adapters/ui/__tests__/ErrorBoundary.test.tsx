import React from 'react';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from '../components/ErrorBoundary';

function ProblemChild() {
  throw new Error('Test error');
  // eslint-disable-next-line no-unreachable
  return <div>Should not render</div>;
}

test('ErrorBoundary displays fallback on error', () => {
  render(
    <ErrorBoundary>
      <ProblemChild />
    </ErrorBoundary>,
  );
  expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
});
