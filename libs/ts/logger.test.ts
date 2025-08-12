import { base } from './logger';

describe('base logger', () => {
  it('omits extra on circular references', () => {
    const extra: any = {};
    extra.self = extra;
    const output = base('info', 'with circular', extra);
    const parsed = JSON.parse(output);
    expect(parsed.message).toContain('serialization error');
    expect(parsed.self).toBeUndefined();
  });

  it('omits extra on unserializable values', () => {
    const extra: any = { value: BigInt(1) };
    const output = base('info', 'with bigint', extra);
    const parsed = JSON.parse(output);
    expect(parsed.message).toContain('serialization error');
    expect(parsed.value).toBeUndefined();
  });
});
