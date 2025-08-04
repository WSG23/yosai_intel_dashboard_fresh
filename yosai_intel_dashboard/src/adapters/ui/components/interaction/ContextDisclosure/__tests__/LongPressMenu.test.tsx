import { render, fireEvent } from '@testing-library/react';
import LongPressMenu from '../LongPressMenu';

jest.useFakeTimers();

test('LongPressMenu reveals content after long press and hides on escape', () => {
  const { getByText } = render(
    <LongPressMenu preview={<div>preview</div>} delay={100}>
      <div>menu</div>
    </LongPressMenu>
  );

  const preview = getByText('preview');
  fireEvent.mouseDown(preview);
  jest.advanceTimersByTime(100);
  expect(getByText('menu')).toBeInTheDocument();
  fireEvent.keyDown(window, { key: 'Escape' });
  expect(getByText('preview')).toBeInTheDocument();
});
