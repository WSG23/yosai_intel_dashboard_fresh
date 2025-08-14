import React from 'react';
import { render, screen } from '@testing-library/react';
import NetworkGraph from '../pages/visualizations/NetworkGraph';

test('renders accessible network graph', () => {
  const { container } = render(<NetworkGraph />);
  expect(
    screen.getByRole('img', {
      name: /relationship graph showing security entity connections/i,
    })
  ).toBeInTheDocument();
  expect(container).toMatchSnapshot();
});
