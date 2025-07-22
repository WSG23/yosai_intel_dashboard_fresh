import { render, screen } from '@testing-library/react';
import { ColumnMappingModal } from './ColumnMappingModal';

const fileData = {
  filename: 'file.csv',
  columns: ['c1'],
  ai_suggestions: { c1: { field: 'person_id', confidence: 0.9 } },
  sample_data: { c1: ['v1'] }
};

test('shows modal title when open', () => {
  render(
    <ColumnMappingModal isOpen={true} onClose={() => {}} fileData={fileData as any} onConfirm={() => {}} />
  );
  expect(screen.getByText(/AI Column Mapping/)).toBeInTheDocument();
});
