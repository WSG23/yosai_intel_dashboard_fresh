import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { ChunkGroup } from '../components/layout';
import ExportForm from '../components/Export/ExportForm';
import { useExportData } from '../hooks';

const Export: React.FC = () => {
  const { startExport, progress, status, cancelExport } = useExportData();

  return (
    <ChunkGroup className="page-container">
      <h1 className="mb-4 flex items-center space-x-2">
        <Download />
        <span>Export Data</span>
      </h1>
      <ExportForm
        onExport={startExport}
        progress={progress}
        status={status}
        onCancel={cancelExport}
      />
    </ChunkGroup>
  );
};

const ExportPage: React.FC = () => (
  <ErrorBoundary>
    <Export />
  </ErrorBoundary>
);

export default ExportPage;
