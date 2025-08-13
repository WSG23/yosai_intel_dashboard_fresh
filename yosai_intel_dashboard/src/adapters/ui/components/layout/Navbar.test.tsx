import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  MockLink,
  MockMemoryRouter as MemoryRouter,
} from '../../test-utils/router';

jest.mock(
  'react-router-dom',
  () => ({
    Link: MockLink,
    useLocation: () => ({ pathname: '/' }),
    useNavigate: () => jest.fn(),
    MemoryRouter,
  }),
  { virtual: true },
);
import Navbar from './Navbar';
import { NavbarTitleProvider } from './NavbarTitleContext';

test('shows brand text and toggles menu', () => {
  (window as any).innerWidth = 500;
  render(
    <MemoryRouter>
      <NavbarTitleProvider>
        <Navbar />
      </NavbarTitleProvider>
    </MemoryRouter>,
  );
  expect(screen.getByText('YOSAI Intelligence')).toBeInTheDocument();
  const toggle = screen.getByLabelText('Toggle menu');
  fireEvent.click(toggle);
  expect(toggle).toBeInTheDocument();
});
