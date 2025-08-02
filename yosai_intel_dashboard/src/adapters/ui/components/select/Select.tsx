import React from 'react';

interface Option {
  value: string;
  label: string;
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'value' | 'onChange'> {
  value: string | string[];
  onChange: (value: string | string[]) => void;
  options: Option[];
  multiple?: boolean;
  placeholder?: string;
  className?: string;
}

export const Select: React.FC<SelectProps> = ({
  value,
  onChange,
  options,
  multiple = false,
  placeholder,
  className = '',
  ...rest
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (multiple) {
      const selected = Array.from(e.target.selectedOptions).map(o => o.value);
      onChange(selected);
    } else {
      onChange(e.target.value);
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
