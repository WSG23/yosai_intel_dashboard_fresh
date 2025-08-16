import os, csv, io
from .plugin_loader import load_callable
_ENRICH = os.getenv("ENRICH_HANDLER", "").strip()
_FN = load_callable(_ENRICH) if _ENRICH else None
def enrich_csv_content(text: str) -> dict:
    if _FN:
        return _FN(text)
    reader = csv.DictReader(io.StringIO(text))
    rows = [dict(r) for r in reader]
    cols = list(rows[0].keys()) if rows else []
    return {"rows": rows, "columns": cols}
