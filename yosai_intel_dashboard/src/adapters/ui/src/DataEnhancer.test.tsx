import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DataEnhancer from '../pages/data_enhancer/DataEnhancer';

test('uploads file and suggests columns', async () => {
  render(<DataEnhancer />);
  const file = new File(['a,b\n1,2'], 'test.csv', { type: 'text/csv' });
  const input = screen.getByLabelText(/upload/i);
  fireEvent.change(input, { target: { files: [file] } });
  await waitFor(() => screen.getByText('File uploaded'));
  fireEvent.click(screen.getByText('Suggest Columns'));
  await waitFor(() => screen.getByText(/Found 2 suggestions/));
});
