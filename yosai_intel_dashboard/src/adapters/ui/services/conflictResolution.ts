export interface VersionedEntity {
  id: string;
  updatedAt: number;
  [key: string]: any;
}

export function resolveConflict<T extends VersionedEntity>(local: T | undefined, remote: T | undefined): T | undefined {
  if (!local) return remote;
  if (!remote) return local;
  return local.updatedAt > remote.updatedAt ? local : remote;
}

export function reconcileLists<T extends VersionedEntity>(local: T[], remote: T[]): T[] {
  const map = new Map<string, T>();
  remote.forEach((item) => map.set(item.id, item));
  local.forEach((item) => {
    const existing = map.get(item.id);
    map.set(item.id, resolveConflict(item, existing)!);
  });
  return Array.from(map.values());
}
