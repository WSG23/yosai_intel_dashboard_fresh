import React from 'react';

interface Props {
  message: string;
  progress: number;
}

const ProgressIndicator: React.FC<Props> = ({ message, progress }) => (
  <div className="my-3">
    <div>{message}</div>
    <div className="progress">
      <div
        className="progress-bar"
        role="progressbar"
        style={{ width: `${progress}%` }}
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  </div>
);

export default ProgressIndicator;
