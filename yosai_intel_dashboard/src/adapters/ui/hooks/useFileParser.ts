import { useCallback } from 'react';
import { read, utils } from 'xlsx';

export interface ParsedData {
  rows: any[];
  columns: string[];
  devices: string[];
}

const sanitizeUnicode = (text: string): string => {
  const surrogatePattern = /[\uD800-\uDFFF]/g;
  let cleaned = text.replace(surrogatePattern, '');
  if ('normalize' in String.prototype) {
    cleaned = cleaned.normalize('NFKC');
  }
  cleaned = cleaned.replace(/[\u200B-\u200D\uFEFF]/g, '');
  return cleaned;
};

const parseCSV = (content: string): ParsedData => {
  const lines = content.split(/\r?\n/).filter(l => l.trim());
  if (lines.length === 0) return { rows: [], columns: [], devices: [] };
  const headers = lines[0].split(',').map(h => sanitizeUnicode(h.trim()));
  const rows = lines.slice(1).map(line => {
    const values = line.split(',');
    return headers.reduce((obj: any, header, idx) => {
      obj[header] = sanitizeUnicode(values[idx]?.trim() || '');
      return obj;
    }, {});
  });
  const deviceColumn = headers.find(h => h.toLowerCase().includes('door') || h.toLowerCase().includes('device'));
  const devices = deviceColumn ? Array.from(new Set(rows.map(r => r[deviceColumn]))) : [];
  return { rows, columns: headers, devices };
};

const parseJSON = (content: string): ParsedData => {
  const data = JSON.parse(content);
  const rows = Array.isArray(data) ? data : data.rows || [];
  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
  const deviceColumn = columns.find(h => h.toLowerCase().includes('door') || h.toLowerCase().includes('device'));
  const devices = deviceColumn ? Array.from(new Set(rows.map((r: any) => r[deviceColumn]))) : [];
  return { rows, columns, devices };
};

const parseXLSX = async (file: File): Promise<ParsedData> => {
  const data = await file.arrayBuffer();
  const workbook = read(data, { type: 'array' });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  const rows: any[] = utils.sheet_to_json(sheet);
  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
  const deviceColumn = columns.find(h => h.toLowerCase().includes('door') || h.toLowerCase().includes('device'));
  const devices = deviceColumn ? Array.from(new Set(rows.map(r => r[deviceColumn]))) : [];
  return { rows, columns, devices };
};

export const useFileParser = () => {
  const getText = async (file: File) => {
    if (typeof (file as any).text === 'function') {
      return (file as any).text();
    }
    return new Response(file).text();
  };

  const parseFile = useCallback(async (file: File): Promise<ParsedData> => {
    const ext = file.name.toLowerCase();
    if (ext.endsWith('.csv')) {
      const text = await getText(file);
      return parseCSV(text);
    }
    if (ext.endsWith('.json')) {
      const text = await getText(file);
      return parseJSON(text);
    }
    if (ext.endsWith('.xlsx') || ext.endsWith('.xls')) {
      return parseXLSX(file);
    }
    return { rows: [], columns: [], devices: [] };
  }, []);

  return { parseFile };
};

export default useFileParser;
