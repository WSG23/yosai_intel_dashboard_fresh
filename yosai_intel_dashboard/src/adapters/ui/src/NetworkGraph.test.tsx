import React from 'react';
import { render, screen } from '@testing-library/react';

jest.mock('d3', () => {
  const selection: any = {
    selectAll: () => selection,
    remove: () => selection,
    data: () => selection,
    enter: () => selection,
    append: () => selection,
    attr: () => selection,
    call: (fn: any) => {
      fn(selection);
      return selection;
    },
    on: () => selection,
  };
  const simulation: any = { force: () => simulation, on: () => {}, stop: () => {} };
  const dragBehavior: any = () => selection;
  dragBehavior.on = () => dragBehavior;
  return {
    select: () => selection,
    forceSimulation: () => simulation,
    forceLink: () => ({ id: () => ({ distance: () => ({}) }) }),
    forceManyBody: () => ({ strength: () => ({}) }),
    forceCenter: () => ({}),
    drag: () => dragBehavior,
  };
});

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
