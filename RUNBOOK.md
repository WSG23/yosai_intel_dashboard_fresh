# Yōsai Intel — Dev Runbook

## Start (Docker, dev mode)
docker compose -f compose.dev.yml up -d --build
bash scripts/ui-probe.sh   # shows UI URL, API health, proxy checks

## Stop
bash scripts/mvp-stack-stop.sh

## Local (no Docker)
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY='dev'
uvicorn mvp_api:app --host 0.0.0.0 --port 8000 --reload
cd mvp-ui && npm install && npm run dev

## Notes
- UI runs on the first free port starting at 5173 (compose uses 5175).  
- Proxy path is `/api/*` → backend at `http://api:8000` in Docker, `http://localhost:8000` locally.
- Metrics/profiling via env: ENABLE_METRICS=1, YOSAI_ENABLE_PROFILING=0
