import React from 'react';

export interface Option<T extends string> {
  value: T;
  label: string;
}

interface Props<T extends string> extends React.SelectHTMLAttributes<HTMLSelectElement> {
  value: T | T[];
  onChange: (value: T | T[]) => void;
  options: Option<T>[];
  multiple?: boolean;
  placeholder?: string;
  className?: string;
}

export const Select = <T extends string>({
  value,
  onChange,
  options,
  multiple = false,
  placeholder,
  className = '',
  ...rest
}: Props<T>) => {
  return (
    <select
      multiple={multiple}
      value={value}
      {...rest}
      onChange={(e) => {
        if (multiple) {
          const selected = Array.from(e.target.selectedOptions).map(o => o.value as T);
          onChange(selected);
        } else {
          onChange(e.target.value as T);
        }
      }}
      className={`border rounded-md px-2 py-1 ${className}`}
    >
      {!multiple && placeholder && <option value="">{placeholder}</option>}
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  );
};

