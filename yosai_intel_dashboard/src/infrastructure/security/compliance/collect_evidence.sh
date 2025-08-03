#!/bin/bash
# Collects audit evidence such as configs, logs, and system information.
set -e
OUTPUT_DIR=${1:-evidence}
mkdir -p "$OUTPUT_DIR"

echo "Collecting system information..."
uname -a > "$OUTPUT_DIR/system_info.txt"

echo "Collecting running processes..."
ps aux > "$OUTPUT_DIR/process_list.txt"

echo "Collecting application logs..."
if [ -d logs ]; then
  cp -r logs "$OUTPUT_DIR"/
fi

echo "Archiving evidence..."
tar -czf "$OUTPUT_DIR.tgz" "$OUTPUT_DIR"

echo "Evidence collected in $OUTPUT_DIR.tgz"
