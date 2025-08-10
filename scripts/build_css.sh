#!/usr/bin/env bash
set -euo pipefail
NODE_ENV=development postcss assets/css/main.css -o assets/dist/main.css
printf '/* This file is auto-generated. Do not edit directly. */\n' | cat - assets/dist/main.css > assets/dist/main.css.tmp
mv assets/dist/main.css.tmp assets/dist/main.css
NODE_ENV=production postcss assets/css/main.css -o assets/dist/main.min.css --map
