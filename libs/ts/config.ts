export type EnvSpec<T> = {
  name: string;
  parse: (raw: string) => T;
  required?: boolean;
  default?: T;
};

function fromRuntime(name: string): string | undefined {
  // Node or bundler
  // @ts-ignore
  if (typeof process !== 'undefined' && process?.env) return process.env[name];
  // Vite-style
  // @ts-ignore
  if (typeof import !== 'undefined' && (import as any)?.meta?.env)
    return (import as any).meta.env[name];
  return undefined;
}

export function loadEnv<T>(spec: EnvSpec<T>): T {
  const raw = fromRuntime(spec.name);
  if (raw == null || raw === '') {
    if (spec.required && spec.default === undefined)
      throw new Error(`Missing required env: ${spec.name}`);
    return spec.default as T;
  }
  try {
    return spec.parse(raw);
  } catch (e: any) {
    throw new Error(`Invalid env ${spec.name}: ${raw}`);
  }
}

