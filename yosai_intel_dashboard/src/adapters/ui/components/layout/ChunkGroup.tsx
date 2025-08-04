import React, { useState } from 'react';

interface ChunkGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  children: React.ReactNode;
  className?: string;
  limit?: number; // number of visible elements before collapsing
}

const ChunkGroup: React.FC<ChunkGroupProps> = ({
  title,
  children,
  className = '',
  limit = 7,
  ...rest
}) => {
  const items = React.Children.toArray(children);
  const [expanded, setExpanded] = useState(false);
  const hasMore = items.length > limit;
  const visible = expanded ? items : items.slice(0, limit);

  return (
    <div className={className} {...rest}>
      {title && <h3 className="mb-2 font-semibold">{title}</h3>}
      {visible}
      {hasMore && (
        <button
          type="button"
          className="mt-2 text-sm text-blue-600 underline"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Show Less' : 'Show More'}
        </button>
      )}
    </div>
  );
};

export default ChunkGroup;
