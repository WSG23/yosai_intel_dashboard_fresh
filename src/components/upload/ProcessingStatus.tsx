import React from 'react';
import './ProcessingStatus.css';

interface ProcessingStatusProps {
  message: string;
  progress: number;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ message, progress }) => {
  return (
    <div className="processing-status-overlay">
      <div className="processing-status-modal">
        <h3>Processing Files</h3>
        <p>{message}</p>
        <div className="processing-progress">
          <div className="progress-bar-large">
            <div 
              className="progress-fill-large"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="progress-text">{progress}%</span>
        </div>
      </div>
    </div>
  );
};

export default ProcessingStatus;
