import React, { useEffect, useState } from 'react';

interface CollapsiblePanelProps {
  id: string;
  title: string;
  children: React.ReactNode;
  collapseAfter?: number; // milliseconds
}

const STORAGE_PREFIX = 'panel-collapsed-';

const CollapsiblePanel: React.FC<CollapsiblePanelProps> = ({
  id,
  title,
  children,
  collapseAfter,
}) => {
  const storageKey = `${STORAGE_PREFIX}${id}`;
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    try {
      return localStorage.getItem(storageKey) === 'true';
    } catch {
      return false;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, String(collapsed));
    } catch {
      /* ignore */
    }
  }, [collapsed, storageKey]);

  useEffect(() => {
    if (!collapseAfter || collapsed) return;
    const timer = setTimeout(() => setCollapsed(true), collapseAfter);
    return () => clearTimeout(timer);
  }, [collapseAfter, collapsed]);

  const toggle = () => setCollapsed((c) => !c);

  return (
    <div>
      <button onClick={toggle} aria-expanded={!collapsed}>
        {title}
      </button>
      {!collapsed && <div>{children}</div>}
    </div>
  );
};

export default CollapsiblePanel;
