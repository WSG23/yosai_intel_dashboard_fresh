import React, { useState } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { Stepper, Step } from '../components/interaction';
import { isFeatureEnabled } from '../plugins/featureFlags';


interface Filter {
  id: number;
  field: string;
  value: string;
}

const availableFilters = [
  { field: 'source', label: 'Source' },
  { field: 'device', label: 'Device' },
  { field: 'severity', label: 'Severity' },
  { field: 'status', label: 'Status' },
];

const QueryBuilder: React.FC = () => {
  const [filters, setFilters] = useState<Filter[]>([]);
  const showPreview = isFeatureEnabled('queryPreview', 'demo-user');

  const onDragStart = (e: React.DragEvent, field: string) => {
    e.dataTransfer.setData('field', field);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const field = e.dataTransfer.getData('field');
    setFilters((prev) => [...prev, { id: Date.now(), field, value: '' }]);
  };

  const updateValue = (id: number, value: string) => {
    setFilters((prev) => prev.map((f) => (f.id === id ? { ...f, value } : f)));
  };

  const removeFilter = (id: number) => {
    setFilters((prev) => prev.filter((f) => f.id !== id));
  };

  const preview = filters
    .map((f) => `${f.field}:${f.value || '*'}`)
    .join(' AND ');

  const steps: Step<{ filters: Filter[] }>[] = [
    {
      id: 'build',
      label: 'Build Query',
      content: (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h2 className="font-semibold mb-2">Available Filters</h2>
            <div className="space-y-2">
              {availableFilters.map((f) => (
                <div
                  key={f.field}
                  draggable
                  onDragStart={(e) => onDragStart(e, f.field)}
                  className="border p-2 rounded cursor-move bg-gray-50"
                >
                  {f.label}
                </div>
              ))}
            </div>
          </div>
          <div>
            <h2 className="font-semibold mb-2">Build Query</h2>
            <div
              onDrop={onDrop}
              onDragOver={(e) => e.preventDefault()}
              className="min-h-[150px] border-2 border-dashed p-2 rounded"
            >
              {filters.map((f) => (
                <div
                  key={f.id}
                  className="flex items-center space-x-2 mb-2 bg-white p-2 rounded shadow"
                >
                  <span className="font-medium">{f.field}</span>
                  <input
                    value={f.value}
                    onChange={(e) => updateValue(f.id, e.target.value)}
                    className="border p-1 flex-1 rounded"
                  />
                  <button
                    onClick={() => removeFilter(f.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    &times;
                  </button>
                </div>
              ))}
              {filters.length === 0 && (
                <p className="text-gray-500 text-sm">Drag filters here</p>
              )}
            </div>
          </div>

        </div>
      ),
      next: (ctx) => (showPreview && ctx.filters.length > 0 ? 'preview' : undefined),
    },
  ];

  if (showPreview) {
    steps.push({
      id: 'preview',
      label: 'Preview',
      optional: true,
      content: (
        <div>
          <h2 className="font-semibold mb-1">Query Preview</h2>
          <div className="border p-2 rounded bg-gray-50 text-sm min-h-[40px]">
            {preview || 'No filters applied'}
          </div>
        </div>
      ),
    });
  }

  return <Stepper steps={steps} context={{ filters }} />;
};

const QueryBuilderPage: React.FC = () => (
  <ErrorBoundary>
    <QueryBuilder />
  </ErrorBoundary>
);

export default QueryBuilderPage;
