import { render, screen } from '@testing-library/react';
import ProgressIndicator from './ProgressIndicator';

test('shows progress and message', () => {
  render(<ProgressIndicator message="loading" progress={50} />);
  expect(screen.getByText('loading')).toBeInTheDocument();
  expect(screen.getByRole('progressbar')).toHaveStyle('width: 50%');
});
