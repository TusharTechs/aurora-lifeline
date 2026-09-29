#!/usr/bin/env bash
# Sentinel-1 flood mask for Cyclone Montha (ENGINE §10), computed in Earth Engine, for the proof
# page. Run in Cloud Shell after 01_bootstrap.sh:
#   cd ~/aurora-lifeline && git pull && bash infra/cloudshell/04_sentinel1.sh
# Prints scene metadata and nine short-lived GeoTIFF download links; paste the whole output back.
# Uses the Earth Engine Community tier (a few EECU-minutes; well under the "large job" limit).
set -euo pipefail
PROJECT="${PROJECT:-aurora-lifeline}"
cd "$(git rev-parse --show-toplevel)"
test -x "$HOME/.aurora-venv/bin/python" || { echo "run 01_bootstrap.sh first" >&2; exit 1; }
"$HOME/.aurora-venv/bin/python" pipelines/aurora_pipelines/ee_s1_flood.py \
  --project "$PROJECT" --t 2025-10-28T18:30:00Z \
  --bbox 80.371 15.442 82.887 17.923 --out "$HOME/s1_montha.json" 2>&1 | grep -v "^WARNING"
