import { render, screen, fireEvent } from '@testing-library/react';
import Tooltip from './Tooltip';

test('shows and hides tooltip on hover', () => {
  render(
    <Tooltip text="Info">
      <span>Hover me</span>
    </Tooltip>,
  );

  expect(screen.queryByText('Info')).not.toBeInTheDocument();

  const trigger = screen.getByText('Hover me');
  fireEvent.mouseEnter(trigger);
  expect(screen.getByText('Info')).toBeInTheDocument();

  fireEvent.mouseLeave(trigger);
  expect(screen.queryByText('Info')).not.toBeInTheDocument();
});
