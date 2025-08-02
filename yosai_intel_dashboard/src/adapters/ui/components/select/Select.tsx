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
  if (!searchable) {
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
  }

  const [query, setQuery] = React.useState('');
  const [activeIndex, setActiveIndex] = React.useState(0);

  const filtered = React.useMemo(
    () =>
      options.filter(o =>
        o.label.toLowerCase().includes(query.toLowerCase())
      ),
    [options, query]
  );

  React.useEffect(() => {
    if (activeIndex > filtered.length - 1) {
      setActiveIndex(filtered.length - 1);
    }
  }, [filtered.length, activeIndex]);

  const selectOption = (index: number) => {
    const opt = filtered[index];
    if (!opt) return;
    if (multiple) {
      const current = Array.isArray(value) ? value : [];
      const exists = current.includes(opt.value);
      const next = exists
        ? current.filter(v => v !== opt.value)
        : [...current, opt.value];
      onChange(next);
    } else {
      onChange(opt.value);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!filtered.length) return;
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex(i => (i + 1) % filtered.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex(i => (i - 1 + filtered.length) % filtered.length);
        break;
      case 'Home':
        e.preventDefault();
        setActiveIndex(0);
        break;
      case 'End':
        e.preventDefault();
        setActiveIndex(filtered.length - 1);
        break;
      case 'Enter':
        e.preventDefault();
        selectOption(activeIndex);
        break;
      case 'Escape':
        e.preventDefault();
        setQuery('');
        setActiveIndex(0);
        break;
    }
  };

  const listboxId = React.useId();

  return (
    <div className={className}>
      <input
        type="text"
        value={query}
        placeholder={placeholder}
        onChange={e => {
          setQuery(e.target.value);
          setActiveIndex(0);
        }}
        onKeyDown={handleKeyDown}
        aria-controls={listboxId}
        aria-expanded="true"
        role="combobox"
        className="border rounded-md px-2 py-1 mb-2 w-full"
        {...rest}
      />
      <ul role="listbox" id={listboxId} className="border rounded-md max-h-60 overflow-auto">
        {filtered.map((opt, idx) => {
          const selected = multiple
            ? Array.isArray(value) && value.includes(opt.value)
            : value === opt.value;
          return (
            <li
              key={opt.value}
              role="option"
              aria-selected={selected}
              id={`${listboxId}-option-${idx}`}
              className={`${
                activeIndex === idx ? 'bg-blue-500 text-white' : ''
              } px-2 py-1 cursor-pointer`}
              onMouseDown={e => e.preventDefault()}
              onClick={() => selectOption(idx)}
            >
              {opt.label}
            </li>
          );
        })}
      </ul>

    </div>
  );
};

export default Select;

