import React from 'react';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';
import { log } from './logger';

jest.mock('./logger', () => ({ log: jest.fn() }));

describe('ErrorBoundary', () => {
  test('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>child</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('child')).toBeInTheDocument();
  });

  test('shows fallback and logs when child throws', () => {
    const ConsoleError = jest.spyOn(console, 'error').mockImplementation(() => {});

    const Boom = () => {
      throw new Error('boom');
    };
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(log).toHaveBeenCalledWith(
      'error',
      'render error',
      expect.objectContaining({ error: 'boom' })
    );
    ConsoleError.mockRestore();
  });
});
