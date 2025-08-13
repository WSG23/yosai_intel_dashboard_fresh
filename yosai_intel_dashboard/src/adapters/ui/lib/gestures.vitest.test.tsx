import { render, fireEvent } from '@testing-library/react';
import React from 'react';
import { vi } from 'vitest';
import { useSwipe, type SwipeDir } from './gestures';

const SwipeComponent: React.FC<{ onSwipe: (dir: SwipeDir) => void }> = ({
  onSwipe,
}) => {
  const ref = useSwipe(onSwipe);
  return <div data-testid="swipe" ref={ref} />;
};

it('detects left swipe', () => {
  const handler = vi.fn();
  const { getByTestId } = render(<SwipeComponent onSwipe={handler} />);
  const el = getByTestId('swipe');
  fireEvent.touchStart(el, { touches: [{ clientX: 100, clientY: 0 }] });
  fireEvent.touchEnd(el, { changedTouches: [{ clientX: 50, clientY: 0 }] });
  expect(handler).toHaveBeenCalledWith('left');
});
