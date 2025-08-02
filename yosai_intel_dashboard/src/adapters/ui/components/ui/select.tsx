import React, { createContext, useContext } from 'react';

interface SelectContextProps {
  value: string[];
  multiple: boolean;
  onValueChange: (values: string[]) => void;
}

const SelectContext = createContext<SelectContextProps | null>(null);

interface SelectProps {
  value: string[];
  onValueChange: (values: string[]) => void;
  multiple?: boolean;
  children: React.ReactNode;
}

export const Select: React.FC<SelectProps> = ({ value, onValueChange, multiple = false, children }) => (
  <SelectContext.Provider value={{ value, onValueChange, multiple }}>
    <div className="relative">{children}</div>
  </SelectContext.Provider>
);

export const SelectTrigger: React.FC<{ className?: string; children: React.ReactNode }> = ({ className = '', children }) => (
  <div className={`border rounded px-3 py-2 ${className}`}>{children}</div>
);

export const SelectValue: React.FC<{ placeholder?: string }> = ({ placeholder }) => (
  <span className="text-gray-500">{placeholder}</span>
);

export const SelectContent: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="absolute z-10 bg-white border rounded shadow-lg">{children}</div>
);

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
}

export const SelectItem: React.FC<SelectItemProps> = ({ value, children }) => {
  const ctx = useContext(SelectContext);
  if (!ctx) return null;
  const { value: selected, onValueChange, multiple } = ctx;
  const checked = selected.includes(value);
  const toggle = () => {
    if (checked) {
      onValueChange(selected.filter((v) => v !== value));
    } else {
      onValueChange(multiple ? [...selected, value] : [value]);
    }
  };
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === ' ' || e.key === 'Spacebar') {
      e.preventDefault();
      toggle();
    }
  };
  return (
    <div
      tabIndex={0}
      role={multiple ? 'checkbox' : 'option'}
      aria-checked={multiple ? checked : undefined}
      aria-selected={!multiple ? checked : undefined}
      onClick={toggle}
      onKeyDown={handleKeyDown}
      className="px-3 py-2 hover:bg-gray-100 cursor-pointer flex items-center"
    >
      {multiple && <input type="checkbox" checked={checked} readOnly className="mr-2" />}
      {children}
    </div>
  );
};
