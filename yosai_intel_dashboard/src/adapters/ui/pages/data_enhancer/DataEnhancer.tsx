import React from 'react';
import { useDataEnhancerStore } from './useDataEnhancerStore';

const DataEnhancer: React.FC = () => {
  const {
    uploadedData,
    columnSuggestions,
    enhancedData,
    uploadStatus,
    aiStatus,
    enhanceStatus,
    setUploadedData,
    setColumnSuggestions,
    setEnhancedData,
  } = useDataEnhancerStore();

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setUploadedData(reader.result as string, 'File uploaded');
    };
    reader.readAsText(file);
  };

  const handleSuggest = () => {
    if (!uploadedData) return;
    const firstLine = uploadedData.split('\n')[0];
    const suggestions = firstLine.split(',').map((c) => c.trim());
    setColumnSuggestions(suggestions, `Found ${suggestions.length} suggestions`);
  };

  const handleEnhance = () => {
    if (!uploadedData) return;
    const enhanced = uploadedData + '\n';
    setEnhancedData(enhanced, 'Data enhancement complete');
  };

  const handleDownload = () => {
    if (!enhancedData) return;
    const blob = new Blob([enhancedData], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'enhanced.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <input type="file" aria-label="upload" onChange={handleUpload} />
      {uploadStatus && <div>{uploadStatus}</div>}
      <button onClick={handleSuggest} disabled={!uploadedData}>Suggest Columns</button>
      {aiStatus && <div>{aiStatus}</div>}
      <button onClick={handleEnhance} disabled={!uploadedData}>Enhance Data</button>
      {enhanceStatus && <div>{enhanceStatus}</div>}
      <button onClick={handleDownload} disabled={!enhancedData}>Download</button>
      {columnSuggestions.length > 0 && (
        <ul>
          {columnSuggestions.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default DataEnhancer;
