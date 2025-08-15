import React from 'react';
import CenteredSpinner from './CenteredSpinner';

export interface LoadingErrorProps {
  loading: boolean;
  error?: Error | string | null;
  children: React.ReactNode;
}

const LoadingError: React.FC<LoadingErrorProps> = ({
  loading,
  error,
  children,
}) => {
  if (loading) {
    return <CenteredSpinner className="p-4" />;
  }
  if (error) {
    const message = typeof error === 'string' ? error : error?.message;
    return (
      <p role="alert" className="p-4 text-red-600">
        {message || 'An unexpected error occurred.'}
      </p>
    );
  }
  return <>{children}</>;
};

export default LoadingError;
