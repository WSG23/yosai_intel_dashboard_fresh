import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardTitle, CardContent } from './card';

test('renders card with content', () => {
  render(
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
      </CardHeader>
      <CardContent>body</CardContent>
    </Card>
  );
  expect(screen.getByText('Title')).toBeInTheDocument();
  expect(screen.getByText('body')).toBeInTheDocument();
});
