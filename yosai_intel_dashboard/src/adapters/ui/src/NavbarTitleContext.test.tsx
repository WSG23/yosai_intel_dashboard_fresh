import React from 'react';
import { render, screen } from '@testing-library/react';
import Navbar from '../components/layout/Navbar';
import { NavbarTitleProvider, NavbarTitleUpdater } from '../components/layout/NavbarTitleContext';

jest.mock('react-router-dom', () => ({
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  useLocation: () => ({ pathname: '/' }),
  useNavigate: () => jest.fn(),
  MemoryRouter: ({ children }: any) => <div>{children}</div>,
}), { virtual: true });

beforeAll(() => {
  (window as any).matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  });
});

const MemoryRouter: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div>{children}</div>
);

test('navbar title updates via context', () => {
  render(
    <MemoryRouter>
      <NavbarTitleProvider>
        <Navbar />
        <NavbarTitleUpdater title="Test Title" />
      </NavbarTitleProvider>
    </MemoryRouter>
  );
  expect(screen.getByText('Test Title')).toBeInTheDocument();
});
