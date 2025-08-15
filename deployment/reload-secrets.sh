#!/usr/bin/env sh
# Watches the mounted secret directory and sends HUP to the service process
# when any secret is updated. Requires inotify-tools in the image.

set -eu
SECRET_DIR=${SECRET_DIR:-/etc/secrets}
PID_FILE=${PID_FILE:-/var/run/service.pid}

inotifywait -m "$SECRET_DIR" -e modify,create,delete,move |
while read -r _ _ file; do
  if [ -f "$PID_FILE" ]; then
    kill -HUP "$(cat "$PID_FILE")"
  fi
  echo "reloaded secret $file" >&2
done
