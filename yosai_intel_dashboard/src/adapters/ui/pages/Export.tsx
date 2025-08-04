import React from 'react';
import { Download } from 'lucide-react';
import ErrorBoundary from '../components/ErrorBoundary';
import { ChunkGroup } from '../components/layout';

const Export: React.FC = () => {
  return (
    <ChunkGroup className="page-container">
      <h1>Export Data</h1>
      <p>Export functionality coming soon...</p>
    </ChunkGroup>
  );
};

const ExportPage: React.FC = () => (
  <ErrorBoundary>
    <Export />
  </ErrorBoundary>
);

export default ExportPage;
