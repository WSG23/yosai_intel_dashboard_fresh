import React from 'react';

interface Option {
  value: string;
  label: string;
}

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  value: string | string[];
  onChange: (value: any) => void;
  options: Option[];
  multiple?: boolean;
  placeholder?: string;
  className?: string;
}

export const Select: React.FC<Props> = ({
  value,
  onChange,
  options,
  multiple = false,
  placeholder,
  className = '',
  ...rest
}) => {
  const displayOptions = React.useMemo(() => {
    return !multiple && placeholder
      ? [{ value: '', label: placeholder }, ...options]
      : options;
  }, [options, placeholder, multiple]);

  const [focusIndex, setFocusIndex] = React.useState(0);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const selectOption = (index: number) => {
    const opt = displayOptions[index];
    if (!opt) return;
    if (multiple) {
      const current = Array.isArray(value) ? value : [];
      if (current.includes(opt.value)) {
        onChange(current.filter(v => v !== opt.value));
      } else {
        onChange([...current, opt.value]);
      }
    } else {
      onChange(opt.value);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusIndex(i => Math.min(i + 1, displayOptions.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusIndex(i => Math.max(i - 1, 0));
        break;
      case 'Home':
        e.preventDefault();
        setFocusIndex(0);
        break;
      case 'End':
        e.preventDefault();
        setFocusIndex(displayOptions.length - 1);
        break;
      case 'Enter':
        e.preventDefault();
        selectOption(focusIndex);
        break;
      case 'Escape':
        e.preventDefault();
        setFocusIndex(-1);
        containerRef.current?.blur();
        break;
    }
  };

  return (
    <div
      {...rest}
      ref={containerRef}
      tabIndex={0}
      role="listbox"
      onKeyDown={handleKeyDown}
      className={`border rounded-md px-2 py-1 ${className}`}
    >
      {displayOptions.map((opt, index) => {
        const selected = multiple
          ? Array.isArray(value) && value.includes(opt.value)
          : value === opt.value;
        const focused = index === focusIndex;
        return (
          <div
            key={opt.value}
            role="option"
            aria-selected={selected}
            data-focused={focused}
            className={focused ? 'bg-blue-500 text-white' : ''}
            onMouseEnter={() => setFocusIndex(index)}
            onClick={() => selectOption(index)}
          >
            {opt.label}
          </div>
        );
      })}
    </div>
  );
};
