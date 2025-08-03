import { useEffect, useRef } from 'react';

/**
 * Provides utilities for keeping visualizations performant by
 * throttling rendering to a target frame rate and offloading heavy
 * computations to WebWorkers.
 */
const useVisualizationPerformance = () => {
  const rafRef = useRef<number>();

  /**
   * Wraps a callback so that it runs at most once per frame.
   * Returns a function that cancels the scheduled work.
   */
  const throttleToFrameRate = (callback: () => void, fps: number = 60) => {
    const frameDuration = 1000 / fps;
    let last = 0;

    const loop = (time: number) => {
      if (time - last >= frameDuration) {
        last = time;
        callback();
      }
      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = undefined;
      }
    };
  };

  /**
   * Creates a helper for running work inside a WebWorker. The returned
   * function accepts data and resolves with the worker's response.
   */
  const runInWorker = <T, R>(fn: (input: T) => R) => {
    const blob = new Blob(
      [`self.onmessage = e => { postMessage((${fn.toString()})(e.data)); };`],
      { type: 'text/javascript' }
    );
    const worker = new Worker(URL.createObjectURL(blob));

    return (data: T): Promise<R> =>
      new Promise(resolve => {
        worker.onmessage = ev => resolve(ev.data as R);
        worker.postMessage(data);
      });
  };

  useEffect(
    () => () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    },
    []
  );

  return { throttleToFrameRate, runInWorker } as const;
};

export default useVisualizationPerformance;

