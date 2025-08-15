# Auto-loaded if present on sys.path (e.g., /app).
# Keeps legacy SA import path working and cushions callback signature changes.
try:
    import sqlalchemy.sql as _sa_sql
    from sqlalchemy.sql.elements import TextClause as _TextClause
    setattr(_sa_sql, "TextClause", _TextClause)
except Exception as e:
    import sys
    print(f"[sitecustomize] SQLAlchemy shim not applied: {e}", file=sys.stderr)

# Best-effort shim for libraries that now require callback_id/component_name.
# If the target class/module name differs in your codebase, this no-ops harmlessly.
try:
    # Try common import names; ignore failures.
    try:
        from truly_unified_callbacks import TrulyUnifiedCallbacks as _TUC  # adjust if different
    except Exception:
        _TUC = None
    if _TUC:
        _orig = _TUC.register_handler
        def _wrapper(*args, **kwargs):
            kwargs.setdefault("callback_id", "default")
            kwargs.setdefault("component_name", "unknown")
            return _orig(*args, **kwargs)
        try:
            # handle possible @staticmethod
            if isinstance(_TUC.register_handler, staticmethod):
                _TUC.register_handler = staticmethod(_wrapper)
            else:
                _TUC.register_handler = _wrapper
        except Exception:
            pass
except Exception:
    pass
