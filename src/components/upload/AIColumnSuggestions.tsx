import React from 'react';
import { ParsedData } from '../../hooks/useFileParser';

interface Props {
  data: ParsedData | null;
}

export const AIColumnSuggestions: React.FC<Props> = ({ data }) => {
  if (!data) return null;
  return (
    <div className="mt-3">
      <h6>Columns Detected:</h6>
      <ul>
        {data.columns.map(col => (
          <li key={col}>{col}</li>
        ))}
      </ul>
    </div>
  );
};

export default AIColumnSuggestions;
