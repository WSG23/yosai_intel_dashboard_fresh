export type Listener<T = unknown> = (payload: T) => void;

class EventBus {
  private listeners: Map<string, Set<Listener>> = new Map();

  on<T>(event: string, listener: Listener<T>): () => void {
    const set = this.listeners.get(event) ?? new Set<Listener>();
    set.add(listener as Listener);
    this.listeners.set(event, set);
    return () => this.off(event, listener);
  }

  off<T>(event: string, listener: Listener<T>): void {
    const set = this.listeners.get(event);
    set?.delete(listener as Listener);
    if (set && set.size === 0) {
      this.listeners.delete(event);
    }
  }

  emit<T>(event: string, payload: T): void {
    const set = this.listeners.get(event);
    set?.forEach(listener => listener(payload));
  }
}

export const eventBus = new EventBus();
export default eventBus;
