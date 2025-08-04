import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import ResponsiveTable, { ColumnConfig } from './ResponsiveTable';

interface RowData {
  name: string;
  detail: string;
}

const columns: ColumnConfig<RowData>[] = [
  { key: 'name', header: 'Name', priority: 1 },
  { key: 'detail', header: 'Detail', priority: 2 },
];

const data: RowData[] = [
  { name: 'Alice', detail: 'Extra info' },
];

describe('ResponsiveTable', () => {
  test('expands to show low priority columns in card view', () => {
    render(<ResponsiveTable<RowData> data={data} columns={columns} />);
    const card = screen.getByTestId('card-view');
    expect(within(card).getByText(/Name/)).toBeInTheDocument();
    expect(within(card).queryByText(/Detail/)).not.toBeInTheDocument();
    fireEvent.click(within(card).getByRole('button', { name: /show details/i }));
    expect(within(card).getByText(/Detail/)).toBeInTheDocument();
  });

  test('applies priority classes and sticky header in table view', () => {
    const { getByTestId } = render(
      <ResponsiveTable<RowData> data={data} columns={columns} />
    );
    const table = getByTestId('table-view');
    const thead = table.querySelector('thead');
    expect(thead?.className).toMatch(/sticky/);
    const ths = table.querySelectorAll('th');
    expect(ths[1].className).toMatch(/hidden lg:table-cell/);
  });
});
