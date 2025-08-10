export function t(key: string): string {
  const translator = (window as any).t;
  if (typeof translator === 'function') {
    return translator(key);
  }
  return key;
}
