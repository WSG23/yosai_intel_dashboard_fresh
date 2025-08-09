import React, { useState } from 'react';
import type { ExportOptions } from '../../hooks/useExportData';

interface Props {
  onExport: (options: ExportOptions) => void;
  progress: number;
  status: 'idle' | 'exporting' | 'completed' | 'error';
  onCancel: () => void;
}

const ExportForm: React.FC<Props> = ({ onExport, progress, status, onCancel }) => {
  const [fileType, setFileType] = useState('csv');
  const [columns, setColumns] = useState('');
  const [timezone, setTimezone] = useState('UTC');
  const [locale, setLocale] = useState('en-US');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const opts: ExportOptions = {
      fileType,
      columns: columns.split(',').map((c) => c.trim()).filter(Boolean),
      timezone,
      locale,
    };
    onExport(opts);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block mb-1">File Type</label>
        <select
          value={fileType}
          onChange={(e) => setFileType(e.target.value)}
          className="border p-1 rounded"
        >
          <option value="csv">CSV</option>
          <option value="json">JSON</option>
        </select>
      </div>
      <div>
        <label className="block mb-1">Columns (comma separated)</label>
        <input
          type="text"
          value={columns}
          onChange={(e) => setColumns(e.target.value)}
          className="border p-1 rounded w-full"
        />
      </div>
      <div>
        <label className="block mb-1">Timezone</label>
        <input
          type="text"
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          className="border p-1 rounded w-full"
        />
      </div>
      <div>
        <label className="block mb-1">Locale</label>
        <input
          type="text"
          value={locale}
          onChange={(e) => setLocale(e.target.value)}
          className="border p-1 rounded w-full"
        />
      </div>
      <div className="flex items-center space-x-2">
        <button type="submit" className="btn btn-primary" disabled={status === 'exporting'}>
          Export
        </button>
        {status === 'exporting' && (
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
      {status !== 'idle' && (
        <div className="mt-4" role="status" aria-live="polite">
          {status === 'exporting' && (
            <div className="flex items-center space-x-2">
              <progress value={progress} max="100" className="flex-1" />
              <span>{progress}%</span>
            </div>
          )}
          {status === 'completed' && <p className="text-green-600">Export complete.</p>}
          {status === 'error' && <p className="text-red-600">Export failed.</p>}
        </div>
      )}
    </form>
  );
};

export default ExportForm;
