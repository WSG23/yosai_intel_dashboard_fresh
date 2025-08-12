const LEVELS = ['debug', 'info', 'warn', 'error'] as const;
export type LogLevel = typeof LEVELS[number];

function resolveLevel(raw?: string): LogLevel {
  const lvl = raw?.toLowerCase();
  return LEVELS.includes(lvl as LogLevel) ? (lvl as LogLevel) : 'info';
}

export function createLogger(name: string, level?: string) {
  // @ts-ignore process may be undefined in some runtimes
  const env = level ?? (typeof process !== 'undefined' ? process?.env?.LOG_LEVEL : undefined);
  const resolved = resolveLevel(env);
  const threshold = LEVELS.indexOf(resolved);

  const log = (lvl: LogLevel) => (...args: any[]) => {
    if (LEVELS.indexOf(lvl) < threshold) return;
    const message = args.length === 1 ? args[0] : args;
    console[lvl](JSON.stringify({ name, level: lvl, message }));
  };

  return {
    debug: log('debug'),
    info: log('info'),
    warn: log('warn'),
    error: log('error'),
  };
}

