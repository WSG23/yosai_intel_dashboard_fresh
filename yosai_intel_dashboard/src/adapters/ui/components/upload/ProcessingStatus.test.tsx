import { render, screen } from '@testing-library/react';
import ProcessingStatus from './ProcessingStatus';

test('renders progress message and percentage', () => {
  render(<ProcessingStatus message="Uploading" progress={42} />);
  expect(screen.getByText('Uploading')).toBeInTheDocument();
  expect(screen.getByText('42%')).toBeInTheDocument();
});
