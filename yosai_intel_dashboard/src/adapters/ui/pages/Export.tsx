import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { ChunkGroup } from '../components/layout';
import ExportForm from '../components/export/ExportForm';

const Export: React.FC = () => {
  return (
    <ChunkGroup className="page-container space-y-4">
      <h1>Export Data</h1>
      <ExportForm />
    </ChunkGroup>
  );
};

const ExportPage: React.FC = () => (
  <ErrorBoundary>
    <Export />
  </ErrorBoundary>
);

export default ExportPage;
