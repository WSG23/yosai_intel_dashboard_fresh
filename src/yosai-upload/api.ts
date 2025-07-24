import { log } from './logger';

export interface ServiceError {
  code: string;
  message: string;
  details?: any;
}

export async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  const data = await response.json().catch(() => undefined);
  if (!response.ok) {
    const err: ServiceError = data || { code: 'internal', message: 'Unknown error' };
    log('error', 'API request failed', { url: String(input), ...err });
    throw err;
  }
  return data as T;
}
