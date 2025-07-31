import React from 'react';

interface SpinnerProps {
  /** CSS size classes like 'h-6 w-6' */
  sizeClass?: string;
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ sizeClass = 'h-6 w-6', className = '' }) => (
  <div
    className={`animate-spin rounded-full border-2 border-b-transparent border-current ${sizeClass} ${className}`}
    role="status"
  />
);

export default Spinner;
