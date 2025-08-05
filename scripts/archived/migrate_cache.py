import json
import os

import dill
import redis


def migrate():
    client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
    )
    for key in client.keys():
        data = client.get(key)
        if not data:
            continue
        try:
            json.loads(data.decode("utf-8"))
            continue  # already JSON
        except Exception:
            pass
        try:
            obj = dill.loads(data)
        except Exception:
            client.delete(key)
            continue
        client.set(key, json.dumps(obj).encode("utf-8"))


if __name__ == "__main__":
    migrate()
