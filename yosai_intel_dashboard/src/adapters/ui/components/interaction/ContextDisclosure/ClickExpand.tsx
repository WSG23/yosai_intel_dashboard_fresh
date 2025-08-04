import React, { useState, ReactNode } from 'react';
import { useContextDisclosureShortcuts } from './Shortcuts';

interface ClickExpandProps {
  preview: ReactNode;
  children: ReactNode;
}

const ClickExpand: React.FC<ClickExpandProps> = ({ preview, children }) => {
  const [expanded, setExpanded] = useState(false);

  useContextDisclosureShortcuts(
    () => setExpanded(true),
    () => setExpanded(false)
  );

  return (
    <div onClick={() => setExpanded(!expanded)}>
      {expanded ? children : preview}
    </div>
  );
};

export default ClickExpand;
