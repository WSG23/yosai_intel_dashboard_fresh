export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  [key: string]: unknown;
}

export function base(
  level: LogLevel,
  message: string,
  extra: Record<string, unknown> = {},
): string {
  const entry: LogEntry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...extra,
  };
  try {
    return JSON.stringify(entry);
  } catch (err) {
    return JSON.stringify({
      timestamp: entry.timestamp,
      level,
      message: `${message} (serialization error: ${(err as Error).message})`,
    });
  }
}

export function info(message: string, extra?: Record<string, unknown>): string {
  return base('info', message, extra);
}

export function warn(message: string, extra?: Record<string, unknown>): string {
  return base('warn', message, extra);
}

export function error(message: string, extra?: Record<string, unknown>): string {
  return base('error', message, extra);
}
