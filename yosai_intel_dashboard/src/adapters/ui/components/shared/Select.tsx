import React, { useId, useState } from 'react';

interface Option { value: string; label: string; }
interface Props extends React.SelectHTMLAttributes<HTMLSelectElement> {
  value: string | string[];
  onChange: (value: any) => void;
  options: Option[];
  multiple?: boolean;
  placeholder?: string;
  className?: string;
  label?: string;
}

export const Select: React.FC<Props> = ({
  value,
  onChange,
  options,
  multiple = false,
  placeholder,
  className = '',
  label,
  id,
  onFocus,
  onBlur,
  ...rest
}) => {
  const generatedId = useId();
  const selectId = id || generatedId;
  const [expanded, setExpanded] = useState(false);

  const handleFocus = (e: React.FocusEvent<HTMLSelectElement>) => {
    setExpanded(true);
    onFocus?.(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLSelectElement>) => {
    setExpanded(false);
    onBlur?.(e);
  };

  const activeDescendant =
    !multiple && typeof value === 'string' && value !== ''
      ? `${selectId}-option-${value}`
      : undefined;

  return (
    <>
      {label && (
        <label htmlFor={selectId} className="sr-only">
          {label}
        </label>
      )}
      <select
        id={selectId}
        multiple={multiple}
        value={value}
        role={multiple ? 'listbox' : 'combobox'}
        aria-expanded={expanded}
        aria-activedescendant={activeDescendant}
        aria-multiselectable={multiple || undefined}
        {...rest}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onChange={(e) => {
          if (multiple) {
            const selected = Array.from(e.target.selectedOptions).map((o) => o.value);
            onChange(selected);
          } else {
            onChange(e.target.value);
          }
        }}
        className={`border rounded-md px-2 py-1 ${className}`}
      >
        {!multiple && placeholder && (
          <option role="option" id={`${selectId}-option-`} value="">
            {placeholder}
          </option>
        )}
        {options.map((opt) => (
          <option role="option" id={`${selectId}-option-${opt.value}`} key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </>
  );
};
