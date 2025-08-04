import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { Upload as UploadComponent } from '../components/upload';
import { UploadProvider } from '../state/uploadContext';
import { ChunkGroup } from '../components/layout';

const UploadPage: React.FC = () => (
  <ErrorBoundary>
    <UploadProvider>
      <ChunkGroup>
        <UploadComponent />
      </ChunkGroup>
    </UploadProvider>
  </ErrorBoundary>
);

export default UploadPage;
