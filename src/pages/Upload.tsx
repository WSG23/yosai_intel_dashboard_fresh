// Upload.tsx
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import Papa from 'papaparse';
import {
  Card,
  CardHeader,
  CardBody,
  Progress,
  Button,
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Table,
  Input,
  // Select,
  // Checkbox,
  Alert,
  Badge,
  Toast
} from 'reactstrap';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Types matching the Python data structures
interface FileInfo {
  filename: string;
  size: number;
  type: string;
  lastModified: number;
  content?: string;
  rows?: number;
  columns?: string[];
  devices?: string[];
  preview?: any;
}

interface ColumnMapping {
  original: string;
  mapped: string;
  confidence: number;
  isCustom?: boolean;
}

interface DeviceAttributes {
  device_id: string;
  device_name: string;
  floor_number: number;
  security_level: number;
  is_entry: boolean;
  is_exit: boolean;
  is_elevator: boolean;
  is_stairwell: boolean;
  is_fire_escape: boolean;
  is_restricted: boolean;
  confidence: number;
  ai_reasoning?: string;
}

interface UploadProgress {
  taskId: string;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'error';
  message?: string;
}

interface ValidationResult {
  valid: boolean;
  error?: string;
  warnings?: string[];
}

export interface CSVRow {
  [key: string]: string;
}

export interface CSVParseResult {
  rows: CSVRow[];
  columns: string[];
  devices: string[];
}

// Constants matching Python configuration
const MAX_FILE_SIZE_MB = 50;
const ALLOWED_EXTENSIONS = ['.csv', '.json', '.xlsx', '.xls'];
const REQUIRED_FIELDS = ['timestamp', 'person_id', 'door_id', 'access_result'];
const CHUNK_SIZE = 50000;

// Security validation patterns
const MALICIOUS_PATTERNS = [
  /\.\.\//g,  // Path traversal
  /<script/gi, // Script injection
  /union\s+select/gi, // SQL injection
  /\x00/g, // Null bytes
];

export const sanitizeUnicode = (text: string): string => {
  const surrogatePattern = /[\uD800-\uDFFF]/g;
  let cleaned = text.replace(surrogatePattern, '');

  if ('normalize' in String.prototype) {
    cleaned = cleaned.normalize('NFKC');
  }

  cleaned = cleaned.replace(/[\u200B-\u200D\uFEFF]/g, '');

  return cleaned;
};

export const parseCSV = (content: string): CSVParseResult => {
  const result = Papa.parse<CSVRow>(content, {
    header: true,
    skipEmptyLines: true,
  });

  const headers = result.meta.fields?.map(h => sanitizeUnicode(h.trim())) || [];
  const rows = result.data.map(row => {
    const sanitizedRow: CSVRow = {};
    headers.forEach(header => {
      sanitizedRow[header] = sanitizeUnicode((row as any)[header] ?? '');
    });
    return sanitizedRow;
  });

  const deviceColumn = headers.find(h =>
    h.toLowerCase().includes('door') ||
    h.toLowerCase().includes('device')
  );
  const devices = deviceColumn
    ? Array.from(new Set(rows.map(r => r[deviceColumn])))
    : [];

  return { rows, columns: headers, devices };
};

export const Upload: React.FC = () => {
  // State management
  const [uploadedFiles, setUploadedFiles] = useState<FileInfo[]>([]);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [processingTasks, setProcessingTasks] = useState<Map<string, any>>(new Map());
  const [columnMappings, setColumnMappings] = useState<Map<string, ColumnMapping[]>>(new Map());
  const [deviceMappings, setDeviceMappings] = useState<Map<string, DeviceAttributes[]>>(new Map());
  const [showColumnModal, setShowColumnModal] = useState(false);
  const [showDeviceModal, setShowDeviceModal] = useState(false);
  const [currentFile, setCurrentFile] = useState<FileInfo | null>(null);
  const [sessionId] = useState(() => uuidv4());
  const [alerts, setAlerts] = useState<Array<{ id: string; type: string; message: string }>>([]);

  // Refs for background processing
  const uploadQueueRef = useRef<Array<{ file: File; taskId: string }>>([]);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);


  // File validation matching Python's security checks
  const validateFile = (file: File): ValidationResult => {
    // Check file size
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > MAX_FILE_SIZE_MB) {
      return { valid: false, error: `File too large: ${sizeMB.toFixed(1)}MB > ${MAX_FILE_SIZE_MB}MB` };
    }

    // Check file extension
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return { valid: false, error: `Invalid file type: ${ext}` };
    }

    // Check filename for malicious patterns
    const sanitizedName = sanitizeUnicode(file.name);
    for (const pattern of MALICIOUS_PATTERNS) {
      if (pattern.test(sanitizedName)) {
        return { valid: false, error: 'Invalid filename detected' };
      }
    }

    return { valid: true };
  };

  // Process file content (matching Python's process_uploaded_file)
  const processFileContent = async (file: File): Promise<FileInfo> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = async (e) => {
        const content = e.target?.result as string;
        const base64Content = content.split(',')[1];

        // Decode and sanitize content
        const decoded = atob(base64Content);
        const sanitized = sanitizeUnicode(decoded);

        // Parse based on file type
        let parsed: any;
        if (file.name.endsWith('.csv')) {
          parsed = parseCSV(sanitized);
        } else if (file.name.endsWith('.json')) {
          parsed = JSON.parse(sanitized);
        } else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
          // For Excel files, we'd need a library like SheetJS
          parsed = { error: 'Excel parsing requires additional setup' };
        }

        const fileInfo: FileInfo = {
          filename: sanitizeUnicode(file.name),
          size: file.size,
          type: file.type,
          lastModified: file.lastModified,
          content: base64Content,
          rows: parsed.rows?.length || 0,
          columns: parsed.columns || [],
          devices: parsed.devices || []
        };

        resolve(fileInfo);
      };

      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsDataURL(file);
    });
  };


  // AI column suggestion (matching Python's get_ai_column_suggestions)
  const getAIColumnSuggestions = (columns: string[]): ColumnMapping[] => {
    const mappingPatterns = {
      person_id: ['person id', 'userid', 'user id', 'employee', 'badge'],
      door_id: ['device name', 'door', 'reader', 'access point'],
      access_result: ['access result', 'result', 'status', 'outcome'],
      timestamp: ['timestamp', 'time', 'datetime', 'date'],
    };

    return columns.map(col => {
      const colLower = col.toLowerCase();
      let bestMatch = { field: '', confidence: 0 };

      for (const [target, patterns] of Object.entries(mappingPatterns)) {
        for (const pattern of patterns) {
          if (colLower.includes(pattern) || pattern.includes(colLower)) {
            const confidence = colLower === pattern ? 1.0 : 0.7;
            if (confidence > bestMatch.confidence) {
              bestMatch = { field: target, confidence };
            }
          }
        }
      }

      return {
        original: col,
        mapped: bestMatch.field || 'other',
        confidence: bestMatch.confidence
      };
    });
  };

  // AI device analysis (matching Python's AIDeviceGenerator)
  const analyzeDeviceAttributes = (deviceId: string): DeviceAttributes => {
    const deviceLower = deviceId.toLowerCase();

    // Extract floor number
    const floorMatch = deviceId.match(/[Ff](\d+)|floor\s*(\d+)|level\s*(\d+)/);
    const floorNumber = floorMatch ? parseInt(floorMatch[1] || floorMatch[2] || floorMatch[3]) : 1;

    // Determine security level based on keywords
    let securityLevel = 3; // Default
    if (deviceLower.includes('server') || deviceLower.includes('data')) securityLevel = 8;
    else if (deviceLower.includes('executive') || deviceLower.includes('secure')) securityLevel = 7;
    else if (deviceLower.includes('lobby') || deviceLower.includes('public')) securityLevel = 1;

    // Determine access types
    const isEntry = !deviceLower.includes('exit');
    const isExit = deviceLower.includes('exit') || deviceLower.includes('out');
    const isElevator = deviceLower.includes('elevator') || deviceLower.includes('lift');
    const isStairwell = deviceLower.includes('stair');
    const isFireEscape = deviceLower.includes('fire') && deviceLower.includes('exit');
    const isRestricted = securityLevel >= 7;

    // Generate readable name
    const deviceName = deviceId
      .replace(/_/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/\b\w/g, l => l.toUpperCase());

    // Calculate confidence
    const confidence = floorMatch ? 0.85 : 0.65;

    return {
      device_id: deviceId,
      device_name: deviceName,
      floor_number: floorNumber,
      security_level: securityLevel,
      is_entry: isEntry,
      is_exit: isExit,
      is_elevator: isElevator,
      is_stairwell: isStairwell,
      is_fire_escape: isFireEscape,
      is_restricted: isRestricted,
      confidence: confidence,
      ai_reasoning: `Pattern analysis: ${deviceLower}`
    };
  };

  // File upload handler
  const handleFileUpload = async (acceptedFiles: File[]) => {
    const validFiles: File[] = [];

    // Validate each file
    for (const file of acceptedFiles) {
      const validation = validateFile(file);
      if (validation.valid) {
        validFiles.push(file);
      } else {
        addAlert('error', `${file.name}: ${validation.error}`);
      }
    }

    // Process valid files
    for (const file of validFiles) {
      const taskId = uuidv4();

      // Add to upload queue
      uploadQueueRef.current.push({ file, taskId });

      // Initialize progress tracking
      setUploadProgress(prev => [...prev, {
        taskId,
        progress: 0,
        status: 'pending'
      }]);

      // Schedule processing
      scheduleFileProcessing(file, taskId);
    }
  };

  // Background file processing
  const scheduleFileProcessing = async (file: File, taskId: string) => {
    try {
      // Update progress
      updateProgress(taskId, 10, 'processing');

      // Process file content
      const fileInfo = await processFileContent(file);
      updateProgress(taskId, 30, 'processing');

      // Get AI suggestions for columns
      const columnSuggestions = getAIColumnSuggestions(fileInfo.columns || []);
      setColumnMappings(prev => new Map(prev).set(fileInfo.filename, columnSuggestions));
      updateProgress(taskId, 50, 'processing');

      // Analyze devices
      const deviceAnalysis = (fileInfo.devices || []).map(analyzeDeviceAttributes);
      setDeviceMappings(prev => new Map(prev).set(fileInfo.filename, deviceAnalysis));
      updateProgress(taskId, 70, 'processing');

      // Save to backend (simulated)
      await saveToBackend(fileInfo, columnSuggestions, deviceAnalysis);
      updateProgress(taskId, 90, 'processing');

      // Finalize
      setUploadedFiles(prev => [...prev, fileInfo]);
      updateProgress(taskId, 100, 'completed');

      // Show verification modals
      setCurrentFile(fileInfo);
      setShowColumnModal(true);

    } catch (error) {
      console.error('Processing error:', error);
      updateProgress(taskId, 0, 'error', (error as Error).message || "Unknown error");
      addAlert('error', `Failed to process ${file.name}`);
    }
  };

  // Progress update helper
  const updateProgress = (taskId: string, progress: number, status: UploadProgress['status'], message?: string) => {
    setUploadProgress(prev => prev.map(p =>
      p.taskId === taskId
        ? { ...p, progress, status, message }
        : p
    ));
  };

  // Alert helper
  const addAlert = (type: string, message: string) => {
    const id = uuidv4();
    setAlerts(prev => [...prev, { id, type, message }]);
    setTimeout(() => {
      setAlerts(prev => prev.filter(a => a.id !== id));
    }, 5000);
  };

  // Backend save simulation
  const saveToBackend = async (fileInfo: FileInfo, columns: ColumnMapping[], devices: DeviceAttributes[]) => {
    // In a real implementation, this would make API calls
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Simulate saving mappings
    const payload = {
      session_id: sessionId,
      file_info: fileInfo,
      column_mappings: columns,
      device_mappings: devices,
      metadata: {
        processed_at: new Date().toISOString(),
        quality_score: 95,
        user_id: 'current_user'
      }
    };

    console.log('Saving to backend:', payload);
  };

  // Dropzone configuration
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileUpload,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxSize: MAX_FILE_SIZE_MB * 1024 * 1024,
    multiple: true
  });

  // Column verification modal handlers
  const handleColumnMappingConfirm = () => {
    if (!currentFile) return;

    const mappings = columnMappings.get(currentFile.filename);
    if (!mappings) return;

    // Validate required fields
    const mappedFields = mappings.map(m => m.mapped);
    const missingRequired = REQUIRED_FIELDS.filter(f => !mappedFields.includes(f));

    if (missingRequired.length > 0) {
      addAlert('warning', `Missing required fields: ${missingRequired.join(', ')}`);
    }

    // Save confirmed mappings
    addAlert('success', `Column mappings saved for ${currentFile.filename}`);
    setShowColumnModal(false);

    // Show device modal next
    setShowDeviceModal(true);
  };

  // Device verification modal handlers
  const handleDeviceMappingConfirm = () => {
    if (!currentFile) return;

    const devices = deviceMappings.get(currentFile.filename);
    if (!devices) return;

    // Save confirmed device mappings
    addAlert('success', `Device mappings saved for ${currentFile.filename}`);
    setShowDeviceModal(false);

    // Clear current file
    setCurrentFile(null);
  };

  // Render upload area
  const renderUploadArea = () => (
    <div
      {...getRootProps()}
      className={`upload-dropzone ${isDragActive ? 'upload-dropzone--active' : ''}`}
      style={{
        border: '2px dashed #007bff',
        borderRadius: '8px',
        padding: '3rem',
        textAlign: 'center',
        cursor: 'pointer',
        backgroundColor: isDragActive ? '#f0f8ff' : '#fafafa',
        minHeight: '200px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      <input {...getInputProps()} />
      <i className="fas fa-cloud-upload-alt" style={{ fontSize: '48px', color: '#007bff', marginBottom: '16px' }} />
      <h3>Drag & Drop Files Here</h3>
      <p>or click to browse</p>
      <small>Supported formats: CSV, JSON, Excel (max {MAX_FILE_SIZE_MB}MB)</small>
    </div>
  );

  // Render progress bars
  const renderProgress = () => (
    <div className="mt-3">
      {uploadProgress.map(progress => (
        <div key={progress.taskId} className="mb-2">
          <Progress
            value={progress.progress}
            color={progress.status === 'error' ? 'danger' : 'primary'}
            striped={progress.status === 'processing'}
            animated={progress.status === 'processing'}
          >
            {progress.progress}%
          </Progress>
          {progress.message && (
            <small className="text-muted">{progress.message}</small>
          )}
        </div>
      ))}
    </div>
  );

  // Render column verification modal
  const renderColumnModal = () => {
    const mappings = currentFile ? columnMappings.get(currentFile.filename) || [] : [];

    return (
      <Modal isOpen={showColumnModal} toggle={() => setShowColumnModal(false)} size="lg">
        <ModalHeader>Verify Column Mappings - {currentFile?.filename}</ModalHeader>
        <ModalBody>
          <Table>
            <thead>
              <tr>
                <th>Original Column</th>
                <th>Map To</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {mappings.map((mapping, idx) => (
                <tr key={idx}>
                  <td>{mapping.original}</td>
                  <td>
                    <Input
                      type="select"
                      value={mapping.mapped}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                        const updated = [...mappings];
                        updated[idx].mapped = e.target.value;
                        setColumnMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                      }}
                    >
                      <option value="">-- Select --</option>
                      {REQUIRED_FIELDS.map(field => (
                        <option key={field} value={field}>{field}</option>
                      ))}
                      <option value="other">Other</option>
                    </Input>
                  </td>
                  <td>
                    <Badge color={mapping.confidence > 0.8 ? 'success' : mapping.confidence > 0.5 ? 'warning' : 'secondary'}>
                      {(mapping.confidence * 100).toFixed(0)}%
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </ModalBody>
        <ModalFooter>
          <Button color="secondary" onClick={() => setShowColumnModal(false)}>Cancel</Button>
          <Button color="primary" onClick={handleColumnMappingConfirm}>Confirm Mappings</Button>
        </ModalFooter>
      </Modal>
    );
  };

  // Render device verification modal  
  const renderDeviceModal = () => {
    const devices = currentFile ? deviceMappings.get(currentFile.filename) || [] : [];

    return (
      <Modal isOpen={showDeviceModal} toggle={() => setShowDeviceModal(false)} size="xl">
        <ModalHeader>Verify Device Mappings - {currentFile?.filename}</ModalHeader>
        <ModalBody style={{ maxHeight: '70vh', overflowY: 'auto' }}>
          <div className="mb-3">
            <Alert color="info">
              <strong>Security Level Guide:</strong>
              <div>0-2: Public areas | 3-5: Office areas | 6-8: Restricted | 9-10: Critical</div>
            </Alert>
          </div>
          <Table>
            <thead>
              <tr>
                <th>Device ID</th>
                <th>Device Name</th>
                <th>Floor</th>
                <th>Entry/Exit</th>
                <th>Special</th>
                <th>Security</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((device, idx) => (
                <tr key={idx}>
                  <td>{device.device_id}</td>
                  <td>
                    <Input
                      type="text"
                      value={device.device_name}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                        const updated = [...devices];
                        updated[idx].device_name = e.target.value;
                        setDeviceMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                      }}
                    />
                  </td>
                  <td>
                    <Input
                      type="number"
                      min="0"
                      max="50"
                      value={device.floor_number}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                        const updated = [...devices];
                        updated[idx].floor_number = parseInt(e.target.value) || 0;
                        setDeviceMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                      }}
                      style={{ width: '80px' }}
                    />
                  </td>
                  <td>
                    <div>
                      <Input type="checkbox"
                        checked={device.is_entry}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                          const updated = [...devices];
                          updated[idx].is_entry = e.target.checked;
                          setDeviceMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                        }}
                      />
                      <Input type="checkbox"
                        checked={device.is_exit}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                          const updated = [...devices];
                          updated[idx].is_exit = e.target.checked;
                          setDeviceMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                        }}
                      />
                    </div>
                  </td>
                  <td>
                    <div>
                      <Input type="checkbox"
                        checked={device.is_elevator}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                          const updated = [...devices];
                          updated[idx].is_elevator = e.target.checked;
                          setDeviceMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                        }}
                      />
                      <Input type="checkbox"
                        checked={device.is_stairwell}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                          const updated = [...devices];
                          updated[idx].is_stairwell = e.target.checked;
                          setDeviceMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                        }}
                      />
                      <Input type="checkbox"
                        checked={device.is_fire_escape}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                          const updated = [...devices];
                          updated[idx].is_fire_escape = e.target.checked;
                          setDeviceMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                        }}
                      />
                      <Input type="checkbox"
                        checked={device.is_restricted}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                          const updated = [...devices];
                          updated[idx].is_restricted = e.target.checked;
                          setDeviceMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                        }}
                      />
                    </div>
                  </td>
                  <td>
                    <Input
                      type="number"
                      min="0"
                      max="10"
                      value={device.security_level}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                        const updated = [...devices];
                        updated[idx].security_level = parseInt(e.target.value) || 0;
                        setDeviceMappings(prev => new Map(prev).set(currentFile!.filename, updated));
                      }}
                      style={{ width: '80px' }}
                    />
                  </td>
                  <td>
                    <Badge color={device.confidence > 0.8 ? 'success' : device.confidence > 0.6 ? 'warning' : 'secondary'}>
                      {(device.confidence * 100).toFixed(0)}%
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </ModalBody>
        <ModalFooter>
          <Button color="secondary" onClick={() => setShowDeviceModal(false)}>Cancel</Button>
          <Button color="primary" onClick={handleDeviceMappingConfirm}>Confirm Devices</Button>
        </ModalFooter>
      </Modal>
    );
  };

  // Main render
  return (
    <div className="upload-container">
      {/* Alerts */}
      <div className="alerts-container" style={{ position: 'fixed', top: 20, right: 20, zIndex: 9999 }}>
        {alerts.map(alert => (
          <Toast key={alert.id}>
            <Alert color={alert.type === 'error' ? 'danger' : alert.type}>
              {alert.message}
            </Alert>
          </Toast>
        ))}
      </div>

      {/* Main upload card */}
      <Card>
        <CardHeader>
          <h5>Upload Data Files</h5>
        </CardHeader>
        <CardBody>
          {renderUploadArea()}
          {uploadProgress.length > 0 && renderProgress()}

          {/* Uploaded files list */}
          {uploadedFiles.length > 0 && (
            <div className="mt-4">
              <h6>Uploaded Files:</h6>
              <ul>
                {uploadedFiles.map((file, idx) => (
                  <li key={idx}>
                    {file.filename} - {file.rows} rows, {file.columns?.length} columns
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Modals */}
      {renderColumnModal()}
      {renderDeviceModal()}
    </div>
  );
};

export default Upload;