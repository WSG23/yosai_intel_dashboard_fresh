import { render, screen } from '@testing-library/react';
import { FilePreview } from './FilePreview';

const file = { id: '1', file: new File(['d'], 'file.csv'), status: 'ready', progress: 10 };

test('renders file name', () => {
  render(<FilePreview file={file} onRemove={() => {}} />);
  expect(screen.getByText('file.csv')).toBeInTheDocument();
});
