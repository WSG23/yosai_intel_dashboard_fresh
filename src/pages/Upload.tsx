import React, { useState, useCallback } from "react";
import {
  Upload as UploadIcon,
  FileText,
  AlertCircle,
  CheckCircle,
  X,
  Loader,
} from "lucide-react";
import SimpleModal from "../components/upload/SimpleModal";
import "./Upload.css";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: "pending" | "processing" | "mapping" | "completed" | "error";
  progress: number;
  error?: string;
  columns?: string[];
  mappedColumns?: Record<string, string>;
  devices?: string[];
  mappedDevices?: Record<string, string>;
  aiSuggestions?: Record<string, any>;
  deviceSuggestions?: Record<string, any>;
  fileInfo?: any;
  previewHtml?: string;
}

// Column mapping options that match your analytics system
const COLUMN_MAPPING_OPTIONS = [
  { value: "", label: "-- Select mapping --" },
  { value: "timestamp", label: "Event Time" },
  { value: "employee_code", label: "Employee Code" },
  { value: "access_card", label: "Access Card" },
  { value: "door_location", label: "Door Location" },
  { value: "entry_status", label: "Entry Status" },
  { value: "person_id", label: "Person/User ID" },
  { value: "token_id", label: "Token/Badge ID" },
  { value: "access_result", label: "Access Result" },
  { value: "device", label: "Device" },
  { value: "action", label: "Action" },
  { value: "source_ip", label: "Source IP" },
  { value: "dest_ip", label: "Destination IP" },
  { value: "protocol", label: "Protocol" },
  { value: "message", label: "Message" },
  { value: "severity", label: "Severity" },
];

const Upload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);

  // Modal states
  const [modalOpen, setModalOpen] = useState(false);
  const [deviceModalOpen, setDeviceModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null);

  // Mapping states
  const [columnMappings, setColumnMappings] = useState<Record<string, string>>(
    {},
  );
  const [deviceMappings, setDeviceMappings] = useState<Record<string, string>>(
    {},
  );
  const [aiSuggestions, setAiSuggestions] = useState<Record<string, any>>({});
  const [validationResults, setValidationResults] = useState<
    Record<string, any>
  >({});

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

  const handleFiles = async (fileList: File[]) => {
    const validFiles = fileList.filter((file) => {
      const validTypes = [".csv", ".xlsx", ".xls", ".json", ".log"];
      return validTypes.some((type) => file.name.toLowerCase().endsWith(type));
    });

    if (validFiles.length === 0) {
      alert("Please upload valid file types: CSV, Excel, JSON, or LOG files");
      return;
    }

    const newFiles: UploadedFile[] = validFiles.map((file) => ({
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: file.name,
      size: file.size,
      type: file.type || "application/octet-stream",
      status: "pending",
      progress: 0,
    }));

    setFiles((prev) => [...prev, ...newFiles]);

    for (const file of validFiles) {
      await uploadFile(file, newFiles.find((f) => f.name === file.name)!.id);
    }
  };

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

  const uploadFile = async (file: File, fileId: string) => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      console.log("Starting upload for:", file.name);
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId ? { ...f, status: "processing", progress: 25 } : f,
        ),
      );

      // Send file directly to Python backend
      const response = await fetch("/api/v1/upload", {
        method: "POST",
        body: formData,
      });

      console.log("Response received:", response.status);

      if (!response.ok) {
        let message = `Upload failed: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) {
            message = errorData.error;
          }
        } catch (_e) {
          const text = await response.text();
          if (text) {
            message = `${message} - ${text}`;
          }
        }
        throw new Error(message);
      }

      const data = await response.json();
      console.log("Python backend response:", data);

      // Extract all the Python-processed data
      const fileInfo = data.file_info_dict?.[file.name] || {};
      const suggestions = fileInfo.ai_suggestions || {};
      const columns = fileInfo.column_names || data.columns || [];
      const previewHtml = data.preview_html || "";
      const deviceSuggestions = data.device_suggestions || {};
      const hasLearnedMappings = fileInfo.learned_mappings || false;

      console.log("AI suggestions from Python:", suggestions);
      console.log("Device suggestions from Python:", deviceSuggestions);
      console.log("Has learned mappings:", hasLearnedMappings);

      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? {
                ...f,
                status: "completed",
                progress: 100,
                columns: columns,
                devices: data.detected_devices || [],
                aiSuggestions: suggestions,
                deviceSuggestions: deviceSuggestions,
                fileInfo: fileInfo,
                previewHtml: previewHtml,
              }
            : f,
        ),
      );

      const statusIcon = hasLearnedMappings ? "📋" : "🤖";
      const statusText = hasLearnedMappings
        ? "Using learned mappings"
        : "AI suggestions generated";

      setUploadMessage(
        `✅ Upload Successful! ${statusIcon} ${statusText} | File: ${file.name}, Rows: ${fileInfo.rows || 0}, Columns: ${columns.length}`,
      );
      setTimeout(() => setUploadMessage(""), 5000);
    } catch (error) {
      console.error("Upload error:", error);
      setFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? {
                ...f,
                status: "error",
                error: error instanceof Error ? error.message : "Upload failed",
              }
            : f,
        ),
      );
    }
  };

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  // Placeholder for server-side validation
  const validateMappings = async (_mappings: Record<string, string>) => {
    return true;
  };

  // Open column mapping modal with Python AI suggestions
  const openColumnMapping = async (file: UploadedFile) => {
    console.log("Opening column mapping for:", file);
    setSelectedFile(file);
    setIsProcessing(true);

    try {
      // Use AI suggestions from Python backend
      const mappings: Record<string, string> = {};

      if (file.aiSuggestions && Object.keys(file.aiSuggestions).length > 0) {
        // Python backend already analyzed the data and provided suggestions
        Object.entries(file.aiSuggestions).forEach(
          ([col, suggestion]: [string, any]) => {
            if (suggestion.field) {
              mappings[col] = suggestion.field;
            }
          },
        );
        setAiSuggestions(file.aiSuggestions);
      }

      console.log("Python AI mappings:", mappings);
      setColumnMappings(mappings);

      // Validate initial mappings
      await validateMappings(mappings);
    } finally {
      setIsProcessing(false);
      setModalOpen(true);
    }
  };

  // Save column mappings and open device modal
  const handleColumnMappingSave = async () => {
    if (!selectedFile) return;

    console.log("Saving column mappings:", columnMappings);

    // Validate before saving
    const isValid = await validateMappings(columnMappings);
    if (!isValid) {
      const confirmSave = window.confirm(
        "Some mappings may not be valid. Continue anyway?",
      );
      if (!confirmSave) return;
    }

    setFiles((prev) =>
      prev.map((f) =>
        f.id === selectedFile.id ? { ...f, mappedColumns: columnMappings } : f,
      ),
    );

    setModalOpen(false);

    // Persist column mappings
    await fetch("/api/v1/mappings/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: selectedFile.name,
        mapping_type: "column",
        column_mappings: columnMappings,
      }),
    });

    // Request device suggestions from backend
    try {
      const resp = await fetch("/api/v1/ai/suggest-devices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: selectedFile.name,
          column_mappings: columnMappings,
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        const devMappings: Record<string, string> = {};
        Object.entries(data.device_mappings || {}).forEach(
          ([device, info]: [string, any]) => {
            const parts = [] as string[];
            if (info.floor_number) parts.push(`Floor ${info.floor_number}`);
            if (info.is_entry) parts.push("Entry");
            if (info.is_exit) parts.push("Exit");
            if (info.is_elevator) parts.push("Elevator");
            if (info.is_stairwell) parts.push("Stairwell");
            if (info.security_level)
              parts.push(`Security: ${info.security_level}/10`);
            devMappings[device] =
              parts.join(", ") || info.classification || "Unknown";
          },
        );
        setDeviceMappings(devMappings);
      }
    } catch (err) {
      console.error("Device suggestion error", err);
    }

    setDeviceModalOpen(true);
  };

  // Process file and save learned mappings
  const handleDeviceMappingSave = async () => {
    if (!selectedFile) return;

    console.log("Saving device mappings:", deviceMappings);
    setIsProcessing(true);

    try {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === selectedFile.id
            ? {
                ...f,
                mappedDevices: deviceMappings,
                status: "completed" as const,
              }
            : f,
        ),
      );

      // Persist device mappings
      await fetch("/api/v1/mappings/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: selectedFile.name,
          mapping_type: "device",
          device_mappings: deviceMappings,
        }),
      });

      // Process file
      const processResponse = await fetch("/api/v1/process-enhanced", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fileId: selectedFile.id,
          fileName: selectedFile.name,
          columnMappings: selectedFile.mappedColumns || columnMappings,
          deviceMappings: deviceMappings,
        }),
      });

      if (processResponse.ok) {
        alert(
          "✅ File processed successfully! Mappings learned for future use.",
        );
      } else {
        throw new Error("Failed to process file");
      }
    } catch (error) {
      console.error("Process error:", error);
      alert(
        "❌ Failed to save mappings. Please check the console for details.",
      );
    } finally {
      setIsProcessing(false);
      setDeviceModalOpen(false);
      setDeviceMappings({});
      setSelectedFile(null);
    }
  };

  // Create data preview with actual data from Python
  const createDataPreview = (file: UploadedFile) => {
    if (!file.fileInfo) return null;

    // Use the preview HTML from Python backend
    if (file.previewHtml) {
      return (
        <div
          style={{
            marginTop: "20px",
            background: "#f8f9fa",
            padding: "15px",
            borderRadius: "5px",
          }}
        >
          <h4 style={{ marginBottom: "10px" }}>Data Preview (first 5 rows):</h4>
          <div
            style={{ overflowX: "auto" }}
            dangerouslySetInnerHTML={{ __html: file.previewHtml }}
          />
        </div>
      );
    }

    return null;
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h1>Upload Security Data</h1>
        <p>Upload CSV, Excel, JSON, or LOG files for analysis</p>
      </div>

      <div
        className={`upload-dropzone ${isDragging ? "dragging" : ""}`}
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
        <div
          style={{
            background: "#10b981",
            color: "white",
            padding: "15px",
            borderRadius: "5px",
            margin: "20px 0",
            textAlign: "left",
            fontSize: "16px",
            fontWeight: "500",
          }}
        >
          {uploadMessage}
        </div>
      )}

      {files.length > 0 && (
        <div className="files-list">
          <h2>Uploaded Files</h2>
          {files.map((file) => (
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
                {file.status === "pending" && (
                  <span className="status-text">Waiting...</span>
                )}
                {file.status === "processing" && (
                  <span className="status-text">
                    Processing with Python AI...
                  </span>
                )}
                {file.status === "completed" && (
                  <>
                    <CheckCircle size={20} className="success-icon" />
                    <span className="status-text">Ready</span>
                  </>
                )}
                {file.status === "error" && (
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

      {/* Show AI Column Mapping section for completed uploads */}
      {files.filter((f) => f.status === "completed").length > 0 && (
        <div style={{ marginTop: "30px" }}>
          <h2>AI Column Mapping</h2>
          {files
            .filter((f) => f.status === "completed")
            .map((file) => (
              <div
                key={`mapping-${file.id}`}
                style={{
                  background: "#f8f9fa",
                  border: "1px solid #dee2e6",
                  padding: "20px",
                  margin: "10px 0",
                  borderRadius: "5px",
                }}
              >
                <div style={{ marginBottom: "15px" }}>
                  <strong>Column Names:</strong>
                  <ul style={{ margin: "5px 0", paddingLeft: "20px" }}>
                    {file.columns?.map((col, idx) => (
                      <li key={idx} style={{ fontSize: "14px" }}>
                        {col}
                      </li>
                    )) || <li>No columns detected</li>}
                  </ul>
                </div>

                {createDataPreview(file)}

                <div style={{ marginTop: "20px" }}>
                  <h4 style={{ marginBottom: "10px" }}>AI Column Mapping:</h4>
                  <p
                    style={{
                      fontSize: "14px",
                      color: "#6c757d",
                      marginBottom: "15px",
                    }}
                  >
                    Review AI suggestions and adjust mappings as needed.
                  </p>

                  {/* Show Python AI analysis results */}
                  {file.aiSuggestions &&
                    Object.keys(file.aiSuggestions).length > 0 && (
                      <div style={{ marginBottom: "15px", fontSize: "14px" }}>
                        <strong>Column Name & AI Suggestion</strong>
                        <div style={{ marginTop: "10px" }}>
                          {Object.entries(file.aiSuggestions).map(
                            ([col, suggestion]: [string, any]) => (
                              <div key={col} style={{ marginBottom: "5px" }}>
                                <span style={{ color: "#495057" }}>{col}:</span>
                                {suggestion.field && (
                                  <span
                                    style={{
                                      marginLeft: "10px",
                                      color:
                                        suggestion.confidence > 0.7
                                          ? "#28a745"
                                          : "#ffc107",
                                      fontWeight: "bold",
                                    }}
                                  >
                                    {COLUMN_MAPPING_OPTIONS.find(
                                      (opt) => opt.value === suggestion.field,
                                    )?.label || suggestion.field}
                                    ({(suggestion.confidence * 100).toFixed(0)}
                                    %)
                                  </span>
                                )}
                              </div>
                            ),
                          )}
                        </div>
                      </div>
                    )}

                  <button
                    onClick={() => openColumnMapping(file)}
                    disabled={isProcessing}
                    style={{
                      background: isProcessing ? "#6c757d" : "#007bff",
                      color: "white",
                      padding: "10px 20px",
                      border: "none",
                      borderRadius: "4px",
                      cursor: isProcessing ? "not-allowed" : "pointer",
                      fontSize: "16px",
                      fontWeight: "500",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                    }}
                  >
                    {isProcessing && (
                      <Loader size={16} className="animate-spin" />
                    )}
                    Save Column Mappings
                  </button>
                </div>
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
          setValidationResults({});
        }}
        title={
          selectedFile ? `Map Columns for ${selectedFile.name}` : "Map Columns"
        }
      >
        {selectedFile && (
          <div>
            <p style={{ marginBottom: "20px" }}>
              Map the columns from your file to standard fields. AI suggestions
              are based on data analysis.
            </p>

            {selectedFile.columns?.map((col, idx) => {
              const suggestion = aiSuggestions[col] || {};
              const currentMapping = columnMappings[col] || "";
              const hasAISuggestion = suggestion.field && suggestion.confidence;
              const validation = validationResults[col];

              return (
                <div key={idx} style={{ marginBottom: "15px" }}>
                  <label
                    style={{
                      display: "block",
                      marginBottom: "5px",
                      color: "#495057",
                      fontWeight: "500",
                    }}
                  >
                    {col}
                    {hasAISuggestion && (
                      <span
                        style={{
                          marginLeft: "10px",
                          fontSize: "0.875rem",
                          color:
                            suggestion.confidence > 0.7
                              ? "#28a745"
                              : suggestion.confidence > 0.5
                                ? "#ffc107"
                                : "#dc3545",
                          fontWeight: "normal",
                        }}
                      >
                        (AI: {(suggestion.confidence * 100).toFixed(0)}% - based
                        on data analysis)
                      </span>
                    )}
                  </label>
                  <select
                    value={currentMapping}
                    onChange={async (e) => {
                      const newMappings = {
                        ...columnMappings,
                        [col]: e.target.value,
                      };
                      setColumnMappings(newMappings);
                      // Validate on change
                      await validateMappings(newMappings);
                    }}
                    style={{
                      width: "100%",
                      padding: "8px",
                      borderRadius: "4px",
                      border:
                        validation && !validation.valid
                          ? "2px solid #dc3545"
                          : "1px solid #ced4da",
                      background: currentMapping ? "#e8f5e9" : "white",
                      color: "#495057",
                      fontSize: "14px",
                    }}
                  >
                    {COLUMN_MAPPING_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {validation && !validation.valid && (
                    <small
                      style={{
                        color: "#dc3545",
                        marginTop: "2px",
                        display: "block",
                      }}
                    >
                      {validation.message}
                    </small>
                  )}
                </div>
              );
            })}

            <div
              style={{
                marginTop: "20px",
                display: "flex",
                gap: "10px",
                justifyContent: "flex-end",
              }}
            >
              <button
                onClick={() => setModalOpen(false)}
                style={{
                  background: "#6c757d",
                  color: "white",
                  padding: "8px 16px",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleColumnMappingSave}
                style={{
                  background: "#007bff",
                  color: "white",
                  padding: "8px 16px",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
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
        title={
          selectedFile ? `Map Devices for ${selectedFile.name}` : "Map Devices"
        }
      >
        {selectedFile && (
          <div>
            <p style={{ marginBottom: "20px" }}>
              Device mappings{" "}
              {selectedFile.fileInfo?.learned_mappings
                ? "loaded from previous sessions"
                : "generated by AI analysis"}
              .
            </p>

            {selectedFile.devices && selectedFile.devices.length > 0 ? (
              selectedFile.devices.map((device, idx) => (
                <div key={idx} style={{ marginBottom: "15px" }}>
                  <label
                    style={{
                      display: "block",
                      marginBottom: "5px",
                      color: "#495057",
                    }}
                  >
                    {device}
                  </label>
                  <input
                    type="text"
                    value={deviceMappings[device] || ""}
                    onChange={(e) =>
                      setDeviceMappings({
                        ...deviceMappings,
                        [device]: e.target.value,
                      })
                    }
                    placeholder="e.g., Main Entrance, Floor 2, High Security"
                    style={{
                      width: "100%",
                      padding: "8px",
                      borderRadius: "4px",
                      border: "1px solid #ced4da",
                      background: deviceMappings[device] ? "#e8f5e9" : "white",
                      color: "#495057",
                    }}
                  />
                </div>
              ))
            ) : (
              <p style={{ color: "#6c757d" }}>
                No devices detected. Click Process to continue.
              </p>
            )}

            <div
              style={{
                marginTop: "20px",
                display: "flex",
                gap: "10px",
                justifyContent: "flex-end",
              }}
            >
              <button
                onClick={() => {
                  if (selectedFile) {
                    setFiles((prev) =>
                      prev.map((f) =>
                        f.id === selectedFile.id
                          ? { ...f, status: "completed" as const }
                          : f,
                      ),
                    );
                  }
                  setDeviceModalOpen(false);
                  setDeviceMappings({});
                }}
                style={{
                  background: "#6c757d",
                  color: "white",
                  padding: "8px 16px",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Skip
              </button>
              <button
                onClick={handleDeviceMappingSave}
                disabled={isProcessing}
                style={{
                  background: isProcessing ? "#6c757d" : "#28a745",
                  color: "white",
                  padding: "8px 16px",
                  border: "none",
                  borderRadius: "4px",
                  cursor: isProcessing ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                {isProcessing && <Loader size={16} className="animate-spin" />}
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
