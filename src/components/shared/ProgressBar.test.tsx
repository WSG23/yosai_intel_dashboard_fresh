import { render } from '@testing-library/react';
import { ProgressBar } from './ProgressBar';

test('sets progress width', () => {
  const { getByRole } = render(<ProgressBar progress={50} />);
  const progress = getByRole('progressbar');
  expect(progress).toHaveAttribute('aria-valuenow', '50');
});
