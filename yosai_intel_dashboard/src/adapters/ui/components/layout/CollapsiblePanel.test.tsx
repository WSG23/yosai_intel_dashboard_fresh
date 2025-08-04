import React from 'react';
import { render, screen, act } from '@testing-library/react';
import CollapsiblePanel from './CollapsiblePanel';

describe('CollapsiblePanel', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  test('auto collapses after delay', () => {
    render(
      <CollapsiblePanel id="p" title="Panel" collapseAfter={1000}>
        content
      </CollapsiblePanel>
    );
    expect(screen.getByText('content')).toBeInTheDocument();
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    expect(screen.queryByText('content')).not.toBeInTheDocument();
  });

  test('persists collapsed state', () => {
    localStorage.setItem('panel-collapsed-p', 'true');
    render(
      <CollapsiblePanel id="p" title="Panel">
        content
      </CollapsiblePanel>
    );
    expect(screen.queryByText('content')).not.toBeInTheDocument();
  });
});
