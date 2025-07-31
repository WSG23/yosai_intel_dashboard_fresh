import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { Upload as UploadComponent } from '../components/upload';
import { UploadProvider } from '../state/uploadContext';

const UploadPage: React.FC = () => (
  <ErrorBoundary>
    <UploadProvider>
      <UploadComponent />
    </UploadProvider>
  </ErrorBoundary>
);

export default UploadPage;
