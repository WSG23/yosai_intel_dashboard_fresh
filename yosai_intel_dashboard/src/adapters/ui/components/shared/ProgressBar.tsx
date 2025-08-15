import React from 'react';

interface Props {
  /** Current progress as a number between 0 and 100 */
  progress: number;
  /** Optional class names applied to the outer progress element */
  className?: string;
  /** Accessible label describing the progress bar */
  ariaLabel?: string;
}

export const ProgressBar: React.FC<Props> = ({
  progress,
  className = '',
  ariaLabel = 'progress'
}) => {
  return (
    <div
      className={`w-full bg-gray-200 rounded-full h-2 ${className}`}
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={ariaLabel}
    >
      <div
        className="bg-blue-600 h-2 rounded-full"
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      />
    </div>
  );
};
