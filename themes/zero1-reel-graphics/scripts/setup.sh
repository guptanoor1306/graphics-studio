#!/usr/bin/env bash
# Writes an absolute-path fonts.css for this machine: bash setup.sh <work_dir>
set -e; S="$(cd "$(dirname "$0")/.." && pwd)"; W="${1:-$PWD}"; mkdir -p "$W"
sed "s#__FONTS__#$S/assets/fonts#g" "$S/assets/fonts.css.template" > "$W/fonts.css"
python3 -c "import playwright" 2>/dev/null || pip install --break-system-packages playwright
echo "fonts.css -> $W/fonts.css"
