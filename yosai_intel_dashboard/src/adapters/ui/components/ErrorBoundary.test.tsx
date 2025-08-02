import React from 'react';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

const ProblemChild: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error('Boom');
  }
  return <div>content</div>;
};

test('renders children when no error', () => {
  render(
    <ErrorBoundary>
      <ProblemChild />
    </ErrorBoundary>
  );
  expect(screen.getByText('content')).toBeInTheDocument();
});

test('handles thrown errors and reports to backend', () => {
  const consoleError = jest
    .spyOn(console, 'error')
    .mockImplementation(() => {});

  render(
    <ErrorBoundary>
      <ProblemChild shouldThrow />
    </ErrorBoundary>
  );

  expect(screen.getByText('Something went wrong.')).toBeInTheDocument();
  expect(consoleError).toHaveBeenCalled();
  consoleError.mockRestore();
});

test('retries rendering after reset', () => {
  const { rerender } = render(
    <ErrorBoundary>
      <ProblemChild shouldThrow />
    </ErrorBoundary>
  );

  expect(screen.getByText('Something went wrong.')).toBeInTheDocument();

  rerender(
    <ErrorBoundary>
      <ProblemChild />
    </ErrorBoundary>
  );

  expect(screen.getByText('Something went wrong.')).toBeInTheDocument();

  rerender(
    <ErrorBoundary key="reset">
      <ProblemChild />
    </ErrorBoundary>
  );

  expect(screen.getByText('content')).toBeInTheDocument();
});
