import React from 'react';
import { useUiStore } from '../../state';
import type { TableDensity } from '../../state/uiSlice';

const densities: { value: TableDensity; label: string }[] = [
  { value: 'compact', label: 'Compact' },
  { value: 'comfortable', label: 'Comfortable' },
  { value: 'spacious', label: 'Spacious' },
];

const TableDensitySwitcher: React.FC = () => {
  const { tableDensity, setTableDensity } = useUiStore();
  return (
    <div>
      {densities.map((d) => (
        <button
          key={d.value}
          onClick={() => setTableDensity(d.value)}
          aria-pressed={tableDensity === d.value}
        >
          {d.label}
        </button>
      ))}
    </div>
  );
};

export default TableDensitySwitcher;
