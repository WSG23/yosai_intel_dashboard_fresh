import React from 'react';
import { Alert, AlertDescription } from './ui/alert';
import { Button } from './ui/button';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * Generic React error boundary that displays a fallback UI and reports
 * errors to the backend for further inspection.
 */
class ErrorBoundary extends React.Component<
  React.PropsWithChildren<unknown>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<unknown>) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
    this.handleRetry = this.handleRetry.bind(this);
    this.handleReport = this.handleReport.bind(this);
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error, errorInfo: null };
  }

  private reportError(error: Error, info: React.ErrorInfo) {
    fetch('/api/error-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: error.message,
        stack: error.stack,
        componentStack: info.componentStack,
      }),
    }).catch((err) => console.error('Failed to report error', err));
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    this.setState({ errorInfo: info });
    this.reportError(error, info);
    console.error('ErrorBoundary caught an error', error, info);
  }

  handleRetry() {
    this.setState({ hasError: false, error: null, errorInfo: null });
  }

  handleReport() {
    const { error, errorInfo } = this.state;
    if (!error) return;
    const comments = window.prompt('Please describe what happened (optional):') || '';
    fetch('/api/error-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo?.componentStack,
        comments
      })
    }).catch((err) => console.error('Failed to report error', err));
  }

  render() {
    const { hasError, error, errorInfo } = this.state;
    if (hasError) {
      return (
        <Alert className="bg-red-50 border-red-200 text-red-800">
          <AlertDescription>
            <p className="font-medium">Something went wrong.</p>
            {process.env.NODE_ENV === 'development' && error && (
              <pre className="mt-2 whitespace-pre-wrap text-sm">{error.stack}</pre>
            )}
            {process.env.NODE_ENV === 'development' && errorInfo && (
              <pre className="mt-2 whitespace-pre-wrap text-xs">{errorInfo.componentStack}</pre>
            )}
            <div className="mt-4 flex gap-2">
              <Button onClick={this.handleRetry}>Retry</Button>
              <Button variant="outline" onClick={this.handleReport}>Report Issue</Button>
            </div>
          </AlertDescription>
        </Alert>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
