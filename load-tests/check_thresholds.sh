#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(dirname "$0")/.."
BUDGETS_FILE="$ROOT_DIR/config/performance_budgets.yml"

for f in "$@"; do
  name="$(basename "$f" .json)"
  endpoint="/$name"
  p50=$(jq -r '.metrics.http_req_duration["p(50)"]' "$f")
  p95=$(jq -r '.metrics.http_req_duration["p(95)"]' "$f")
  p99=$(jq -r '.metrics.http_req_duration["p(99)"]' "$f")
  python - "$BUDGETS_FILE" "$endpoint" "$p50" "$p95" "$p99" <<'PY'
import sys, yaml
budgets_file, endpoint, p50, p95, p99 = sys.argv[1:]
with open(budgets_file) as fh:
    budgets = yaml.safe_load(fh).get("endpoints", {})
budget = budgets.get(endpoint)
if not budget:
    sys.exit(0)
violations = []
if float(p50) > budget.get("p50", float("inf")):
    violations.append(f"p50 {p50}ms > {budget['p50']}ms")
if float(p95) > budget.get("p95", float("inf")):
    violations.append(f"p95 {p95}ms > {budget['p95']}ms")
if float(p99) > budget.get("p99", float("inf")):
    violations.append(f"p99 {p99}ms > {budget['p99']}ms")
if violations:
    msg = f"{endpoint} exceeds budget: " + ", ".join(violations)
    print(msg, file=sys.stderr)
    sys.exit(1)
PY
done
