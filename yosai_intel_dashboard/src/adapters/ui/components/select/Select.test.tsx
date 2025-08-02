import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Select, Option } from './Select';

const options: Option<'a' | 'b'>[] = [
  { value: 'a', label: 'A' },
  { value: 'b', label: 'B' }
];

test('calls onChange with selected value', () => {
  const onChange = jest.fn();
  render(<Select value="" onChange={onChange} options={options} />);
  fireEvent.change(screen.getByRole('combobox'), { target: { value: 'a' } });
  expect(onChange).toHaveBeenCalledWith('a');
});

test('handles multiple selection', () => {
  const onChange = jest.fn();
  render(<Select value={[]} onChange={onChange} options={options} multiple />);
  const select = screen.getByRole('listbox');
  fireEvent.change(select, {
    target: { selectedOptions: [{ value: 'a' }, { value: 'b' }] }
  });
  expect(onChange).toHaveBeenCalledWith(['a', 'b']);
});

test('filters options based on search input', () => {
  const onChange = jest.fn();

  const SearchableSelect = () => {
    const [query, setQuery] = React.useState('');
    const filtered = options.filter(opt =>
      opt.label.toLowerCase().includes(query.toLowerCase())
    );
    return (
      <>
        <input
          aria-label="search"
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <Select value="" onChange={onChange} options={filtered} />
      </>
    );
  };

  render(<SearchableSelect />);
  fireEvent.change(screen.getByLabelText('search'), {
    target: { value: 'b' }
  });

  expect(screen.queryByText('A')).toBeNull();
  expect(screen.getByText('B')).toBeInTheDocument();

  fireEvent.change(screen.getByRole('combobox'), {
    target: { value: 'b' }
  });
  expect(onChange).toHaveBeenCalledWith('b');
});

test('supports keyboard navigation for single select', () => {
  const onChange = jest.fn();
  render(<Select value="a" onChange={onChange} options={options} />);
  const select = screen.getByRole('combobox');

  select.focus();
  fireEvent.keyDown(select, { key: 'ArrowDown' });
  fireEvent.change(select, { target: { value: 'b' } });
  expect(onChange).toHaveBeenCalledWith('b');

  fireEvent.keyDown(select, { key: 'Enter' });
  expect(onChange).toHaveBeenLastCalledWith('b');

  fireEvent.keyDown(select, { key: 'Escape' });
  fireEvent.blur(select);
  expect(select).not.toHaveFocus();
});

test('multi-select keyboard toggling and focus management', () => {
  const onChange = jest.fn();
  render(<Select value={[]} onChange={onChange} options={options} multiple />);
  const listbox = screen.getByRole('listbox');

  listbox.focus();
  fireEvent.keyDown(listbox, { key: 'ArrowDown' });
  fireEvent.change(listbox, {
    target: { selectedOptions: [{ value: 'a' }] }
  });
  expect(onChange).toHaveBeenCalledWith(['a']);

  fireEvent.keyDown(listbox, { key: 'ArrowDown' });
  fireEvent.change(listbox, {
    target: { selectedOptions: [{ value: 'a' }, { value: 'b' }] }
  });
  expect(onChange).toHaveBeenLastCalledWith(['a', 'b']);

  fireEvent.keyDown(listbox, { key: 'Enter' });
  fireEvent.change(listbox, {
    target: { selectedOptions: [{ value: 'b' }] }
  });
  expect(onChange).toHaveBeenLastCalledWith(['b']);

  fireEvent.keyDown(listbox, { key: 'Escape' });
  fireEvent.blur(listbox);
  expect(listbox).not.toHaveFocus();

});
