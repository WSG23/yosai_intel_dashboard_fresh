export const SUPPORTED_EXPORT_TYPES = ['csv', 'excel', 'json'] as const;
export type ExportType = typeof SUPPORTED_EXPORT_TYPES[number];

/**
 * Validates that a file type is supported for export.
 */
export function validateFileType(type: string): type is ExportType {
  return (SUPPORTED_EXPORT_TYPES as readonly string[]).includes(type);
}

/**
 * Normalizes a list of column names by trimming whitespace,
 * removing empties and duplicates.
 */
export function normalizeColumns(columns: string[]): string[] {
  return Array.from(new Set(columns.map(c => c.trim()).filter(Boolean)));
}
