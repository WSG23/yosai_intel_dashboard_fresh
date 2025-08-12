from __future__ import annotations

import json
import subprocess
import sys

REQ_FILES = ["requirements.txt", "requirements-dev.txt"]

cmd = ["safety", "check", "--full-report", "--json"]
for req in REQ_FILES:
    cmd.extend(["-r", req])

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
except FileNotFoundError:
    print("The 'safety' CLI is not installed or not found in PATH", file=sys.stderr)
    raise SystemExit(1)
except subprocess.CalledProcessError as exc:
    if exc.returncode != 1:
        print(exc.stdout)
        print(exc.stderr, file=sys.stderr)
        print(f"'safety' exited unexpectedly with code {exc.returncode}", file=sys.stderr)
        raise SystemExit(exc.returncode)
    result = exc

try:
    vulnerabilities = json.loads(result.stdout)
except json.JSONDecodeError as exc:
    print("Failed to parse Safety output", file=sys.stderr)
    print(result.stdout)
    raise SystemExit(1) from exc

high_vulns = [
    v for v in vulnerabilities if v.get("severity", "").lower() in {"high", "critical"}
]

if high_vulns:
    print("High severity vulnerabilities detected:")
    for vuln in high_vulns:
        pkg = vuln.get("package_name")
        version = vuln.get("analyzed_version")
        ident = vuln.get("vulnerability_id")
        sev = vuln.get("severity")
        print(f"- {pkg} {version}: {ident} ({sev})")
    sys.exit(1)

print("No high severity vulnerabilities found.")
