import React from 'react';

export interface ColumnConfig<T> {
  key: keyof T;
  header: string;
  priority?: number; // 1 = highest (always visible), higher numbers hide on smaller screens
  render?: (value: any, row: T) => React.ReactNode;
}

interface ResponsiveTableProps<T> {
  data: T[];
  columns: ColumnConfig<T>[];
}

function priorityClass(priority = 1): string {
  switch (priority) {
    case 2:
      return 'hidden lg:table-cell';
    case 3:
      return 'hidden xl:table-cell';
    default:
      return '';
  }
}

export function ResponsiveTable<T extends Record<string, any>>({ data, columns }: ResponsiveTableProps<T>) {
  const [expandedRows, setExpandedRows] = React.useState<Set<number>>(new Set());

  const toggleRow = (idx: number) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  const highPriorityCols = columns.filter((c) => (c.priority ?? 1) === 1);
  const lowPriorityCols = columns.filter((c) => (c.priority ?? 1) > 1);

  return (
    <>
      {/* Card view for mobile */}
      <div data-testid="card-view" className="md:hidden space-y-4">
        {data.map((row, rowIndex) => (
          <div key={rowIndex} className="border rounded p-4">
            {highPriorityCols.map((col) => (
              <div key={String(col.key)} className="mb-1">
                <span className="font-medium">{col.header}: </span>
                <span>{col.render ? col.render(row[col.key], row) : String(row[col.key])}</span>
              </div>
            ))}
            {lowPriorityCols.length > 0 && (
              <>
                <button
                  className="mt-2 text-blue-600 underline"
                  onClick={() => toggleRow(rowIndex)}
                  aria-expanded={expandedRows.has(rowIndex)}
                >
                  {expandedRows.has(rowIndex) ? 'Hide details' : 'Show details'}
                </button>
                {expandedRows.has(rowIndex) && (
                  <div className="mt-2 space-y-1">
                    {lowPriorityCols.map((col) => (
                      <div key={String(col.key)}>
                        <span className="font-medium">{col.header}: </span>
                        <span>{col.render ? col.render(row[col.key], row) : String(row[col.key])}</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </div>

      {/* Table view for tablets and above */}
      <div data-testid="table-view" className="hidden md:block overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead className="sticky top-0 bg-white z-10">
            <tr>
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  className={`p-2 text-left border-b ${priorityClass(col.priority)}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIndex) => (
              <tr key={rowIndex} className="border-b">
                {columns.map((col) => (
                  <td
                    key={String(col.key)}
                    className={`p-2 ${priorityClass(col.priority)}`}
                  >
                    {col.render ? col.render(row[col.key], row) : String(row[col.key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default ResponsiveTable;
