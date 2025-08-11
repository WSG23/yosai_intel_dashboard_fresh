import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';

global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => [],
}) as unknown as typeof fetch;

import LearnMore from './LearnMore';

describe('LearnMore page', () => {
  it('renders heading', async () => {
    render(<LearnMore />);
    expect(
      screen.getByRole('heading', { name: /learn more/i })
    ).toBeInTheDocument();
  });
});
