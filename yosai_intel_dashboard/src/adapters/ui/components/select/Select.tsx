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
  const [isOpen, setIsOpen] = React.useState(false);
  const [search, setSearch] = React.useState('');
  const [activeIndex, setActiveIndex] = React.useState<number | null>(null);
  const listboxId = React.useId();

  const filteredOptions = React.useMemo(
    () =>
      options.filter(opt =>
        opt.label.toLowerCase().includes(search.toLowerCase())
      ),
    [options, search]
  );

  const selectOption = (val: string) => {
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setIsOpen(true);
      setActiveIndex(prev => {
        const next = prev === null ? 0 : Math.min(prev + 1, filteredOptions.length - 1);
        return next;
      });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setIsOpen(true);
      setActiveIndex(prev => {
        const next = prev === null ? filteredOptions.length - 1 : Math.max(prev - 1, 0);
        return next;
      });
    } else if (e.key === 'Enter') {
      if (activeIndex !== null && filteredOptions[activeIndex]) {
        selectOption(filteredOptions[activeIndex].value);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const activeId =
    activeIndex !== null ? `${listboxId}-option-${activeIndex}` : undefined;

  return (
    <div className={`relative ${className}`} {...rest}>
      <input
        type="text"
        role="combobox"
        aria-expanded={isOpen}
        aria-controls={listboxId}
        aria-activedescendant={activeId}
        placeholder={placeholder}
        value={search}
        onChange={e => {
          setSearch(e.target.value);
          setIsOpen(true);
        }}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsOpen(true)}
        className="border rounded-md px-2 py-1 w-full"
      />
      {isOpen && (
        <ul
          role="listbox"
          id={listboxId}
          aria-multiselectable={multiple || undefined}
          className="border rounded-md mt-1 max-h-60 overflow-auto bg-white z-10"
        >
          {filteredOptions.map((opt, index) => {
            const selected = multiple
              ? Array.isArray(value) && value.includes(opt.value)
              : value === opt.value;
            return (
              <li
                key={opt.value}
                role="option"
                id={`${listboxId}-option-${index}`}
                aria-selected={selected}
                className={`px-2 py-1 cursor-pointer hover:bg-gray-100 ${
                  activeIndex === index ? 'bg-gray-100' : ''
                }`}
                onMouseDown={e => {
                  e.preventDefault();
                  selectOption(opt.value);
                }}
                onMouseEnter={() => setActiveIndex(index)}
              >
                {opt.label}
              </li>
            );
          })}
        </ul>
      )}
      <div role="status" aria-live="polite" className="sr-only">
        {`${filteredOptions.length} results available`}
      </div>

    </div>
  );
};

export default Select;

