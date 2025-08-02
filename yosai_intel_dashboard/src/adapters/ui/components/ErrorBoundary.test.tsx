import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

// Silence expected console errors in tests
beforeEach(() => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
  global.fetch = jest.fn().mockResolvedValue({ ok: true });
});

afterEach(() => {
  (console.error as jest.Mock).mockRestore();
  (global.fetch as jest.Mock).mockClear();
});

test('renders children when no error', () => {
  render(
    <ErrorBoundary>
      <div>content</div>
    </ErrorBoundary>
  );
  expect(screen.getByText('content')).toBeInTheDocument();
});

test('shows fallback UI and posts error report', () => {
  const ThrowError = () => {
    throw new Error('boom');
  };

  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );

  expect(screen.getByText('Something went wrong.')).toBeInTheDocument();
  expect(screen.getByText('Retry')).toBeInTheDocument();
  expect(screen.getByText('Report Issue')).toBeInTheDocument();
  expect(global.fetch).toHaveBeenCalledWith('/api/error-report', expect.any(Object));
});

test('includes user comments when reporting issue', () => {
  const ThrowError = () => {
    throw new Error('boom');
  };

  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );

  const originalPrompt = window.prompt;
  (window as any).prompt = jest.fn().mockReturnValue('It failed after clicking');
  fireEvent.click(screen.getByText('Report Issue'));

  expect((window as any).prompt).toHaveBeenCalled();
  expect(global.fetch).toHaveBeenCalledTimes(2);
  const payload = JSON.parse((global.fetch as jest.Mock).mock.calls[1][1].body);
  expect(payload.comments).toBe('It failed after clicking');
  window.prompt = originalPrompt;
});

test('retry resets error boundary', () => {
  let shouldThrow = true;
  const ProblemChild = () => {
    if (shouldThrow) throw new Error('fail');
    return <div>safe</div>;
  };

  render(
    <ErrorBoundary>
      <ProblemChild />
    </ErrorBoundary>
  );

  expect(screen.getByText('Something went wrong.')).toBeInTheDocument();
  shouldThrow = false;
  fireEvent.click(screen.getByText('Retry'));
  expect(screen.getByText('safe')).toBeInTheDocument();
});

test('displays error details in development mode', () => {
  const prevEnv = process.env.NODE_ENV;
  process.env.NODE_ENV = 'development';
  const ThrowError = () => {
    throw new Error('dev boom');
  };

  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );

  expect(screen.getByText(/dev boom/)).toBeInTheDocument();
  process.env.NODE_ENV = prevEnv;
});
