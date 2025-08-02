import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import ErrorBoundary from '../yosai_intel_dashboard/src/adapters/ui/components/ErrorBoundary';

interface PlaygroundArgs {
  shouldThrow: boolean;
}

const meta: Meta<PlaygroundArgs> = {
  title: 'Components/ErrorBoundary',
  component: ErrorBoundary,
  argTypes: {
    shouldThrow: {
      control: 'boolean',
      description: 'Trigger the child component to throw an error.'
    }
  },
  parameters: {
    docs: {
      description: {
        component: 'Catches runtime errors and displays a fallback message. Ensure the fallback content is descriptive for screen readers.'
      }
    },
    controls: { expanded: true }
  }
};

export default meta;
type Story = StoryObj<PlaygroundArgs>;

const Buggy: React.FC<PlaygroundArgs> = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error('Boom');
  }
  return <div>No error</div>;
};

export const Playground: Story = {
  args: { shouldThrow: false },
  render: ({ shouldThrow }) => {
    const [key, setKey] = React.useState(0);
    return (
      <ErrorBoundary key={key}>
        <Buggy shouldThrow={shouldThrow} />
        <button onClick={() => setKey(k => k + 1)}>Retry</button>
      </ErrorBoundary>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Use the **shouldThrow** control to trigger an error. The **Retry** button remounts the boundary and is keyboard focusable.'
      }
    }
  }
};
