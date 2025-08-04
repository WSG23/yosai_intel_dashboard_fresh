import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { Upload as UploadComponent } from '../components/upload';
import { UploadProvider } from '../state/uploadContext';
import { TaskLauncher, Wizard } from '../components/interaction';

const UploadPage: React.FC = () => {
  const steps = [
    { title: 'Upload', content: <UploadComponent /> },
    {
      title: 'Review',
      content: <div>Please review your upload before submitting.</div>,
    },
  ];

  return (
    <ErrorBoundary>
      <TaskLauncher />
      <UploadProvider>
        <Wizard steps={steps} storageKey="upload-wizard-step" />
      </UploadProvider>
    </ErrorBoundary>
  );
};


export default UploadPage;
