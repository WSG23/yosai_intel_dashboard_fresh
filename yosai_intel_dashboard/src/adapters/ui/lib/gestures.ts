import Hammer from 'hammerjs';

let manager: HammerManager | null = null;

/**
 * Returns a singleton Hammer.js gesture manager attached to the given target.
 * Defaults to `document.body` so global gesture handlers can be registered.
 */
export const getGestureManager = (target: HTMLElement = document.body): HammerManager => {
  if (!manager) {
    manager = new Hammer.Manager(target);
    manager.add(new Hammer.Swipe());
    manager.add(new Hammer.Pinch({ enable: true }));
    manager.add(new Hammer.Press({ event: 'press', time: 500 }));
  }
  return manager;
};

export default getGestureManager;
