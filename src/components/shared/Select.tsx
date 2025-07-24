import React from 'react';

interface Option { value: string; label: string; }
interface Props extends React.SelectHTMLAttributes<HTMLSelectElement> {
  value: string | string[];
  onChange: (value: any) => void;
  options: Option[];
  multiple?: boolean;
  placeholder?: string;
  className?: string;
}

export const Select: React.FC<Props> = ({ value, onChange, options, multiple = false, placeholder, className='', ...rest }) => {
  return (
    <select
      multiple={multiple}
      value={value}
      {...rest}
      onChange={(e) => {
        if (multiple) {
          const selected = Array.from(e.target.selectedOptions).map(o => o.value);
          onChange(selected);
        } else {
          onChange(e.target.value);
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
