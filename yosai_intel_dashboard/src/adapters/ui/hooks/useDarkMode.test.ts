import { renderHook, act } from '@testing-library/react';
import useDarkMode from './useDarkMode';

describe('useDarkMode', () => {
  beforeEach(() => {
    document.documentElement.classList.remove('dark');
    window.localStorage.clear();
  });

  it('toggles dark class on root element', () => {
    const { result } = renderHook(() => useDarkMode());
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    act(() => result.current.toggle());
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    act(() => result.current.toggle());
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
});
