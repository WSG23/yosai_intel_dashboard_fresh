import { describe, it, expect, vi, afterEach, expectTypeOf } from 'vitest';
import { createLogger, type Logger } from './logger';

const ORIGINAL = process.env.LOG_LEVEL;

afterEach(() => {
  if (ORIGINAL === undefined) delete process.env.LOG_LEVEL;
  else process.env.LOG_LEVEL = ORIGINAL;
  vi.restoreAllMocks();
});

describe('createLogger LOG_LEVEL handling', () => {
  it('honors valid LOG_LEVEL', () => {
    process.env.LOG_LEVEL = 'warn';
    const logger: Logger = createLogger('test');
    const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    const infoSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    logger.debug('debug');
    logger.info('info');
    logger.warn('warn');
    logger.error('error');
    expect(debugSpy).not.toHaveBeenCalled();
    expect(infoSpy).not.toHaveBeenCalled();
    expect(warnSpy).toHaveBeenCalledOnce();
    expect(errorSpy).toHaveBeenCalledOnce();
  });

  it('falls back to info on invalid LOG_LEVEL', () => {
    process.env.LOG_LEVEL = 'verbose';
    const logger: Logger = createLogger('test');
    const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    const infoSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
    logger.debug('debug');
    logger.info('info');
    expect(debugSpy).not.toHaveBeenCalled();
    expect(infoSpy).toHaveBeenCalledOnce();
  });

  it('defaults to info when LOG_LEVEL unset', () => {
    delete process.env.LOG_LEVEL;
    const logger: Logger = createLogger('test');
    const debugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    const infoSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
    logger.debug('debug');
    logger.info('info');
    expect(debugSpy).not.toHaveBeenCalled();
    expect(infoSpy).toHaveBeenCalledOnce();
  });
});

it('returns object satisfying Logger interface', () => {
  const logger = createLogger('test');
  expectTypeOf(logger).toMatchTypeOf<Logger>();
  expect(typeof logger.debug).toBe('function');
  expect(typeof logger.info).toBe('function');
  expect(typeof logger.warn).toBe('function');
  expect(typeof logger.error).toBe('function');
});
