import { render } from '@testing-library/react';
import { ProgressBar } from './ProgressBar';

test('sets progress width with accessible label', () => {
  const { getByRole } = render(<ProgressBar progress={50} />);
  const progress = getByRole('progressbar', { name: /progress/i });
  expect(progress).toHaveAttribute('aria-valuenow', '50');
});
