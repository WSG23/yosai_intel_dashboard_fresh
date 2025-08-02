import React from 'react';

export const Select: React.FC<{ value: string; onValueChange: (value: string) => void; children: React.ReactNode }> = ({ children }) => <div className="relative">{children}</div>;

export const SelectTrigger: React.FC<{ className?: string; children: React.ReactNode }> = ({ className = '', children }) => <div className={`border rounded px-3 py-2 ${className}`}>{children}</div>;

export const SelectValue: React.FC<{ placeholder?: string }> = ({ placeholder }) => <span className="text-gray-500">{placeholder}</span>;

export const SelectContent: React.FC<{
  children: React.ReactNode;
  searchable?: boolean;
  onSearch?: (query: string) => void;
}> = ({ children, searchable = false, onSearch }) => {
  const [query, setQuery] = React.useState('');
  const items = React.Children.toArray(children);
  const filteredItems = !onSearch && searchable && query
    ? items.filter((child) => {
        if (React.isValidElement(child)) {
          const text = String(child.props.children).toLowerCase();
          return text.includes(query.toLowerCase());
        }
        return true;
      })
    : items;

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    if (onSearch) {
      onSearch(value);
    }
  };

  return (
    <div className="absolute z-10 bg-white border rounded shadow-lg">
      {searchable && (
        <input
          type="text"
          value={query}
          onChange={handleSearch}
          placeholder="Search..."
          className="w-full p-2 border-b outline-none"
        />
      )}
      {filteredItems}
    </div>
  );
};

export const SelectItem: React.FC<{ value: string; children: React.ReactNode }> = ({ children }) => <div className="px-3 py-2 hover:bg-gray-100 cursor-pointer">{children}</div>;
