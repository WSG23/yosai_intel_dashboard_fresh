import React from 'react';

interface Props {
  progress: number; // 0-100
  className?: string;
}

export const ProgressBar: React.FC<Props> = ({ progress, className = '' }) => {
  return (
    <div
      className={`w-full bg-gray-200 rounded-full h-2 ${className}`}
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="bg-blue-600 h-2 rounded-full"
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      />
    </div>
  );
};
