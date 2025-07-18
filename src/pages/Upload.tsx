import React, { useState, useCallback, useEffect } from 'react';
import { Upload as UploadIcon, FileText, AlertCircle, CheckCircle, X } from 'lucide-react';
import SimpleModal from '../components/upload/SimpleModal';
import { saveColumnMappings, saveDeviceMappings } from '../api/upload';
import './Upload.css';

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
  aiSuggestions?: Record<string, any>;
}

const Upload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string>('');
  
  // Modal states
  const [modalOpen, setModalOpen] = useState(false);
  const [deviceModalOpen, setDeviceModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null);
  
  // Mapping states
  const [columnMappings, setColumnMappings] = useState<Record<string, string>>({});
  const [deviceMappings, setDeviceMappings] = useState<Record<string, string>>({});
  const [aiSuggestions, setAiSuggestions] = useState<Record<string, any>>({});

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
      console.log('Response data:', data);
      console.log('AI suggestions from upload:', data.ai_suggestions);

      setFiles(prev => prev.map(f => 
        f.id === fileId ? { 
          ...f, 
          status: 'completed',
          progress: 100,
          columns: data.columns || [],
          devices: data.detected_devices || [],
          aiSuggestions: data.ai_suggestions || {}
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

  // Open column mapping modal with AI suggestions
  const openColumnMapping = (file: UploadedFile) => {
    console.log('Opening column mapping for:', file);
    setSelectedFile(file);
    
    // Pre-fill mappings with AI suggestions from upload
    if (file.aiSuggestions) {
      const mappings: Record<string, string> = {};
      Object.entries(file.aiSuggestions).forEach(([col, suggestion]: [string, any]) => {
        if (suggestion.field) {
          mappings[col] = suggestion.field;
        }
      });
      console.log('Pre-filling with AI mappings:', mappings);
      setColumnMappings(mappings);
      setAiSuggestions(file.aiSuggestions);
    }
    
    setModalOpen(true);
  };

  // Save column mappings and open device modal
  const handleColumnMappingSave = async () => {
    if (!selectedFile) return;

    console.log('Saving column mappings:', columnMappings);
    setFiles(prev => prev.map(f =>
      f.id === selectedFile.id
        ? { ...f, mappedColumns: columnMappings }
        : f
    ));
    try {
      await saveColumnMappings(selectedFile.id, columnMappings);
      alert('Column mappings saved successfully!');
    } catch (error) {
      console.error('Error saving column mappings:', error);
      alert('Failed to save column mappings.');
    }

    setModalOpen(false);
    
    // Fetch device AI suggestions
    try {
      const response = await fetch('http://localhost:5001/api/v1/ai/suggest-devices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          devices: selectedFile.devices || [],
          filename: selectedFile.name 
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Device AI suggestions:', data.suggestions);
        
        // Pre-fill device mappings
        const devMappings: Record<string, string> = {};
        Object.entries(data.suggestions || {}).forEach(([device, info]: [string, any]) => {
          const parts = [];
          if (info.floor_number) parts.push(`Floor ${info.floor_number}`);
          if (info.is_entry) parts.push('Entry');
          if (info.is_exit) parts.push('Exit');
          if (info.is_elevator) parts.push('Elevator');
          if (info.is_stairwell) parts.push('Stairwell');
          parts.push(`Security: ${info.security_level || 5}/10`);
          devMappings[device] = parts.join(', ');
        });
        setDeviceMappings(devMappings);
      }
    } catch (error) {
      console.error('Error fetching device suggestions:', error);
    }
    
    setDeviceModalOpen(true);
  };

  // Process file with all mappings
  const handleDeviceMappingSave = async () => {
    if (!selectedFile) return;
    
    console.log('Saving device mappings:', deviceMappings);
    setFiles(prev => prev.map(f => 
      f.id === selectedFile.id 
        ? { ...f, mappedDevices: deviceMappings, status: 'completed' as const }
        : f
    ));
    
    try {
      // Process file
      const processResponse = await fetch('http://localhost:5001/api/v1/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fileId: selectedFile.id,
          fileName: selectedFile.name,
          columnMappings: selectedFile.mappedColumns || columnMappings,
          deviceMappings: deviceMappings
        })
      });
      
      if (processResponse.ok) {
        try {
          await saveDeviceMappings(selectedFile.id, deviceMappings);
          alert('File processed successfully! Mappings saved for future use.');
        } catch (error) {
          console.error('Error saving device mappings:', error);
          alert('File processed but failed to save device mappings.');
        }
      }
    } catch (error) {
      console.error('Process error:', error);
    }
    
    setDeviceModalOpen(false);
    setDeviceMappings({});
    setSelectedFile(null);
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

      {/* Show file details and mapping buttons for completed uploads */}
      {files.filter(f => f.status === 'completed').length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h2>Process Files</h2>
          {files.filter(f => f.status === 'completed').map(file => (
            <div key={`process-${file.id}`} style={{
              background: '#1e293b',
              border: '1px solid #334155',
              padding: '15px',
              margin: '10px 0',
              borderRadius: '5px'
            }}>
              <h3 style={{ color: '#f1f5f9', marginBottom: '10px' }}>{file.name}</h3>
              <p style={{ color: '#94a3b8' }}>Columns: {file.columns?.join(', ') || 'None'}</p>
              <p style={{ color: '#94a3b8' }}>Devices: {file.devices?.join(', ') || 'None'}</p>
              <button 
                onClick={() => openColumnMapping(file)}
                style={{
                  background: '#3b82f6',
                  color: 'white',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '4px',
                  marginTop: '10px',
                  cursor: 'pointer'
                }}
              >
                Start Processing
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Column Mapping Modal */}
      <SimpleModal 
        isOpen={modalOpen} 
        onClose={() => {
          setModalOpen(false);
          setColumnMappings({});
        }}
        title={selectedFile ? `Map Columns for ${selectedFile.name}` : 'Map Columns'}
      >
        {selectedFile && (
          <div>
            <p style={{ marginBottom: '20px' }}>
              Map the columns from your file to standard fields. AI suggestions are pre-filled based on column names.
            </p>
            
            {selectedFile.columns?.map((col, idx) => {
              const suggestion = aiSuggestions[col] || {};
              const confidence = suggestion.confidence || 0;
              const confidenceColor = confidence > 0.7 ? '#22c55e' : confidence > 0.5 ? '#f59e0b' : '#ef4444';
              
              return (
                <div key={idx} style={{ marginBottom: '15px' }}>
                  <label style={{ display: 'block', marginBottom: '5px', color: '#94a3b8' }}>
                    {col}
                    {confidence > 0 && (
                      <span style={{ 
                        marginLeft: '10px', 
                        fontSize: '0.8em', 
                        color: confidenceColor 
                      }}>
                        (AI: {(confidence * 100).toFixed(0)}% confident)
                      </span>
                    )}
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
                    <option value="person_id">Person/User ID</option>
                    <option value="door_id">Door/Location ID</option>
                    <option value="access_result">Access Result</option>
                    <option value="token_id">Token/Badge ID</option>
                    <option value="source_ip">Source IP</option>
                    <option value="dest_ip">Destination IP</option>
                    <option value="action">Action</option>
                    <option value="protocol">Protocol</option>
                    <option value="device">Device</option>
                    <option value="message">Message</option>
                    <option value="severity">Severity</option>
                  </select>
                </div>
              );
            })}
            
            <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => setModalOpen(false)}
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
              <button 
                onClick={handleColumnMappingSave}
                style={{
                  background: '#3b82f6',
                  color: 'white',
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Next: Map Devices
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
        {selectedFile && (
          <div>
            <p style={{ marginBottom: '20px' }}>
              Map the devices found in your file. AI suggestions are based on device names and patterns.
            </p>
            
            {selectedFile.devices && selectedFile.devices.length > 0 ? (
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
                    placeholder="e.g., Main Entrance, Floor 2, High Security"
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
              <p style={{ color: '#94a3b8' }}>No devices detected. Click Process to continue.</p>
            )}
            
            <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => {
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
              <button 
                onClick={handleDeviceMappingSave}
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
            </div>
          </div>
        )}
      </SimpleModal>
    </div>
  );
};

export default Upload;


