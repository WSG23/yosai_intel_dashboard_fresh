import { render, screen, fireEvent } from '@testing-library/react';
import { FilePreview } from './FilePreview';

const file = { id: '1', file: new File(['d'], 'file.csv'), status: 'ready', progress: 10 };

test('renders file name', () => {
  render(<FilePreview file={file} onRemove={() => {}} />);
  expect(screen.getByText('file.csv')).toBeInTheDocument();
});

test('remove button is focusable and supports keyboard activation', () => {
  const onRemove = jest.fn();
  render(<FilePreview file={file} onRemove={onRemove} />);
  const button = screen.getByRole('button', { name: `Remove ${file.file.name}` });
  button.focus();
  expect(button).toHaveFocus();
  fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });
  fireEvent.keyUp(button, { key: 'Enter', code: 'Enter' });
  expect(onRemove).toHaveBeenCalled();
});

test('invokes onCancel when cancel button clicked', () => {
  const onCancel = jest.fn();
  const uploadingFile = { ...file, status: 'uploading' };
  render(
    <FilePreview file={uploadingFile} onRemove={() => {}} onCancel={onCancel} />,
  );
  const button = screen.getByRole('button', { name: `Cancel ${file.file.name}` });
  fireEvent.click(button);
  expect(onCancel).toHaveBeenCalled();
});
