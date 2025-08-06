import React from 'react';
import { render, screen } from '@testing-library/react';

jest.mock('three', () => ({
  Scene: class { add() {} },
  PerspectiveCamera: class { position = { z: 0 }; constructor() {} },
  WebGLRenderer: class {
    domElement: HTMLCanvasElement = {
      nodeType: 1,
      setAttribute: () => {},
    } as unknown as HTMLCanvasElement;
    setSize() {}
    render() {}
  },
  BoxGeometry: class {},
  MeshBasicMaterial: class {},
  Mesh: class {
    rotation = { x: 0, y: 0 };
    constructor() {}
  },
}));

import FacilityLayout from '../pages/visualizations/FacilityLayout';

test('renders facility layout canvas', () => {
  const { container } = render(<FacilityLayout />);
  expect(screen.getByRole('img', { name: /3d facility layout/i })).toBeInTheDocument();
  expect(container).toMatchSnapshot();
});
