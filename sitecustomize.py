# Auto-loaded by Python at startup if present on sys.path.
# Shim old SQLAlchemy import paths so legacy code keeps running.
try:
    import sqlalchemy.sql as _sa_sql
    from sqlalchemy.sql.elements import TextClause as _TextClause
    _sa_sql.TextClause = _TextClause  # makes: from sqlalchemy.sql import TextClause work again
except Exception as e:
    import sys
    print(f"[sitecustomize] SQLAlchemy shim not applied: {e}", file=sys.stderr)
