import { render, screen } from '@testing-library/react';
import { Select } from '../select/Select';

const options = [{ value: '1', label: 'One' }];

test('renders unified select', () => {
  render(<Select value="" onChange={() => {}} options={options} />);
  expect(screen.getByRole('combobox')).toBeInTheDocument();
});
