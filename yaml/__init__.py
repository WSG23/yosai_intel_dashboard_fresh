import json

def safe_load(stream):
    if isinstance(stream, str):
        try:
            return json.loads(stream)
        except Exception:
            return {}
    return {}

def dump(data):
    return json.dumps(data)
