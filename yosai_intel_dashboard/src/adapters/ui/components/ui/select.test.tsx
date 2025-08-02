import { render, screen, fireEvent } from '@testing-library/react';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from './select';

test('renders select components', () => {
  render(
    <Select value="" onValueChange={() => {}}>
      <SelectTrigger>
        <SelectValue placeholder="choose" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="1">One</SelectItem>
      </SelectContent>
    </Select>
  );
});

test('filters options when searchable is enabled', () => {
  render(
    <Select value="" onValueChange={() => {}}>
      <SelectTrigger>
        <SelectValue placeholder="choose" />
      </SelectTrigger>
      <SelectContent searchable>
        <SelectItem value="1">Apple</SelectItem>
        <SelectItem value="2">Banana</SelectItem>
      </SelectContent>
    </Select>
  );

  const input = screen.getByPlaceholderText('Search...');
  fireEvent.change(input, { target: { value: 'ban' } });

  expect(screen.queryByText('Apple')).toBeNull();
  expect(screen.getByText('Banana')).toBeInTheDocument();
});

test('calls onSearch when provided', () => {
  const onSearch = jest.fn();
  render(
    <Select value="" onValueChange={() => {}}>
      <SelectTrigger>
        <SelectValue placeholder="choose" />
      </SelectTrigger>
      <SelectContent searchable onSearch={onSearch}>
        <SelectItem value="1">Apple</SelectItem>
        <SelectItem value="2">Banana</SelectItem>
      </SelectContent>
    </Select>
  );

  const input = screen.getByPlaceholderText('Search...');
  fireEvent.change(input, { target: { value: 'app' } });
  expect(onSearch).toHaveBeenCalledWith('app');
});
