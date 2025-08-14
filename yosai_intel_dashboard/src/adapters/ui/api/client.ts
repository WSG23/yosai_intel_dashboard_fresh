import { toast } from 'react-hot-toast';

interface ApiError {
  message: string;
  status: number;
  issues?: string[];
}

interface ServiceError {
  code: string;
  message: string;
  details?: any;
}

interface ApiResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  timestamp?: string;
}

export interface AuthHeaders {
  Authorization?: string;
}

export interface CsrfHeaders {
  'X-CSRF-Token'?: string;
}

export type ApiHeaders = Record<string, string> & AuthHeaders & CsrfHeaders;

const API_BASE_URL =
  process.env.REACT_APP_API_URL || 'http://localhost:5001/api/v1';
const TIMEOUT = 30000;

const requestQueue: Array<() => Promise<any>> = [];
let isOnline = navigator.onLine;

window.addEventListener('online', () => {
  isOnline = true;
  processQueue();
});

window.addEventListener('offline', () => {
  isOnline = false;
});

const processQueue = async () => {
  while (requestQueue.length > 0) {
    const request = requestQueue.shift();
    if (request) {
      try {
        await request();
      } catch (error) {
        console.error('Failed to process queued request:', error);
      }
    }
  }
};

class HttpError extends Error {
  status: number;
  code?: string;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export function getCsrfToken(): string | undefined {
  return document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrf_token='))
    ?.split('=')[1];
}

export function authHeader(token: string): AuthHeaders {
  return { Authorization: `Bearer ${token}` };
}

export function csrfHeader(token?: string): CsrfHeaders {
  const value = token ?? getCsrfToken();
  return value ? { 'X-CSRF-Token': value } : {};
}

export interface ApiRequestConfig extends Omit<RequestInit, 'headers'> {
  url: string;
  data?: any;
  params?: Record<string, any>;
  responseType?: 'json' | 'blob';
  headers?: ApiHeaders;
}

function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function randomHex(size: number): string {
  const arr = new Uint8Array(size);
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    crypto.getRandomValues(arr);
  } else {
    const nodeCrypto = require('crypto');
    const buf = nodeCrypto.randomBytes(size);
    arr.set(buf);
  }
  return Array.from(arr)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function generateTraceParent(): string {
  const traceId = randomHex(16); // 16 bytes -> 32 hex chars
  const spanId = randomHex(8); // 8 bytes -> 16 hex chars
  return `00-${traceId}-${spanId}-01`;
}

function buildUrl(base: string, params?: Record<string, any>): string {
  if (!params) return base;
  const search = new URLSearchParams(
    params as Record<string, string>,
  ).toString();
  if (!search) return base;
  return `${base}${base.includes('?') ? '&' : '?'}${search}`;
}

async function safeJson(response: Response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function handleErrorResponse(data: any, status: number, url: string): never {
  const code = data?.code;
  const msg = data?.message || 'An unexpected error occurred.';

  let toastMsg: string | undefined;
  switch (code) {
    case 'invalid_input':
      toastMsg = 'Request validation failed';
      break;
    case 'unauthorized':
      toastMsg = 'You are not authorized to perform this action.';
      if (status === 401) {
        window.location.href = '/login';
      }
      break;
    case 'not_found':
      toastMsg = 'The requested resource was not found.';
      break;
    case 'internal':
      toastMsg = 'Server error. Please try again later.';
      break;
    case 'unavailable':
      toastMsg = 'Service temporarily unavailable. Please try again later.';
      break;
    default:
      toastMsg = msg;
  }

  toast.error(toastMsg);

  console.error(
    JSON.stringify({
      level: 'error',
      code: code || 'unknown',
      message: msg,
      status,
      url,
    }),
  );

  throw new HttpError(msg, status, code);
}

export async function apiRequest<T = any>(
  config: ApiRequestConfig,
  retries = 3,
): Promise<T> {
  let lastError: unknown;
  for (let i = 0; i < retries; i++) {
    const {
      url,
      data,
      params,
      headers,
      responseType = 'json',
      ...rest
    } = config;

    const finalUrl = buildUrl(
      url.startsWith('http') ? url : `${API_BASE_URL}${url}`,
      params,
    );

    const finalHeaders: ApiHeaders = {
      Accept: 'application/json',
      ...(data instanceof FormData
        ? {}
        : { 'Content-Type': 'application/json' }),
      ...(headers as ApiHeaders),
      'X-Request-ID': generateRequestId(),
      'X-Request-Time': new Date().toISOString(),
    };
    if (!finalHeaders['traceparent']) {
      finalHeaders['traceparent'] = generateTraceParent();
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT);
    const start = Date.now();

    try {
      const response = await fetch(finalUrl, {
        ...rest,
        method: rest.method || 'GET',
        headers: finalHeaders,
        body: data
          ? data instanceof FormData
            ? data
            : JSON.stringify(data)
          : undefined,
        credentials: 'include',
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const duration = Date.now() - start;
      console.debug(`API call took ${duration}ms: ${finalUrl}`);

      if (!response.ok) {
        const errorData = await safeJson(response);
        handleErrorResponse(errorData, response.status, finalUrl);
      }

      if (responseType === 'blob') {
        return (await response.blob()) as unknown as T;
      }

      const payload = (await response.json()) as ApiResponse<T>;
      if (payload.status === 'error') {
        throw new HttpError(
          payload.message || 'Request failed',
          response.status,
        );
      }
      return payload.data as T;
    } catch (error: unknown) {
      clearTimeout(timeout);
      lastError = error;
      if (error instanceof HttpError) {
        if (error.status < 500) {
          throw error;
        }
      } else {
        if (!isOnline) {
          toast.error(
            'You are offline. Request will be retried when connection is restored.',
          );
          if (requestQueue.length >= 50) {
            requestQueue.shift();
            console.warn(
              'Request queue limit reached. Dropping oldest request.',
            );
          }
          requestQueue.push(() => apiRequest(config));
          return Promise.reject(error);
        }
        toast.error('Network error. Please check your connection.');
        console.error(
          JSON.stringify({
            level: 'error',
            message: 'Network error',
            url: finalUrl,
          }),
        );
      }

      if (i < retries - 1) {
        await new Promise((resolve) =>
          setTimeout(resolve, 1000 * Math.pow(2, i)),
        );
      }
    }
  }
  throw lastError;
}

export const api = {
  get: <T = any>(
    url: string,
    config?: Omit<ApiRequestConfig, 'url' | 'method'>,
  ) => apiRequest<T>({ ...config, method: 'GET', url }),
  post: <T = any>(
    url: string,
    data?: any,
    config?: Omit<ApiRequestConfig, 'url' | 'method' | 'data'>,
  ) => apiRequest<T>({ ...config, method: 'POST', url, data }),
  put: <T = any>(
    url: string,
    data?: any,
    config?: Omit<ApiRequestConfig, 'url' | 'method' | 'data'>,
  ) => apiRequest<T>({ ...config, method: 'PUT', url, data }),
  delete: <T = any>(
    url: string,
    config?: Omit<ApiRequestConfig, 'url' | 'method'>,
  ) => apiRequest<T>({ ...config, method: 'DELETE', url }),
  patch: <T = any>(
    url: string,
    data?: any,
    config?: Omit<ApiRequestConfig, 'url' | 'method' | 'data'>,
  ) => apiRequest<T>({ ...config, method: 'PATCH', url, data }),
};

export type { ApiError, ApiResponse, AuthHeaders, CsrfHeaders };
