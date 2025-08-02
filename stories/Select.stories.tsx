import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { Select } from '../yosai_intel_dashboard/src/adapters/ui/components/select/Select';

const fruitOptions = [
  { value: 'apple', label: 'Apple' },
  { value: 'banana', label: 'Banana' },
  { value: 'cherry', label: 'Cherry' }
];

const meta: Meta<typeof Select> = {
  title: 'Components/Select',
  component: Select,
  args: {
    options: fruitOptions,
    value: '',
    'aria-label': 'Fruit picker'
  },
  argTypes: {
    multiple: { control: 'boolean' }
  },
  parameters: {
    docs: {
      description: {
        component: 'Accessible select component supporting single and multiple selection. Provide an `aria-label` or associated `<label>`.'
      }
    },
    controls: { expanded: true }
  }
};

export default meta;
type Story = StoryObj<typeof Select>;

export const Playground: Story = {
  args: {
    placeholder: 'Choose fruit'
  },
  render: (args) => {
    const [value, setValue] = React.useState(args.value as string);
    return (
      <div>
        <Select
          {...args}
          searchable
          value={value}
          onChange={setValue}
          onKeyDown={e => console.log('Key pressed', e.key)}
        />
        <div className="mt-2">Selected: {JSON.stringify(value)}</div>
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story:
          'Use arrow keys to navigate options, type in the search box to filter, and press Enter or Space to select.'
      }
    }
  }
};

export const MultiSelect: Story = {
  render: (args) => {
    const [value, setValue] = React.useState<string[]>([]);
    return (
      <Select {...args} multiple value={value} onChange={setValue} />
    );
  },
  args: {
    options: [
      { value: 'html', label: 'HTML' },
      { value: 'css', label: 'CSS' },
      { value: 'js', label: 'JavaScript' }
    ],
    'aria-label': 'Languages'
  },
  parameters: {
    docs: {
      description: {
        story:
          'Hold Ctrl/Command or Shift while clicking or using arrow keys to select multiple items.'
      }
    }
  }
};
