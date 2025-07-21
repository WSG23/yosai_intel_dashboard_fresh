export type ProcessingStatus = 'pending' | 'uploading' | 'completed' | 'error';

export interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  status: ProcessingStatus;
  progress: number;
  error?: string;
}

export interface ColumnMapping {
  original: string;
  mapped: string;
  confidence: number;
}

export interface DeviceMapping {
  device_id: string;
  device_name: string;
  floor_number: number;
  is_entry: boolean;
  is_exit: boolean;
  is_elevator: boolean;
  is_stairwell: boolean;
  is_fire_escape: boolean;
  is_restricted: boolean;
  security_level: number;
}

export interface AISuggestion {
  field: string;
  confidence: number;
}

export interface FileData {
  filename: string;
  columns: string[];
  ai_suggestions: Record<string, AISuggestion>;
  sample_data?: Record<string, any[]>;
}
