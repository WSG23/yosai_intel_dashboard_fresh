import { fetchJson, FetchError } from '../utils/fetchJson';
import { log } from './logger';

export interface ServiceError {
  code: string;
  message: string;
  details?: any;
}

export async function request<T>(
  input: RequestInfo,
  init?: RequestInit,
): Promise<T> {
  try {
    return await fetchJson<T>(input, init);
  } catch (err) {
    const error = err as FetchError;
    const serviceError: ServiceError =
      (error.data as ServiceError) || {
        code: 'internal',
        message: error.message,
      };
    log('error', 'API request failed', { url: String(input), ...serviceError });
    throw serviceError;
  }
}
