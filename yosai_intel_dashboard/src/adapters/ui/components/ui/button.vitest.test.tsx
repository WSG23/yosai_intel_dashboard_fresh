import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { Button } from './button';

describe('Button', () => {
  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Press me</Button>);
    await userEvent.click(screen.getByRole('button', { name: /press me/i }));
    expect(handleClick).toHaveBeenCalled();
  });
});
