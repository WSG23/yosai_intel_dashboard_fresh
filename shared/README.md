# Shared Libraries (Python & TS)

## Python
`shared/python/config_loader.py` – typed env access (`get_str/get_int/get_bool`) with errors on bad input.
`shared/python/yosai_logging.py` – JSON logger; call `get_logger("name")`.
`shared/python/retry.py` – `retry()` and `aretry()` with exp-backoff + jitter.
`shared/python/unicode_sanitize.py` – `clean_surrogates()` to replace isolated surrogates with U+FFFD.

## TypeScript
`libs/ts/config.ts` – `loadEnv({ name, parse, required?, default? })`.
`libs/ts/logger.ts` – `createLogger(name, level?)` JSON console logs.
`libs/ts/retry.ts` – `retry(fn, { attempts, baseDelayMs, jitter, signal })`.

> Import these from `yosai_intel_dashboard.src.services.pages` to eliminate duplicate helpers and to enforce consistent behavior across the stack.
