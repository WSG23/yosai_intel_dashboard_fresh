import { render } from '@testing-library/react';
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
