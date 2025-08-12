#!/usr/bin/env bash
# shellcheck shell=bash
set -euo pipefail
IFS=$'\n\t'

on_err() {
  local exit_code=$?
  echo "ERR: ${BASH_SOURCE[1]}:${BASH_LINENO[0]} — command '${BASH_COMMAND}' exited ${exit_code}" >&2
  exit "${exit_code}"
}
trap on_err ERR

# Safe mktemp wrapper (dir)
mktempd() { mktemp -d 2>/dev/null || mktemp -d -t tmp; }

# Require tools
require() {
  for bin in "$@"; do command -v "$bin" >/dev/null 2>&1 || { echo "Missing '$bin'"; exit 127; }; done
}
