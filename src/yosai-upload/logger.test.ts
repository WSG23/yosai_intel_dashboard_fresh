import { log } from './logger';

describe('log', () => {
  test('logs info messages using console.log', () => {
    const spy = jest.spyOn(console, 'log').mockImplementation(() => {});
    log('info', 'hello', { foo: 'bar' });
    expect(spy).toHaveBeenCalledTimes(1);
    const entry = JSON.parse(spy.mock.calls[0][0] as string);
    expect(entry.level).toBe('info');
    expect(entry.message).toBe('hello');
    expect(entry.foo).toBe('bar');
    expect(typeof entry.timestamp).toBe('string');
    spy.mockRestore();
  });

  test('uses console.error for error level', () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    log('error', 'oops');
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
});
