# API Reference

## Health-Check Endpoints


### `GET /health`

**Summary:** Health

**FastAPI**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    ...
```

**Flask**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify()
```

**curl**
```bash
curl -X GET http://localhost:8000/health
```


### `GET /health/live`

**Summary:** Health Live

**FastAPI**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health/live")
async def health_live():
    ...
```

**Flask**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health/live", methods=["GET"])
def health_live():
    return jsonify()
```

**curl**
```bash
curl -X GET http://localhost:8000/health/live
```


### `GET /health/ready`

**Summary:** Health Ready

**FastAPI**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health/ready")
async def health_ready():
    ...
```

**Flask**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health/ready", methods=["GET"])
def health_ready():
    return jsonify()
```

**curl**
```bash
curl -X GET http://localhost:8000/health/ready
```


### `GET /health/startup`

**Summary:** Health Startup

**FastAPI**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health/startup")
async def health_startup():
    ...
```

**Flask**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health/startup", methods=["GET"])
def health_startup():
    return jsonify()
```

**curl**
```bash
curl -X GET http://localhost:8000/health/startup
```

## Metrics Endpoints


### `GET /api/v1/metrics/drift`

**Summary:** Return sample drift statistics.

**FastAPI**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/v1/metrics/drift")
async def v1_metrics_drift():
    ...
```

**Flask**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/v1/metrics/drift", methods=["GET"])
def v1_metrics_drift():
    return jsonify()
```

**curl**
```bash
curl -X GET http://localhost:8000/api/v1/metrics/drift
```


### `GET /api/v1/metrics/feature-importance`

**Summary:** Return sample feature importances.

**FastAPI**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/v1/metrics/feature-importance")
async def v1_metrics_feature_importance():
    ...
```

**Flask**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/v1/metrics/feature-importance", methods=["GET"])
def v1_metrics_feature_importance():
    return jsonify()
```

**curl**
```bash
curl -X GET http://localhost:8000/api/v1/metrics/feature-importance
```


### `GET /api/v1/metrics/performance`

**Summary:** Return sample performance metrics.

**FastAPI**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/v1/metrics/performance")
async def v1_metrics_performance():
    ...
```

**Flask**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/v1/metrics/performance", methods=["GET"])
def v1_metrics_performance():
    return jsonify()
```

**curl**
```bash
curl -X GET http://localhost:8000/api/v1/metrics/performance
```
