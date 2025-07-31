import { render, screen } from '@testing-library/react';
import SimpleModal from './SimpleModal';

test('renders modal content when open', () => {
  render(
    <SimpleModal isOpen={true} onClose={() => {}} title="Title">
      body
    </SimpleModal>
  );
  expect(screen.getByText('Title')).toBeInTheDocument();
  expect(screen.getByText('body')).toBeInTheDocument();
});
