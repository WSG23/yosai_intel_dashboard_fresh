import React, { useState, ReactNode } from 'react';
import { useContextDisclosureShortcuts } from './Shortcuts';

interface HoverPreviewProps {
  preview: ReactNode;
  children: ReactNode;
}

const HoverPreview: React.FC<HoverPreviewProps> = ({ preview, children }) => {
  const [expanded, setExpanded] = useState(false);

  useContextDisclosureShortcuts(
    () => setExpanded(true),
    () => setExpanded(false)
  );

  return (
    <div
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      {expanded ? children : preview}
    </div>
  );
};

export default HoverPreview;
