import { render, fireEvent } from '@testing-library/react';
import HoverPreview from '../HoverPreview';

test('HoverPreview toggles content on hover and shortcuts', () => {
  const { getByText } = render(
    <HoverPreview preview={<div>preview</div>}>
      <div>content</div>
    </HoverPreview>
  );

  const preview = getByText('preview');
  fireEvent.mouseEnter(preview);
  expect(getByText('content')).toBeInTheDocument();
  fireEvent.mouseLeave(preview);
  expect(getByText('preview')).toBeInTheDocument();

  fireEvent.keyDown(window, { key: 'e' });
  expect(getByText('content')).toBeInTheDocument();
  fireEvent.keyDown(window, { key: 'Escape' });
  expect(getByText('preview')).toBeInTheDocument();
});
