import React from 'react';
import { render, screen } from '@testing-library/react';
jest.mock('react-router-dom', () => ({
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  useLocation: () => ({ pathname: '/' }),
  useNavigate: () => jest.fn(),
  MemoryRouter: ({ children }: any) => <div>{children}</div>,
}), { virtual: true });
import Navigation, { Header, Sidebar } from './Navigation';

const MemoryRouter: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div>{children}</div>
);

test('renders navigation links', () => {
  render(
    <MemoryRouter>
      <Navigation />
    </MemoryRouter>
  );
  expect(screen.getByText('Upload')).toBeInTheDocument();
  expect(screen.getByText('Analytics')).toBeInTheDocument();
  expect(screen.getByText('Builder')).toBeInTheDocument();
});

test('header shows title', () => {
  render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>
  );
  expect(screen.getByText('Yosai Intel Dashboard')).toBeInTheDocument();
});

test('sidebar renders when open', () => {
  render(
    <MemoryRouter>
      <Sidebar isOpen={true} />
    </MemoryRouter>
  );
  expect(screen.getByText('Analytics Ready')).toBeInTheDocument();
});
