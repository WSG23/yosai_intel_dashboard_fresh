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
  const input = screen.getByRole('combobox');
  fireEvent.focus(input);
  const option = screen.getByRole('option', { name: 'A' });
  fireEvent.mouseDown(option);
  expect(onChange).toHaveBeenCalledWith('a');
});

test('handles multiple selection', () => {
  const onChange = jest.fn();
  render(<Select value={[]} onChange={onChange} options={options} multiple />);
  const input = screen.getByRole('combobox');
  fireEvent.focus(input);
  fireEvent.mouseDown(screen.getByRole('option', { name: 'A' }));
  fireEvent.mouseDown(screen.getByRole('option', { name: 'B' }));
  expect(onChange).toHaveBeenLastCalledWith(['a', 'b']);
});

test('manages aria attributes', () => {
  render(<Select value="" onChange={() => {}} options={options} />);
  const input = screen.getByRole('combobox');
  expect(input).toHaveAttribute('aria-expanded', 'false');
  fireEvent.focus(input);
  const listbox = screen.getByRole('listbox');
  expect(input).toHaveAttribute('aria-controls', listbox.id);
  fireEvent.keyDown(input, { key: 'ArrowDown' });
  const firstOption = screen.getByRole('option', { name: 'A' });
  expect(input).toHaveAttribute('aria-activedescendant', firstOption.id);
});

test('sets aria-multiselectable when multiple', () => {
  render(<Select value={[]} onChange={() => {}} options={options} multiple />);
  const input = screen.getByRole('combobox');
  fireEvent.focus(input);
  const listbox = screen.getByRole('listbox');
  expect(listbox).toHaveAttribute('aria-multiselectable', 'true');
});

test('announces number of results', () => {
  render(<Select value="" onChange={() => {}} options={options} />);
  const status = screen.getByRole('status');
  expect(status).toHaveTextContent('2 results available');
  const input = screen.getByRole('combobox');
  fireEvent.change(input, { target: { value: 'A' } });
  expect(status).toHaveTextContent('1 results available');
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
