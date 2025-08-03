import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { api } from '../client';
import { toast } from 'react-hot-toast';

jest.mock('react-hot-toast', () => ({ toast: { error: jest.fn() } }));

const Greeting: React.FC = () => {
  const [msg, setMsg] = React.useState('');
  React.useEffect(() => {
    api
      .get<{ message: string }>('/greeting')
      .then((res) => setMsg(res.message))
      .catch(() => {});
  }, []);
  return <div>{msg}</div>;
};

describe('component using api client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders data on success', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'success', data: { message: 'hi' } }),
    }) as any;
    render(<Greeting />);
    expect(await screen.findByText('hi')).toBeInTheDocument();
  });

  it('shows toast on failure', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ code: 'internal', message: 'oops' }),
    }) as any;
    render(<Greeting />);
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        'Server error. Please try again later.'
      );
    });
  });
});

