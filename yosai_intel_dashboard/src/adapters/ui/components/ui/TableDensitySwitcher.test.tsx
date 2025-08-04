import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TableDensitySwitcher from './TableDensitySwitcher';
import { boundStore } from '../../state/store';

describe('TableDensitySwitcher', () => {
  beforeEach(() => {
    boundStore.setState({ tableDensity: 'comfortable' });
  });

  test('changes density on click', () => {
    render(<TableDensitySwitcher />);
    fireEvent.click(screen.getByText('Compact'));
    expect(boundStore.getState().tableDensity).toBe('compact');
  });
});
