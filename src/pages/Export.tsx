import React from 'react';
import { Download } from 'lucide-react';
import ErrorBoundary from '../components/ErrorBoundary';

const Export: React.FC = () => {
  return (
    <div className="page-container">
      <h1>Export Data</h1>
      <p>Export functionality coming soon...</p>
    </div>
  );
};

const ExportPage: React.FC = () => (
  <ErrorBoundary>
    <Export />
  </ErrorBoundary>
);

export default ExportPage;
