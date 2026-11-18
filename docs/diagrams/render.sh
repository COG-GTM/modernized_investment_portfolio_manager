#!/usr/bin/env bash
# Renders docs/diagrams/*.dot to PNG and SVG. Needs Graphviz (`apt-get install graphviz`).
set -euo pipefail
cd "$(dirname "$0")"
for src in *.dot; do
  name="${src%.dot}"
  dot -Tpng -Gdpi=150 "$src" -o "$name.png"
  dot -Tsvg "$src" -o "$name.svg"
done
