import { render, screen, fireEvent } from '@testing-library/react';
import UsageDashboard from '../pages/UsageDashboard';

jest.mock('../services/analytics/usage', () => ({
  snapshot: () => ({
    adoption: { featureA: 10 },
    errors: { featureB: 2 },
    proficiency: { user1: 3 },
  }),
  onUsageUpdate: () => () => {},
}));

describe('UsageDashboard progressive disclosure', () => {
  test('reveals adoption details and drill-down info on demand', () => {
    render(<UsageDashboard />);

    const toggle = screen.getByRole('button', {
      name: /show adoption details/i,
    });
    const content = document.getElementById('adoption-details');
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(content).toHaveAttribute('hidden');

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(content).not.toHaveAttribute('hidden');

    const featureSummary = screen.getByText('featureA: 10');
    const details = featureSummary.closest('details');
    expect(details).not.toHaveAttribute('open');
    fireEvent.click(featureSummary);
    expect(details).toHaveAttribute('open');
  });
});
