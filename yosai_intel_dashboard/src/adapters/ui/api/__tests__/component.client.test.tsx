import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
jest.mock('axios', () => require('axios/dist/node/axios.cjs'));
import { api, apiClient } from '../client';
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
    jest.spyOn(api, 'get').mockResolvedValueOnce({ message: 'hi' } as any);
    render(<Greeting />);
    expect(await screen.findByText('hi')).toBeInTheDocument();
  });

  it('shows toast on failure', async () => {
    const error = {
      config: { url: '/greeting', headers: {} },
      response: { status: 500, data: { code: 'internal', message: 'oops' }, config: {}, headers: {} },
    } as any;
    jest.spyOn(api, 'get').mockRejectedValueOnce(error);
    const handler = apiClient.interceptors.response.handlers[0].rejected!;
    render(<Greeting />);
    await handler(error).catch(() => {});
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Server error. Please try again later.');
    });
  });
});
