import React, { useState } from 'react';
import useExportData from '../../hooks/useExportData';
import { Button } from '../shared/Button';
import {
  SUPPORTED_EXPORT_TYPES,
  normalizeColumns,
  validateFileType,
} from '../../utils/exportTransforms';

const ExportForm: React.FC = () => {
  const [format, setFormat] = useState<string>('csv');
  const [columns, setColumns] = useState<string>('');
  const { mutateAsync } = useExportData();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateFileType(format)) {
      alert('Unsupported export format');
      return;
    }
    const columnList = normalizeColumns(columns.split(','));
    await mutateAsync({ format, columns: columnList });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block mb-1">Format</label>
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value)}
          className="border rounded p-2 w-full"
        >
          {SUPPORTED_EXPORT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t.toUpperCase()}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block mb-1">Columns (comma separated)</label>
        <input
          type="text"
          value={columns}
          onChange={(e) => setColumns(e.target.value)}
          className="border rounded p-2 w-full"
          placeholder="e.g. person_id,door_id,timestamp"
        />
      </div>
      <Button type="submit">Export</Button>
    </form>
  );
};

export default ExportForm;
