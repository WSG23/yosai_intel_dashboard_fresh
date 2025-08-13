import { render, screen, fireEvent } from '@testing-library/react';
import Hint from './Hint';
import { logTipInteraction } from '../../services/analytics/usage';

vi.mock('../../services/analytics/usage', () => ({
  logTipInteraction: vi.fn(),
}));

test('logs view and click interactions', () => {
  render(<Hint id="1" message="Hello" />);
  const button = screen.getByRole('button', { name: /hint/i });
  const wrapper = button.parentElement as HTMLElement;

  fireEvent.mouseEnter(wrapper);
  expect(logTipInteraction).toHaveBeenCalledWith({ id: '1', action: 'view' });

  fireEvent.click(button);
  expect(logTipInteraction).toHaveBeenCalledWith({ id: '1', action: 'click' });
});
