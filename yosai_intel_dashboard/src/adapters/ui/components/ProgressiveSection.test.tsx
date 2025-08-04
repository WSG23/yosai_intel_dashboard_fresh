import { render, screen, fireEvent } from '@testing-library/react';
import ProgressiveSection from './ProgressiveSection';

describe('ProgressiveSection', () => {
  test('hides content from screen readers until expanded', () => {
    render(
      <ProgressiveSection title="Details">
        <div>Hidden content</div>
      </ProgressiveSection>,
    );
    const button = screen.getByRole('button', { name: 'Details' });
    const content = screen.getByText('Hidden content');
    // content should be hidden and aria-hidden
    expect(content).toHaveAttribute('hidden');
    expect(content).toHaveAttribute('aria-hidden', 'true');
    expect(button).toHaveAttribute('aria-expanded', 'false');
  });

  test('reveals content when expanded', () => {
    render(
      <ProgressiveSection title="More">
        <p>Secret</p>
      </ProgressiveSection>,
    );
    const button = screen.getByRole('button', { name: 'More' });
    fireEvent.click(button);
    const content = screen.getByText('Secret');
    expect(content).not.toHaveAttribute('hidden');
    expect(content).toHaveAttribute('aria-hidden', 'false');
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });
});
