export type RetryOpts = {
  attempts?: number;
  baseDelayMs?: number;
  jitter?: number;
  signal?: AbortSignal;
};

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((res, rej) => {
    const t = setTimeout(res, ms);
    if (signal) {
      const onAbort = () => {
        clearTimeout(t);
        rej(new DOMException('Aborted', 'AbortError'));
      };
      signal.addEventListener('abort', onAbort, { once: true });
    }
  });
}

function jittered(ms: number, jitter = 0.2): number {
  const delta = ms * jitter;
  return Math.max(0, ms + (Math.random() * 2 * delta - delta));
}

export async function retry<T>(
  fn: () => Promise<T> | T,
  opts: RetryOpts = {},
): Promise<T> {
  const attempts = opts.attempts ?? 3;
  const base = opts.baseDelayMs ?? 200;
  for (let i = 1; i <= attempts; i++) {
    try {
      const v = fn();
      return v instanceof Promise ? await v : v;
    } catch (e) {
      if (i === attempts) throw e;
      await sleep(
        jittered(base * Math.pow(2, i - 1), opts.jitter),
        opts.signal,
      );
    }
  }
  // unreachable
  // @ts-ignore
  return undefined;
}
