import React from 'react';
import useInteractionMode from '../../hooks/useInteractionMode';
import './ResponsiveShell.css';

interface Props {
  left?: React.ReactNode;
  right?: React.ReactNode;
  children: React.ReactNode;
}

/**
 * Renders a responsive shell that exposes additional panels on large screens.
 * For small viewports only the main content is displayed.
 */
const ResponsiveShell: React.FC<Props> = ({ left, right, children }) => {
  useInteractionMode();

  return (
    <div className="responsive-shell">
      {left && (
        <aside className="responsive-shell__panel responsive-shell__panel--left">
          {left}
        </aside>
      )}
      <main className="responsive-shell__main">{children}</main>
      {right && (
        <aside className="responsive-shell__panel responsive-shell__panel--right">
          {right}
        </aside>
      )}
    </div>
  );
};

export default ResponsiveShell;
