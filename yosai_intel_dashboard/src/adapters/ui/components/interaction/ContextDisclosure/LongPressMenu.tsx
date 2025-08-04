import React, { useState, useRef, ReactNode } from 'react';
import { useContextDisclosureShortcuts } from './Shortcuts';

interface LongPressMenuProps {
  preview: ReactNode;
  children: ReactNode;
  delay?: number;
}

const LongPressMenu: React.FC<LongPressMenuProps> = ({ preview, children, delay = 500 }) => {
  const [expanded, setExpanded] = useState(false);
  const timerRef = useRef<number>();

  useContextDisclosureShortcuts(
    () => setExpanded(true),
    () => setExpanded(false)
  );

  const startPress = () => {
    timerRef.current = window.setTimeout(() => setExpanded(true), delay);
  };

  const cancelPress = () => {
    window.clearTimeout(timerRef.current);
    setExpanded(false);
  };

  return (
    <div
      onMouseDown={startPress}
      onMouseUp={cancelPress}
      onMouseLeave={cancelPress}
      onTouchStart={startPress}
      onTouchEnd={cancelPress}
    >
      {expanded ? children : preview}
    </div>
  );
};

export default LongPressMenu;
