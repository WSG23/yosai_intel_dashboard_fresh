import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import { request } from './api';
import { log } from './logger';

jest.mock('./api');
jest.mock('./logger', () => ({ log: jest.fn() }));

test('renders learn react link', async () => {
  (request as jest.Mock).mockResolvedValue({});
  render(<App />);
  await Promise.resolve();
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});

describe('App ping', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  test('logs success when ping succeeds', async () => {
    (request as jest.Mock).mockResolvedValue({});
    render(<App />);
    await screen.findByText(/learn react/i); // wait render
    await Promise.resolve();
    expect(request).toHaveBeenCalledWith('/api/ping');
    expect(log).toHaveBeenCalledWith('info', 'ping ok');
  });

  test('logs error when ping fails', async () => {
    (request as jest.Mock).mockRejectedValue({ message: 'bad' });
    render(<App />);
    await screen.findByText(/learn react/i);
    await Promise.resolve();
    expect(log).toHaveBeenCalledWith('error', 'ping failed', { message: 'bad' });
  });
});
