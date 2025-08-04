import { render, fireEvent } from '@testing-library/react';
import ClickExpand from '../ClickExpand';

test('ClickExpand toggles on click and shortcuts', () => {
  const { getByText } = render(
    <ClickExpand preview={<div>preview</div>}>
      <div>content</div>
    </ClickExpand>
  );

  const container = getByText('preview');
  fireEvent.click(container);
  expect(getByText('content')).toBeInTheDocument();
  fireEvent.click(getByText('content'));
  expect(getByText('preview')).toBeInTheDocument();

  fireEvent.keyDown(window, { key: 'e' });
  expect(getByText('content')).toBeInTheDocument();
  fireEvent.keyDown(window, { key: 'Escape' });
  expect(getByText('preview')).toBeInTheDocument();
});
