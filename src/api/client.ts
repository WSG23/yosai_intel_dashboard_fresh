import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import { toast } from 'react-hot-toast';

interface ApiError {
  message: string;
  status: number;
  issues?: string[];
}

interface ApiResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  timestamp?: string;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/v1';
const TIMEOUT = 30000;

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  withCredentials: true,
});

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

apiClient.interceptors.request.use(
  (config) => {

    config.headers['X-Request-ID'] = generateRequestId();
    config.headers['X-Request-Time'] = new Date().toISOString();

    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => {
    const requestTime = response.config.headers['X-Request-Time'];
    if (requestTime) {
      const duration = Date.now() - new Date(requestTime).getTime();
      console.debug(`API call took ${duration}ms: ${response.config.url}`);
    }
    return response;
  },
  async (error: AxiosError<ApiError>) => {
    const { config, response } = error;

    if (!response) {
      if (!isOnline && config) {
        toast.error('You are offline. Request will be retried when connection is restored.');
        requestQueue.push(() => apiClient.request(config));
        return Promise.reject(error);
      }
      toast.error('Network error. Please check your connection.');
      return Promise.reject(error);
    }

    switch (response.status) {
      case 401:
        window.location.href = '/login';
        break;
      case 403:
        toast.error('You do not have permission to perform this action.');
        break;
      case 404:
        toast.error('The requested resource was not found.');
        break;
      case 422:
        const issues = response.data?.issues || ['Validation failed'];
        issues.forEach((i) => toast.error(i));
        break;
      case 429:
        toast.error('Too many requests. Please slow down.');
        break;
      case 500:
        toast.error('Server error. Please try again later.');
        break;
      default:
        toast.error(response.data?.message || 'An unexpected error occurred.');
    }

    return Promise.reject(error);
  }
);

function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export async function apiRequest<T = any>(config: AxiosRequestConfig, retries = 3): Promise<T> {
  let lastError: any;
  for (let i = 0; i < retries; i++) {
    try {
      const response = await apiClient.request<ApiResponse<T>>(config);
      if (response.data.status === 'error') {
        throw new Error(response.data.message || 'Request failed');
      }
      return response.data.data as T;
    } catch (error) {
      lastError = error;
      if (axios.isAxiosError(error) && error.response?.status && error.response.status < 500) {
        throw error;
      }
      if (i < retries - 1) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * Math.pow(2, i)));
      }
    }
  }
  throw lastError;
}

export const api = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) => apiRequest<T>({ ...config, method: 'GET', url }),
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => apiRequest<T>({ ...config, method: 'POST', url, data }),
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => apiRequest<T>({ ...config, method: 'PUT', url, data }),
  delete: <T = any>(url: string, config?: AxiosRequestConfig) => apiRequest<T>({ ...config, method: 'DELETE', url }),
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => apiRequest<T>({ ...config, method: 'PATCH', url, data }),
};

export type { ApiError, ApiResponse };
