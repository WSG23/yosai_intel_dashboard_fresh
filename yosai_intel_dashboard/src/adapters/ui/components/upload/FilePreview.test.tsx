import { render, screen, fireEvent } from '@testing-library/react';
import { FilePreview } from './FilePreview';

const file = {
  id: '1',
  file: new File(['d'], 'file.csv'),
  status: 'ready',
  progress: 10,
};

test('renders file name', () => {
  render(<FilePreview file={file} onRemove={() => {}} />);
  expect(screen.getByText('file.csv')).toBeInTheDocument();
});

test('remove button is focusable and supports keyboard activation', () => {
  const onRemove = jest.fn();
  render(<FilePreview file={file} onRemove={onRemove} />);
  const button = screen.getByRole('button', {
    name: `Remove ${file.file.name}`,
  });
  button.focus();
  expect(button).toHaveFocus();
  fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });
  fireEvent.keyUp(button, { key: 'Enter', code: 'Enter' });
  fireEvent.keyDown(button, { key: ' ', code: 'Space' });
  fireEvent.keyUp(button, { key: ' ', code: 'Space' });
  expect(onRemove).toHaveBeenCalledTimes(2);
});
