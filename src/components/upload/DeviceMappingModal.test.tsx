import { render, screen } from '@testing-library/react';
import { DeviceMappingModal } from './DeviceMappingModal';

test('renders device modal title', () => {
  render(
    <DeviceMappingModal isOpen={true} onClose={() => {}} devices={['d1']} filename="file.csv" onConfirm={() => {}} />
  );
  expect(screen.getByText(/AI Device Classification/)).toBeInTheDocument();
});
