#!/usr/bin/env bash
# Pre-commit hook: block staged files over 2 MB (raw data belongs in data/, which is git-ignored).
set -euo pipefail
limit=2097152
status=0
for f in "$@"; do
  size=$(wc -c < "$f")
  if [ "$size" -gt "$limit" ]; then
    echo "too large (>2 MB): $f ($size bytes)"
    status=1
  fi
done
exit "$status"
