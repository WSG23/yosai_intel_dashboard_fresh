import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import SmartMenu, { SmartMenuItem } from './SmartMenu';

describe('SmartMenu', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('orders by frequency and shows recently used', () => {
    const items: SmartMenuItem[] = [
      { id: 'a', label: 'A', onSelect: jest.fn() },
      { id: 'b', label: 'B', onSelect: jest.fn() },
    ];
    render(<SmartMenu items={items} />);
    fireEvent.click(screen.getByText('B'));
    fireEvent.click(screen.getByText('B'));
    fireEvent.click(screen.getByText('A'));
    expect(screen.getByText('Recently Used')).toBeInTheDocument();
    const lists = screen.getAllByRole('list');
    const mainButtons = within(lists[lists.length - 1]).getAllByRole('button');
    expect(mainButtons[0]).toHaveTextContent('B');
  });
});
