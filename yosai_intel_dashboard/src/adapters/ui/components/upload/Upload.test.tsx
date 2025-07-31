import { render, screen, fireEvent } from '@testing-library/react';
import Upload from './Upload';
import { ZustandProvider } from '../../state';

describe('Upload component', () => {
  it('does not show upload button with no files', () => {
    render(
      <ZustandProvider>
        <Upload />
      </ZustandProvider>
    );
    expect(screen.queryByRole('button', { name: /upload all/i })).toBeNull();
  });

  it('adds file and enables upload', async () => {
    const { container } = render(
      <ZustandProvider>
        <Upload />
      </ZustandProvider>
    );
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['data'], 'test.csv', { type: 'text/csv' });
    fireEvent.change(input, { target: { files: [file] } });
    expect(await screen.findByText('test.csv')).toBeInTheDocument();
    const button = screen.getByRole('button', { name: /upload all/i });
    expect(button).not.toBeDisabled();
  });

  it('removes file from list', async () => {
    const { container } = render(
      <ZustandProvider>
        <Upload />
      </ZustandProvider>
    );
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['data'], 'test.csv', { type: 'text/csv' });
    fireEvent.change(input, { target: { files: [file] } });
    await screen.findByText('test.csv');
    fireEvent.click(screen.getByText(/remove/i));
    expect(screen.queryByText('test.csv')).not.toBeInTheDocument();
  });
});
