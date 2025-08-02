import React from 'react';

export interface Option<T extends string> {
  value: T;
  label: string;
}

export interface SelectProps<T extends string = string>
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'value' | 'onChange'> {
  value: T | T[];
  onChange: (value: T | T[]) => void;
  options: Option<T>[];
  multiple?: boolean;
  placeholder?: string;
  className?: string;
}

export const Select = <T extends string,>({
  value,
  onChange,
  options,
  multiple = false,
  placeholder,
  className = '',
  ...rest
}: SelectProps<T>) => {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (multiple) {
      const selected = Array.from(e.target.selectedOptions).map(o => o.value as T);
      onChange(selected as T[]);
    } else {
      onChange(e.target.value as T);
    }
  };

  return (
    <select
      multiple={multiple}
      value={value}
      onChange={handleChange}
      className={`border rounded-md px-2 py-1 ${className}`}
      {...rest}
    >
      {!multiple && placeholder && <option value="">{placeholder}</option>}
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
};

export default Select;
