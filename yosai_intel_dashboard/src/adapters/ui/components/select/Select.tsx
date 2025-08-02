import React from 'react';

export interface Option<T extends string> {
  value: T;
  label: string;
}

export interface SelectProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
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

export const Select = <T extends string,>({
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
      const current = Array.isArray(value) ? [...value] : [];
      const index = current.indexOf(val);
      if (index > -1) {
        current.splice(index, 1);
      } else {
        current.push(val);
      }
      onChange(current);
      setSearch('');
    } else {
      onChange(val);
      const selectedOpt = options.find(o => o.value === val);
      setSearch(selectedOpt ? selectedOpt.label : '');
      setIsOpen(false);
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

