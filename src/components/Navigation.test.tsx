import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Navigation, { Header, Sidebar } from './Navigation';

test('renders navigation links', () => {
  render(
    <MemoryRouter>
      <Navigation />
    </MemoryRouter>
  );
  expect(screen.getByText('Upload')).toBeInTheDocument();
  expect(screen.getByText('Analytics')).toBeInTheDocument();
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
