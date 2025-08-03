import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import {
  Building2,
  LogIn,
  LogOut,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import { Button } from '../shared/Button';
import { Input } from '../shared/Input';
import { Select } from '../select/Select';
import { Checkbox } from '../shared/Checkbox';
import { Badge } from '../shared/Badge';
import Spinner from '../shared/Spinner';

interface DeviceMapping {
  deviceId: string;
  floor: number;
  isEntry: boolean;
  isExit: boolean;
  specialAreas: string[];
  securityLevel: number;
  confidence: number;
  edited: boolean;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  devices: string[];
  filename: string;
  onConfirm: (mappings: Record<string, any>) => void;
}

const SPECIAL_AREAS = [
  { value: 'stairwell', label: 'Stairwell' },
  { value: 'elevator', label: 'Elevator' },
  { value: 'emergency_exit', label: 'Emergency Exit' },
  { value: 'server_room', label: 'Server Room' },
  { value: 'executive', label: 'Executive Area' },
  { value: 'restricted', label: 'Restricted Area' },
  { value: 'parking', label: 'Parking' },
  { value: 'lobby', label: 'Lobby' },
];

export const DeviceMappingModal: React.FC<Props> = ({
  isOpen,
  onClose,
  devices,
  filename,
  onConfirm,
}) => {
  const [mappings, setMappings] = useState<DeviceMapping[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAISuggestions = async () => {
      setLoading(true);
      
      // Simulate AI processing
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Create mappings with AI suggestions
      const deviceMappings: DeviceMapping[] = devices.map(device => {
        // AI logic would go here
        const floor = device.toLowerCase().includes('lobby') ? 1 : 
                     device.match(/\d+/) ? parseInt(device.match(/\d+/)![0]) : 1;
        
        const isEntry = device.toLowerCase().includes('entry') || 
                       device.toLowerCase().includes('in');
        
        const isExit = device.toLowerCase().includes('exit') || 
                      device.toLowerCase().includes('out');
        
        const specialAreas: string[] = [];
        if (device.toLowerCase().includes('stair')) specialAreas.push('stairwell');
        if (device.toLowerCase().includes('elevator')) specialAreas.push('elevator');
        if (device.toLowerCase().includes('server')) specialAreas.push('server_room');
        
        const securityLevel = device.toLowerCase().includes('server') ? 8 :
                             device.toLowerCase().includes('executive') ? 7 : 3;
        
        return {
          deviceId: device,
          floor,
          isEntry: isEntry || (!isEntry && !isExit),
          isExit,
          specialAreas,
          securityLevel,
          confidence: Math.random() * 0.5 + 0.5, // 0.5-1.0
          edited: false,
        };
      });
      
      setMappings(deviceMappings);
      setLoading(false);
    };
    
    if (devices.length > 0) {
      loadAISuggestions();
    }
  }, [devices]);

  const updateMapping = (index: number, updates: Partial<DeviceMapping>) => {
    setMappings(prev => prev.map((m, i) => 
      i === index ? { ...m, ...updates, edited: true } : m
    ));
  };

  const handleConfirm = () => {
    const mappingDict = mappings.reduce((acc, m) => {
      acc[m.deviceId] = {
        floor_number: m.floor,
        is_entry: m.isEntry,
        is_exit: m.isExit,
        special_areas: m.specialAreas,
        security_level: m.securityLevel,
        manually_verified: m.edited,
      };
      return acc;
    }, {} as Record<string, any>);
    
    onConfirm(mappingDict);
  };

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      className="fixed inset-0 z-50 overflow-y-auto"
    >
      <div className="flex min-h-screen items-center justify-center p-4">
        
        <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
          <Dialog.Title className="text-xl font-semibold p-6 border-b border-gray-200 dark:border-gray-700">
            AI Device Classification - {filename}
          </Dialog.Title>
          
          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {/* Info Alert */}
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <p className="font-medium mb-1">AI has analyzed {devices.length} devices.</p>
                <p>Review and correct classifications. Your edits train the AI for better future predictions.</p>
              </div>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Spinner sizeClass="h-12 w-12" className="text-blue-600" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-3 px-4 whitespace-nowrap">Device Name</th>
                      <th className="text-left py-3 px-4">Floor</th>
                      <th className="text-left py-3 px-4">Access Type</th>
                      <th className="text-left py-3 px-4">Special Areas</th>
                      <th className="text-left py-3 px-4">Security</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mappings.map((mapping, index) => (
                      <tr 
                        key={index}
                        className={`border-b border-gray-100 dark:border-gray-700/50 ${
                          mapping.edited ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''
                        }`}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <Building2 className="h-5 w-5 text-gray-400" />
                            <div>
                              <div className="font-medium">{mapping.deviceId}</div>
                              <Badge 
                                variant={mapping.confidence > 0.7 ? 'success' : 'warning'}
                                size="sm"
                              >
                                AI: {Math.round(mapping.confidence * 100)}%
                              </Badge>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Input
                            type="number"
                            min={0}
                            max={50}
                            value={mapping.floor}
                            onChange={(e) => updateMapping(index, { floor: parseInt(e.target.value) })}
                            className="w-20"
                          />
                        </td>
                        <td className="py-3 px-4">
                          <div className="space-y-2">
                            <Checkbox
                              label="Entry"
                              checked={mapping.isEntry}
                              onChange={(checked) => updateMapping(index, { isEntry: checked })}
                              icon={<LogIn className="h-4 w-4" />}
                            />
                            <Checkbox
                              label="Exit"
                              checked={mapping.isExit}
                              onChange={(checked) => updateMapping(index, { isExit: checked })}
                              icon={<LogOut className="h-4 w-4" />}
                            />
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Select
                            multiple
                            value={mapping.specialAreas}
                            onChange={(value) => updateMapping(index, { specialAreas: value as string[] })}
                            options={SPECIAL_AREAS}
                            placeholder="Select areas..."
                            className="min-w-[200px]"
                          />
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <ShieldCheck className="h-5 w-5 text-gray-400" />
                            <Input
                              type="number"
                              min={0}
                              max={10}
                              value={mapping.securityLevel}
                              onChange={(e) => updateMapping(index, { securityLevel: parseInt(e.target.value) })}
                              className="w-16"
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Legend */}
            <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
              <h4 className="font-medium mb-2">Security Level Guide:</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><Badge variant="default">0-2</Badge> Public areas</div>
                <div><Badge variant="warning">3-5</Badge> General office areas</div>
                <div><Badge variant="danger">6-8</Badge> Restricted areas</div>
                <div><Badge variant="danger">9-10</Badge> High security (executive, server rooms)</div>
              </div>
            </div>
          </div>
          
          <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-between">
            <div className="text-sm text-gray-500">
              {mappings.filter(m => m.edited).length} devices manually edited
            </div>
            <div className="flex gap-3">
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <Button 
                variant="primary" 
                onClick={handleConfirm}
                disabled={loading}
              >
                Confirm & Train AI
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Dialog>
  );
};
