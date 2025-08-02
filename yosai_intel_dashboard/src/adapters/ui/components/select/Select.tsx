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
  /**
   * Enables an internal search box that filters the available options.
   */
  searchable?: boolean;
}

export const Select: React.FC<SelectProps> = ({
  value,
  onChange,
  options,
  multiple = false,
  placeholder,
  className = '',
  searchable = false,
  ...rest
}) => {
  const [query, setQuery] = React.useState('');
  const filtered = React.useMemo(() => {
    return options.filter(o =>
      o.label.toLowerCase().includes(query.toLowerCase())
    );
  }, [options, query]);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (multiple) {
      const selected = Array.from(e.target.selectedOptions).map(o => o.value);
      onChange(selected);
    } else {
      onChange(e.target.value);
    }
  };

  const renderSelect = (
    <select
      multiple={multiple}
      value={value}
      onChange={handleChange}
      className={`border rounded-md px-2 py-1 ${className}`}
      {...rest}
    >
      {!multiple && placeholder && <option value="">{placeholder}</option>}
      {filtered.map(opt => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );

  if (!searchable) {
    return renderSelect;
  }

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Search..."
        aria-label="Search options"
        className="mb-2 border px-2 py-1"
      />
      {renderSelect}
    </div>
  );
};

export default Select;
