import { useMutation } from '@tanstack/react-query';
import { analyticsAPI } from '../api/analytics';
import { validateFileType, ExportType } from '../utils/exportTransforms';

interface ExportParams {
  format: string;
  dataSource?: string;
  columns?: string[];
}

const useExportData = () =>
  useMutation<Blob, Error, ExportParams>({
    mutationFn: async ({ format, dataSource }: ExportParams) => {
      if (!validateFileType(format)) {
        throw new Error(`Unsupported export format: ${format}`);
      }
      return analyticsAPI.exportData(format as ExportType, dataSource);
    },
  });

export default useExportData;
