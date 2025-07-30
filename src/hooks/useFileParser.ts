import { useCallback } from 'react';
import * as XLSX from 'xlsx';

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

export const parseCSV = (content: string): ParsedData => {
  const rows: string[][] = [];
  let field = '';
  let row: string[] = [];
  let inQuotes = false;

  for (let i = 0; i < content.length; i++) {
    const ch = content[i];
    if (ch === '"') {
      if (inQuotes && content[i + 1] === '"') {
        field += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      row.push(field);
      field = '';
    } else if ((ch === '\n' || ch === '\r') && !inQuotes) {
      if (ch === '\r' && content[i + 1] === '\n') i++;
      row.push(field);
      rows.push(row);
      field = '';
      row = [];
    } else {
      field += ch;
    }
  }
  row.push(field);
  rows.push(row);

  if (rows.length === 0) return { rows: [], columns: [], devices: [] };
  const headers = rows[0].map(h => sanitizeUnicode(h.trim()));
  const dataRows = rows.slice(1).filter(r => r.length && r.some(v => v.length > 0));
  const dataObjects = dataRows.map(r => {
    const obj: any = {};
    headers.forEach((header, idx) => {
      obj[header] = sanitizeUnicode((r[idx] || '').trim());
    });
    return obj;
  });
  const deviceColumn = headers.find(h => h.toLowerCase().includes('door') || h.toLowerCase().includes('device'));
  const devices = deviceColumn ? Array.from(new Set(dataObjects.map(r => r[deviceColumn]))) : [];
  return { rows: dataObjects, columns: headers, devices };
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
  const workbook = XLSX.read(data, { type: 'array' });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  const rows: any[] = XLSX.utils.sheet_to_json(sheet);
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
