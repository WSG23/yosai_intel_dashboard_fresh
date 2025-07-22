import { render, screen } from '@testing-library/react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './tabs';

test('renders tabs structure', () => {
  render(
    <Tabs value="1" onValueChange={() => {}}>
      <TabsList>
        <TabsTrigger value="1">One</TabsTrigger>
      </TabsList>
      <TabsContent value="1">Content</TabsContent>
    </Tabs>
  );
  expect(screen.getByText('One')).toBeInTheDocument();
  expect(screen.getByText('Content')).toBeInTheDocument();
});
