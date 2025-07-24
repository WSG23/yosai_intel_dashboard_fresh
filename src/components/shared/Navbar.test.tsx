import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Navbar from './Navbar';

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
