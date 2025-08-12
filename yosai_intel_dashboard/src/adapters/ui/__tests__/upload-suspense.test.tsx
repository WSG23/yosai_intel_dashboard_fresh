import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

jest.mock('react-router-dom', () => ({
  Link: ({ children, ...props }: any) => <a {...props}>{children}</a>,
  useLocation: () => ({ pathname: '/' }),
  useNavigate: () => jest.fn(),
}), { virtual: true });

jest.mock('../components/upload', () => ({
  Upload: () => {
    throw new Promise(() => {});
  },
}));

test('shows spinner while Upload is loading', () => {
  render(<App />);
  expect(screen.getByRole('status')).toBeInTheDocument();
});
