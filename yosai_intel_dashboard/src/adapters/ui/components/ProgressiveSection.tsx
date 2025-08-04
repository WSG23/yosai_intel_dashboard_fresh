import React, { useState, useId } from 'react';

interface ProgressiveSectionProps {
  title: string;
  children: React.ReactNode;
  /** Whether the section starts expanded */
  initiallyExpanded?: boolean;
  /** Optional id for the content element */
  id?: string;
  className?: string;
}

/**
 * A reusable section that progressively reveals details on demand.
 * Content is hidden from assistive technologies until expanded.
 */
const ProgressiveSection: React.FC<ProgressiveSectionProps> = ({
  title,
  children,
  initiallyExpanded = false,
  id,
  className = '',
}) => {
  const [expanded, setExpanded] = useState(initiallyExpanded);
  const generatedId = useId();
  const contentId = id || generatedId;

  return (
    <section className={className}>
      <button
        type="button"
        aria-expanded={expanded}
        aria-controls={contentId}
        onClick={() => setExpanded((e) => !e)}
        className="progressive-section-toggle"
      >
        {title}
      </button>
      <div
        id={contentId}
        hidden={!expanded}
        aria-hidden={!expanded}
        className="progressive-section-content"
      >
        {children}
      </div>
    </section>
  );
};

export default ProgressiveSection;
