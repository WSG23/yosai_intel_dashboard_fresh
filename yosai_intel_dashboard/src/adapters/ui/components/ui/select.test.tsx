import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from './select';

test('supports multi-selection with keyboard', () => {
  const onValueChange = jest.fn();
  const Wrapper = () => {
    const [values, setValues] = React.useState<string[]>([]);
    const handleChange = (vals: string[]) => {
      onValueChange(vals);
      setValues(vals);
    };
    return (
      <Select value={values} onValueChange={handleChange} multiple>
        <SelectTrigger>
          <SelectValue placeholder="choose" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="1">One</SelectItem>
          <SelectItem value="2">Two</SelectItem>
        </SelectContent>
      </Select>
    );
  };
  render(<Wrapper />);

  const item1 = screen.getByText('One');
  fireEvent.click(item1);
  expect(onValueChange).toHaveBeenLastCalledWith(['1']);
  expect((item1.querySelector('input') as HTMLInputElement).checked).toBe(true);

  const item2 = screen.getByText('Two');
  fireEvent.keyDown(item2, { key: ' ', code: 'Space' });
  expect(onValueChange).toHaveBeenLastCalledWith(['1', '2']);
  expect((item2.querySelector('input') as HTMLInputElement).checked).toBe(true);
});
