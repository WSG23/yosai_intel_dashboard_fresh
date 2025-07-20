import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardHeader, CardBody } from 'reactstrap';
import { useFileParser } from '../hooks/useFileParser';
import { UploadProvider, useUploadContext } from '../state/uploadContext';
import { ColumnMappingModal, DeviceMappingModal, ProgressIndicator, AIColumnSuggestions } from '../components/upload';

const UploadInner: React.FC = () => {
  const { parseFile } = useFileParser();
  const { files, setFiles } = useUploadContext();
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const onDrop = async (accepted: File[]) => {
    for (const file of accepted) {
      setMessage(`Parsing ${file.name}`);
      const data = await parseFile(file);
      setFiles(prev => [...prev, { file, data }]);
      setProgress(100);
    }
  };
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });
  return (
    <div>
      <div {...getRootProps()} className="upload-dropzone" style={{border:'2px dashed #007bff', padding:'2rem'}}>
        <input {...getInputProps()} />
        {isDragActive ? 'Drop files here' : 'Drag files here or click'}
      </div>
      {progress > 0 && <ProgressIndicator progress={progress} message={message} />}
      {files.map(({ file, data }) => (
        <div key={file.name} className="mt-3">
          <strong>{file.name}</strong>
          <AIColumnSuggestions data={data || null} />
        </div>
      ))}
      <ColumnMappingModal isOpen={false} onClose={() => {}} fileData={{}} onConfirm={() => {}} />
      <DeviceMappingModal isOpen={false} onClose={() => {}} devices={[]} filename="" onConfirm={() => {}} />
    </div>
  );
};

const UploadPage: React.FC = () => (
  <UploadProvider>
    <Card>
      <CardHeader>
        <h5>Upload Data Files</h5>
      </CardHeader>
      <CardBody>
        <UploadInner />
      </CardBody>
    </Card>
  </UploadProvider>
);

export default UploadPage;
