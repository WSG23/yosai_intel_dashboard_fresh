export interface FetchJsonOptions extends RequestInit {
  headers?: Record<string, string>;
}

export interface FetchError extends Error {
  status?: number;
  data?: any;
}

export async function fetchJson<T>(
  input: RequestInfo,
  init: FetchJsonOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(init.body && !(init.body instanceof FormData)
      ? { 'Content-Type': 'application/json' }
      : {}),
    ...(init.headers || {}),
  };

  const response = await fetch(input, { ...init, headers });
  let data: any;
  try {
    data = await response.json();
  } catch {
    data = undefined;
  }

  if (!response.ok) {
    const error: FetchError = new Error(
      data?.message || data?.error || response.statusText,
    );
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data as T;
}
