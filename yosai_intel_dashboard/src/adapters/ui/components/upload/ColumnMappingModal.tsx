import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { ExclamationTriangleIcon, CheckIcon } from '@heroicons/react/24/outline';
import { Button } from '../shared/Button';
import { Select } from '../select/Select';
import { Badge } from '../shared/Badge';
import { FileData } from './types';

interface ColumnMapping {
  originalColumn: string;
  mappedTo: string;
  confidence: number;
  isRequired: boolean;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  fileData: FileData | null;
  onConfirm: (mappings: Record<string, string>) => void;
}

const STANDARD_FIELDS = [
  { value: 'person_id', label: 'Person/User ID', required: true },
  { value: 'door_id', label: 'Door/Location ID', required: true },
  { value: 'timestamp', label: 'Timestamp', required: true },
  { value: 'access_result', label: 'Access Result', required: true },
  { value: 'token_id', label: 'Token/Badge ID' },
  { value: 'badge_status', label: 'Badge Status' },
  { value: 'device_status', label: 'Device Status' },
  { value: 'event_type', label: 'Event Type' },
  { value: 'building_id', label: 'Building/Floor' },
  { value: 'entry_type', label: 'Entry/Exit Type' },
  { value: 'duration', label: 'Duration' },
  { value: 'ignore', label: 'Ignore Column' },
];

export const ColumnMappingModal: React.FC<Props> = ({
  isOpen,
  onClose,
  fileData,
  onConfirm,
}) => {
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    if (fileData?.columns && fileData?.ai_suggestions) {
      const columnMappings: ColumnMapping[] = fileData.columns.map((col: string) => {
        const suggestion = fileData.ai_suggestions[col] || {};
        const field = STANDARD_FIELDS.find(f => f.value === suggestion.field);
        
        return {
          originalColumn: col,
          mappedTo: suggestion.field || '',
          confidence: suggestion.confidence || 0,
          isRequired: field?.required || false,
        };
      });
      
      setMappings(columnMappings);
    }
  }, [fileData]);

  const handleMappingChange = (index: number, value: string) => {
    setMappings(prev => prev.map((m, i) => 
      i === index ? { ...m, mappedTo: value } : m
    ));
  };

  const validateMappings = (): boolean => {
    const newErrors: string[] = [];
    const requiredFields = STANDARD_FIELDS.filter(f => f.required).map(f => f.value);
    const mappedFields = mappings.map(m => m.mappedTo).filter(Boolean);
    
    // Check for required fields
    requiredFields.forEach(field => {
      if (!mappedFields.includes(field)) {
        const fieldLabel = STANDARD_FIELDS.find(f => f.value === field)?.label;
        newErrors.push(`${fieldLabel} is required`);
      }
    });
    
    // Check for duplicates (except 'ignore')
    const duplicates = mappedFields.filter((item, index) => 
      item !== 'ignore' && mappedFields.indexOf(item) !== index
    );
    
    if (duplicates.length > 0) {
      newErrors.push(`Duplicate mappings found: ${duplicates.join(', ')}`);
    }
    
    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleConfirm = () => {
    if (validateMappings()) {
      const mappingDict = mappings.reduce((acc, m) => {
        if (m.mappedTo && m.mappedTo !== 'ignore') {
          acc[m.originalColumn] = m.mappedTo;
        }
        return acc;
      }, {} as Record<string, string>);
      
      onConfirm(mappingDict);
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) {
      return <Badge variant="success">High ({Math.round(confidence * 100)}%)</Badge>;
    } else if (confidence >= 0.5) {
      return <Badge variant="warning">Medium ({Math.round(confidence * 100)}%)</Badge>;
    } else {
      return <Badge variant="danger">Low ({Math.round(confidence * 100)}%)</Badge>;
    }
  };

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      className="fixed inset-0 z-50 overflow-y-auto"
    >
      <div className="flex min-h-screen items-center justify-center p-4">
        
        <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
          <Dialog.Title className="text-xl font-semibold p-6 border-b border-gray-200 dark:border-gray-700">
            AI Column Mapping - {fileData?.filename}
          </Dialog.Title>
          
          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {/* Info Alert */}
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-start gap-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <p className="font-medium mb-1">AI has analyzed your columns and made suggestions.</p>
                <p>Review and correct any mistakes. Your corrections help improve future suggestions.</p>
              </div>
            </div>

            {/* Mapping Table */}
            <div className="space-y-4">
              <table className="w-full">
                <caption className="sr-only">Column mappings</caption>
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th scope="col" className="text-left py-3 px-4">Original Column</th>
                    <th scope="col" className="text-left py-3 px-4">AI Confidence</th>
                    <th scope="col" className="text-left py-3 px-4">Map to Field</th>
                  </tr>
                </thead>
                <tbody>
                  {mappings.map((mapping, index) => (
                    <tr 
                      key={index}
                      className="border-b border-gray-100 dark:border-gray-700/50"
                    >
                      <td className="py-3 px-4">
                        <div className="font-medium">{mapping.originalColumn}</div>
                        {fileData?.sample_data && (
                          <div className="text-xs text-gray-500 mt-1">
                            Sample: {fileData.sample_data[mapping.originalColumn]?.slice(0, 3).join(', ')}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {mapping.confidence > 0 && getConfidenceBadge(mapping.confidence)}
                      </td>
                      <td className="py-3 px-4">
                        <Select
                          value={mapping.mappedTo}
                          onChange={(value) => handleMappingChange(index, value)}
                          options={STANDARD_FIELDS}
                          aria-label={`Map column ${mapping.originalColumn}`}
                          className={mapping.confidence < 0.5 ? 'border-yellow-500' : ''}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Errors */}
            {errors.length > 0 && (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <p className="font-medium text-red-800 dark:text-red-200 mb-2">
                  Please fix the following issues:
                </p>
                <ul className="list-disc list-inside text-sm text-red-700 dark:text-red-300">
                  {errors.map((error, i) => (
                    <li key={i}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          
          <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleConfirm}
              icon={<CheckIcon className="h-5 w-5" />}
            >
              Confirm & Continue
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
};
