import React, { useEffect, useRef, useState } from 'react';
import './highContrast.css';
import { useVoiceNavigation } from './useVoiceNavigation';
import { useHighContrast } from './useHighContrast';

interface TableData {
  headers: string[];
  rows: (string | number)[][];
}

interface AccessibleVisualizationProps {
  title: string;
  summary: string;
  tableData: TableData;
  children: React.ReactNode;
}

export const AccessibleVisualization: React.FC<AccessibleVisualizationProps> = ({
  title,
  summary,
  tableData,
  children,
}) => {
  const [showTable, setShowTable] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useHighContrast();
  useEffect(() => {
    if ('speechSynthesis' in window) {
      const utter = new SpeechSynthesisUtterance(summary);
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utter);
    }
  }, [summary]);

  const toggleView = () => setShowTable((v) => !v);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleView();
    }
  };

  useVoiceNavigation({
    'show table': () => setShowTable(true),
    'show chart': () => setShowTable(false),
  });

  return (
    <div ref={containerRef} role="region" aria-label={title} className="accessible-viz">
      <div className="sr-only" aria-live="polite">
        {summary}
      </div>
      <button
        onClick={toggleView}
        onKeyDown={handleKeyDown}
        aria-pressed={showTable}
        aria-label={showTable ? 'Show chart view' : 'Show table view'}
      >
        {showTable ? 'Show Chart' : 'Show Table'}
      </button>
      {showTable ? (
        <table role="table" className="a11y-table">
          <thead>
            <tr>
              {tableData.headers.map((h) => (
                <th key={h} scope="col">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.rows.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => (
                  <td key={j}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div role="img" aria-label={`${title} visualization`} tabIndex={0}>
          {children}
        </div>
      )}
    </div>
  );
};

export default AccessibleVisualization;
