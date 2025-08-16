#!/usr/bin/env bash
set -euo pipefail
tail -n +1 -f /tmp/mvp_api.log /tmp/mvp_ui.log
