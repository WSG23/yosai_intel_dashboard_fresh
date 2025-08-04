import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { Upload as UploadComponent } from '../components/upload';
import { UploadProvider } from '../state/uploadContext';
import { LongPressMenu } from '../components/interaction/ContextDisclosure';

const UploadPage: React.FC = () => (
  <ErrorBoundary>
    <UploadProvider>
      <LongPressMenu preview={<div>Hold to open upload</div>}>
        <UploadComponent />
      </LongPressMenu>
    </UploadProvider>
  </ErrorBoundary>
);

export default UploadPage;
