import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

jest.mock('react-router-dom', () => ({
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  useLocation: () => ({ pathname: '/' }),
  useNavigate: () => jest.fn(),
}), { virtual: true });

describe('App responsive behavior', () => {
  it('opens mobile menu', () => {
    render(<App />);
    const toggle = screen.getByLabelText(/toggle menu/i);
    fireEvent.click(toggle);
    expect(screen.getByText('Upload')).toBeInTheDocument();
  });

  it('toggles dark mode', () => {
    render(<App />);
    const darkToggle = screen.getByLabelText(/toggle dark mode/i);
    fireEvent.click(darkToggle);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});
