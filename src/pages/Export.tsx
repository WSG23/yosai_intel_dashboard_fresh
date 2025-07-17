/**
 * Export Page Component
 * Handle data export in various formats using Python backend
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Loader2, 
  Download, 
  FileText, 
  FileJson, 
  FileSpreadsheet, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  Database,
  Filter
} from 'lucide-react';

// Types
interface ExportFormat {
  type: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  mimeType: string;
  extension: string;
}

interface DataSource {
  value: string;
  label: string;
}

interface ExportJob {
  id: string;
  format: string;
  source: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  createdAt: Date;
  completedAt?: Date;
  errorMessage?: string;
  downloadUrl?: string;
}

// Available export formats
const EXPORT_FORMATS: ExportFormat[] = [
  {
    type: 'csv',
    name: 'CSV',
    description: 'Comma-separated values format for spreadsheet applications',
    icon: <FileText className="h-5 w-5" />,
    mimeType: 'text/csv',
    extension: 'csv'
  },
  {
    type: 'json',
    name: 'JSON',
    description: 'JavaScript Object Notation for API integration',
    icon: <FileJson className="h-5 w-5" />,
    mimeType: 'application/json',
    extension: 'json'
  },
  {
    type: 'xlsx',
    name: 'Excel',
    description: 'Microsoft Excel format with multiple sheets',
    icon: <FileSpreadsheet className="h-5 w-5" />,
    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    extension: 'xlsx'
  }
];

// API Functions
const exportAPI = {
  async getExportFormats(): Promise<{ formats: ExportFormat[] }> {
    try {
      const response = await fetch('/api/v1/export/formats');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    } catch (error) {
      console.error('Failed to fetch export formats:', error);
      return { formats: EXPORT_FORMATS }; // Fallback to static formats
    }
  },

  async getDataSources(): Promise<{ sources: DataSource[] }> {
    const response = await fetch('/api/v1/analytics/sources');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async exportData(format: string, dataSource?: string): Promise<Blob> {
    const url = dataSource 
      ? `/api/v1/export/analytics/${format}?data_source=${encodeURIComponent(dataSource)}`
      : `/api/v1/export/analytics/${format}`;
    
    const response = await fetch(url);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Export failed with status: ${response.status}`);
    }
    
    return response.blob();
  }
};

// Components
const ExportFormatCard: React.FC<{
  format: ExportFormat;
  onExport: (format: string) => void;
  isExporting: boolean;
  currentFormat?: string;
}> = ({ format, onExport, isExporting, currentFormat }) => {
  const isCurrentlyExporting = isExporting && currentFormat === format.type;

  return (
    <Card className="transition-all duration-200 hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              {format.icon}
            </div>
            <div>
              <CardTitle className="text-lg">{format.name}</CardTitle>
              <Badge variant="outline" className="mt-1">
                .{format.extension}
              </Badge>
            </div>
          </div>
          <Button
            onClick={() => onExport(format.type)}
            disabled={isExporting}
            className="flex items-center space-x-2"
          >
            {isCurrentlyExporting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            <span>{isCurrentlyExporting ? 'Exporting...' : 'Export'}</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-gray-600">{format.description}</p>
      </CardContent>
    </Card>
  );
};

const ExportJobCard: React.FC<{ job: ExportJob }> = ({ job }) => {
  const getStatusIcon = () => {
    switch (job.status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (job.status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <p className="font-medium">{job.format.toUpperCase()} Export</p>
              <p className="text-sm text-gray-600">
                {job.source ? `Source: ${job.source}` : 'All sources'}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Badge className={getStatusColor()}>
              {job.status}
            </Badge>
            {job.status === 'completed' && job.downloadUrl && (
              <Button
                size="sm"
                onClick={() => window.open(job.downloadUrl, '_blank')}
                className="flex items-center space-x-1"
              >
                <Download className="h-3 w-3" />
                <span>Download</span>
              </Button>
            )}
          </div>
        </div>
        {job.errorMessage && (
          <Alert className="mt-3 border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {job.errorMessage}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

// Main Component
const ExportPage: React.FC = () => {
  const [exportFormats, setExportFormats] = useState<ExportFormat[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [currentFormat, setCurrentFormat] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [formatsResponse, sourcesResponse] = await Promise.all([
          exportAPI.getExportFormats(),
          exportAPI.getDataSources()
        ]);
        
        setExportFormats(formatsResponse.formats);
        setDataSources(sourcesResponse.sources);
      } catch (err) {
        console.error('Failed to load initial data:', err);
        setError('Failed to load export options');
        setExportFormats(EXPORT_FORMATS); // Fallback
      }
    };

    loadInitialData();
  }, []);

  // Handle export
  const handleExport = async (format: string) => {
    setIsExporting(true);
    setCurrentFormat(format);
    setError(null);
    setSuccess(null);

    // Create export job
    const job: ExportJob = {
      id: Date.now().toString(),
      format,
      source: selectedSource || 'all',
      status: 'processing',
      progress: 0,
      createdAt: new Date()
    };

    setExportJobs(prev => [job, ...prev]);

    try {
      // Call export API
      const blob = await exportAPI.exportData(format, selectedSource || undefined);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const formatInfo = exportFormats.find(f => f.type === format);
      const filename = `analytics_export_${new Date().toISOString().split('T')[0]}.${formatInfo?.extension || format}`;
      
      // Trigger download
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      // Update job status
      setExportJobs(prev => prev.map(j => 
        j.id === job.id 
          ? { ...j, status: 'completed', progress: 100, completedAt: new Date(), downloadUrl: url }
          : j
      ));

      setSuccess(`${format.toUpperCase()} export completed successfully`);
    } catch (err) {
      console.error('Export failed:', err);
      const errorMessage = err instanceof Error ? err.message : 'Export failed';
      
      // Update job status
      setExportJobs(prev => prev.map(j => 
        j.id === job.id 
          ? { ...j, status: 'failed', errorMessage }
          : j
      ));

      setError(`Export failed: ${errorMessage}`);
    } finally {
      setIsExporting(false);
      setCurrentFormat('');
    }
  };

  const handleSourceChange = (value: string) => {
    setSelectedSource(value);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Export Data</h1>
          <p className="text-gray-600 mt-1">
            Export your analytics data in various formats
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Select value={selectedSource} onValueChange={handleSourceChange}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select data source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Sources</SelectItem>
              {dataSources.map((source) => (
                <SelectItem key={source.value} value={source.value}>
                  {source.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      {/* Export Formats */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Database className="h-5 w-5 text-gray-600" />
          <h2 className="text-xl font-semibold text-gray-900">Available Export Formats</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {exportFormats.map((format) => (
            <ExportFormatCard
              key={format.type}
              format={format}
              onExport={handleExport}
              isExporting={isExporting}
              currentFormat={currentFormat}
            />
          ))}
        </div>
      </div>

      {/* Export History */}
      {exportJobs.length > 0 && (
        <div className="space-y-4">
          <Separator />
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-gray-600" />
            <h2 className="text-xl font-semibold text-gray-900">Export History</h2>
          </div>
          
          <div className="space-y-3">
            {exportJobs.slice(0, 5).map((job) => (
              <ExportJobCard key={job.id} job={job} />
            ))}
          </div>
        </div>
      )}

      {/* Data Source Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Filter className="h-5 w-5" />
            <span>Export Options</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium">Data Source</h4>
              <p className="text-sm text-gray-600">
                {selectedSource 
                  ? `Exporting data from: ${dataSources.find(s => s.value === selectedSource)?.label || selectedSource}`
                  : 'Exporting data from all available sources'
                }
              </p>
            </div>
            
            <div>
              <h4 className="font-medium">Export Content</h4>
              <p className="text-sm text-gray-600">
                Analytics data includes pattern analysis, user behavior, device usage, 
                temporal patterns, and recommendations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* No Data State */}
      {exportFormats.length === 0 && !error && (
        <Card>
          <CardContent className="text-center py-12">
            <Download className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Export Options Available</h3>
            <p className="text-gray-600">
              Export options are currently unavailable. Please try again later.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ExportPage;

