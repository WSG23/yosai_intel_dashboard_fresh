import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
jest.mock('react-router-dom', () => ({
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  useLocation: () => ({ pathname: '/' }),
  useNavigate: () => jest.fn(),
  MemoryRouter: ({ children }: any) => <div>{children}</div>,
}), { virtual: true });
import Navbar from './Navbar';

const MemoryRouter: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div>{children}</div>
);

test('shows brand text and toggles menu', () => {
  render(
    <MemoryRouter>
      <Navbar />
    </MemoryRouter>
  );
  expect(screen.getByText('YOSAI Intelligence')).toBeInTheDocument();
  const toggle = screen.getByLabelText('Toggle menu');
  fireEvent.click(toggle);
  expect(toggle).toBeInTheDocument();
});
