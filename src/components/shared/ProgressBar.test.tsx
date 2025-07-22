import { render } from '@testing-library/react';
import { ProgressBar } from './ProgressBar';

test('sets progress width', () => {
  const { container } = render(<ProgressBar progress={50} />);
  const bar = container.querySelector('div > div');
  expect(bar).toHaveStyle('width: 50%');
});
