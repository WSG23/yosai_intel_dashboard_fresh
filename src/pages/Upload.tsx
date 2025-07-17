import React, { useState, useCallback } from 'react';
import { Upload as UploadIcon, FileText, AlertCircle, CheckCircle, X } from 'lucide-react';
import './Upload.css';
import SimpleModal from '../components/upload/SimpleModal';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'processing' | 'mapping' | 'completed' | 'error';
  progress: number;
  error?: string;
  columns?: string[];
  mappedColumns?: Record<string, string>;
  devices?: string[];
  mappedDevices?: Record<string, string>;
}

const Upload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string>('');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null);
  const [columnMappings, setColumnMappings] = useState<Record<string, string>>({});
  const [deviceModalOpen, setDeviceModalOpen] = useState(false);
  const [deviceMappings, setDeviceMappings] = useState<Record<string, string>>({});

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = async (fileList: File[]) => {
    const validFiles = fileList.filter(file => {
      const validTypes = ['.csv', '.xlsx', '.xls', '.json', '.log'];
      return validTypes.some(type => file.name.toLowerCase().endsWith(type));
    });

    if (validFiles.length === 0) {
      alert('Please upload valid file types: CSV, Excel, JSON, or LOG files');
      return;
    }

    const newFiles: UploadedFile[] = validFiles.map(file => ({
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: file.name,
      size: file.size,
      type: file.type || 'application/octet-stream',
      status: 'pending',
      progress: 0
    }));

    setFiles(prev => [...prev, ...newFiles]);

    for (const file of validFiles) {
      await uploadFile(file, newFiles.find(f => f.name === file.name)!.id);
    }
  };

  const uploadFile = async (file: File, fileId: string) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      console.log('Starting upload for:', file.name);
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: 'processing', progress: 25 } : f
      ));

      const response = await fetch('http://localhost:5001/api/v1/upload', {
        method: 'POST',
        body: formData
      });

      console.log('Response received:', response.status);

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
        console.log('AI Column Suggestions received:', data.suggestions);
      console.log('Response data:', data);

      setFiles(prev => prev.map(f => 
        f.id === fileId ? { 
          ...f, 
          status: 'completed',
          progress: 100,
          columns: data.columns || [],
          devices: data.detected_devices || []
        } : f
      ));

      setUploadMessage(`Upload successful! File: ${file.name}`);
      setTimeout(() => setUploadMessage(''), 3000);

    } catch (error) {
      console.error('Upload error:', error);
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { 
          ...f, 
          status: 'error',
          error: error instanceof Error ? error.message : 'Upload failed'
        } : f
      ));
    }
  };

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h1>Upload Security Data</h1>
        <p>Upload CSV, Excel, JSON, or LOG files for analysis</p>
      </div>

      <div
        className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          className="file-input"
          multiple
          accept=".csv,.xlsx,.xls,.json,.log"
          onChange={handleFileInput}
        />
        <label htmlFor="file-input" className="dropzone-content">
          <UploadIcon size={48} className="upload-icon" />
          <p className="dropzone-text">
            Drag and drop files here or click to browse
          </p>
          <p className="dropzone-subtext">
            Supports CSV, Excel, JSON, and LOG files
          </p>
        </label>
      </div>

      {uploadMessage && (
        <div style={{
          background: 'green',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          margin: '20px 0',
          textAlign: 'center'
        }}>
          {uploadMessage}
        </div>
      )}

      {files.length > 0 && (
        <div className="files-list">
          <h2>Uploaded Files</h2>
          {files.map(file => (
            <div key={file.id} className={`file-item ${file.status}`}>
              <div className="file-info">
                <FileText size={20} className="file-icon" />
                <div className="file-details">
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
              </div>
              
              <div className="file-status">
                {file.status === 'pending' && (
                  <span className="status-text">Waiting...</span>
                )}
                {file.status === 'processing' && (
                  <span className="status-text">Uploading...</span>
                )}
                {file.status === 'completed' && (
                  <>
                    <CheckCircle size={20} className="success-icon" />
                    <span className="status-text">Completed</span>
                  </>
                )}
                {file.status === 'error' && (
                  <>
                    <AlertCircle size={20} className="error-icon" />
                    <span className="status-text">{file.error}</span>
                  </>
                )}
              </div>

              <div className="file-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ width: `${file.progress}%` }}
                  />
                </div>
              </div>

              <button
                className="remove-button"
                onClick={() => removeFile(file.id)}
                aria-label="Remove file"
              >
                <X size={16} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* File Info Section for Completed Uploads */}
      {files.filter(f => f.status === 'completed').length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h2>Uploaded File Details</h2>
          {files.filter(f => f.status === 'completed').map(file => (
            <div key={`info-${file.id}`} style={{
              background: '#1e293b',
              border: '1px solid #334155',
              padding: '15px',
              margin: '10px 0',
              borderRadius: '5px'
            }}>
              <h3 style={{ color: '#f1f5f9', marginBottom: '10px' }}>File: {file.name}</h3>
              <p style={{ color: '#94a3b8' }}>Columns detected: {file.columns?.join(', ') || 'None'}</p>
              <p style={{ color: '#94a3b8' }}>Devices detected: {file.devices?.join(', ') || 'None'}</p>
              <div style={{ marginTop: '10px' }}>
                <button 
                  onClick={() => {
                    console.log('Opening modal for:', file);
                    setSelectedFile(file);
                    setModalOpen(true);
                  }}
                  style={{
                    background: '#3b82f6',
                    color: 'white',
                    padding: '8px 16px',
                    border: 'none',
                    borderRadius: '4px',
                    margin: '5px',
                    cursor: 'pointer'
                  }}
                >
                  Map Columns
                </button>
                <button 
                  onClick={() => {
                    console.log('Device mapping for:', file);
                    alert(`Device mapping would open for ${file.name}\nDevices: ${file.devices?.join(', ')}`);
                  }}
                  style={{
                    background: '#22c55e',
                    color: 'white',
                    padding: '8px 16px',
                    border: 'none',
                    borderRadius: '4px',
                    margin: '5px',
                    cursor: 'pointer'
                  }}
                >
                  Map Devices
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      <SimpleModal 
        isOpen={modalOpen} 
        onClose={() => {
          setModalOpen(false);
          setSelectedFile(null);
        }}
        title={selectedFile ? `Map Columns for ${selectedFile.name}` : 'Map Columns'}
      >
        {selectedFile && (
          <div>
            <p style={{ marginBottom: '20px' }}>Map the columns from your file to standard fields:</p>
            
            {selectedFile.columns?.map((col, idx) => (
              <div key={idx} style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', color: '#94a3b8' }}>
                  {col}
                </label>
                <select
                  value={columnMappings[col] || ''}
                  onChange={(e) => setColumnMappings({
                    ...columnMappings,
                    [col]: e.target.value
                  })}
                  style={{
                    width: '100%',
                    padding: '8px',
                    borderRadius: '4px',
                    border: '1px solid #334155',
                    background: '#0f172a',
                    color: '#f1f5f9'
                  }}
                >
                  <option value="">-- Select mapping --</option>
                  <option value="timestamp">Timestamp</option>
                  <option value="source_ip">Source IP</option>
                  <option value="dest_ip">Destination IP</option>
                  <option value="action">Action</option>
                  <option value="protocol">Protocol</option>
                  <option value="port">Port</option>
                  <option value="device">Device</option>
                  <option value="user">User</option>
                  <option value="message">Message</option>
                  <option value="severity">Severity</option>
                </select>
              </div>
            ))}
            
            <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
              <button 
                onClick={() => {
                  console.log('Saving mappings:', columnMappings);
                  if (selectedFile) {
                    setFiles(prev => prev.map(f => 
                      f.id === selectedFile.id 
                        ? { ...f, mappedColumns: columnMappings }
                        : f
                    ));
                  }
                  setModalOpen(false);
                  setColumnMappings({});
                  setDeviceModalOpen(true);
                }}
                style={{
                  background: '#3b82f6',
                  color: 'white',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Save Mappings
              </button>
              <button 
                onClick={() => {
                  setModalOpen(false);
                  setColumnMappings({});
                }}
                style={{
                  background: '#6b7280',
                  color: 'white',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </SimpleModal>

      {/* Device Mapping Modal */}
      <SimpleModal 
        isOpen={deviceModalOpen} 
        onClose={() => {
          setDeviceModalOpen(false);
          setDeviceMappings({});
        }}
        title={selectedFile ? `Map Devices for ${selectedFile.name}` : 'Map Devices'}
      >
        {selectedFile && selectedFile.devices && (
          <div>
            <p style={{ marginBottom: '20px' }}>Map the devices found in your file:</p>
            
            {selectedFile.devices.length > 0 ? (
              selectedFile.devices.map((device, idx) => (
                <div key={idx} style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', color: '#94a3b8' }}>
                    {device}
                  </label>
                  <input
                    type="text"
                    value={deviceMappings[device] || ''}
                    onChange={(e) => setDeviceMappings({
                      ...deviceMappings,
                      [device]: e.target.value
                    })}
                    placeholder="Enter device name or description"
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '4px',
                      border: '1px solid #334155',
                      background: '#0f172a',
                      color: '#f1f5f9'
                    }}
                  />
                </div>
              ))
            ) : (
              <p style={{ color: '#94a3b8' }}>No devices detected. You can skip this step.</p>
            )}
            
            <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
              <button 
                onClick={async () => {
                  console.log('Saving device mappings:', deviceMappings);
                  if (selectedFile) {
                    setFiles(prev => prev.map(f => 
                      f.id === selectedFile.id 
                        ? { ...f, mappedDevices: deviceMappings, status: 'completed' as const }
                        : f
                    ));
                    
                    // Send to backend
                    try {
                      const response = await fetch('http://localhost:5001/api/v1/process', {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                          fileId: selectedFile.id,
                          fileName: selectedFile.name,
                          columnMappings: selectedFile.mappedColumns || columnMappings,
                          deviceMappings: deviceMappings
                        })
                      });
                      
                      if (response.ok) {
                        alert('File processed successfully! In production, this would show results.');
                      }
                    } catch (error) {
                      console.error('Process error:', error);
                    }
                  }
                  setDeviceModalOpen(false);
                  setDeviceMappings({});
                  setSelectedFile(null);
                }}
                style={{
                  background: '#22c55e',
                  color: 'white',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Process File
              </button>
              <button 
                onClick={() => {
                  // Skip device mapping
                  if (selectedFile) {
                    setFiles(prev => prev.map(f => 
                      f.id === selectedFile.id 
                        ? { ...f, status: 'completed' as const }
                        : f
                    ));
                  }
                  setDeviceModalOpen(false);
                  setDeviceMappings({});
                }}
                style={{
                  background: '#6b7280',
                  color: 'white',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Skip
              </button>
            </div>
          </div>
        )}
      </SimpleModal>
    </div>
  );
};

export default Upload;
