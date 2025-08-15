export interface CancelablePromise<T> extends Promise<T> {
  cancel: () => void;
}

interface WindowWithRequestIdleCallback extends Window {
  requestIdleCallback: (callback: () => void) => number;
}

export const requestIdleCallback = (cb: () => void): number => {
  if (
    typeof window !== 'undefined' &&
    typeof (window as Partial<WindowWithRequestIdleCallback>).requestIdleCallback === 'function'
  ) {
    return (window as WindowWithRequestIdleCallback).requestIdleCallback(cb);
  }
  return setTimeout(cb, 0);
};
