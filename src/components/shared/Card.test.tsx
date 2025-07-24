import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardTitle, CardContent } from './Card';

test('renders card children', () => {
  render(
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
      </CardHeader>
      <CardContent>inside</CardContent>
    </Card>
  );
  expect(screen.getByText('Title')).toBeInTheDocument();
  expect(screen.getByText('inside')).toBeInTheDocument();
});
