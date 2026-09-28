#!/usr/bin/env bash
# Approval-free raw downloads for the Montha 2025 slice (BUILD_PLAN task 1.4a).
# Writes to data/raw/<source>/<version>/ and records sha256sums.txt per directory.
# Re-runnable: existing files are skipped.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RAW="$ROOT/data/raw"
FIRST_DAY="${FIRST_DAY:-20251023}"
LAST_DAY="${LAST_DAY:-20251029}"
WITH_OSM="${WITH_OSM:-1}"

fetch() {  # fetch <url> <dest_dir> [<filename>]
  local url="$1" dir="$2" name="${3:-$(basename "$1")}"
  mkdir -p "$dir"
  if [[ -s "$dir/$name" ]]; then return 0; fi
  if curl -fsSL --retry 3 --retry-delay 5 -o "$dir/$name.part" "$url"; then
    mv "$dir/$name.part" "$dir/$name"
    echo "OK   $url"
  else
    rm -f "$dir/$name.part"
    echo "MISS $url"
  fi
}

checksum() {  # checksum <dir>
  (cd "$1" && find . -type f ! -name sha256sums.txt ! -name '*.part' | sort | xargs shasum -a 256 > sha256sums.txt)
}

days() {
  local d="$FIRST_DAY"
  while [[ "$d" -le "$LAST_DAY" ]]; do
    echo "$d"
    d=$(date -j -v+1d -f %Y%m%d "$d" +%Y%m%d 2>/dev/null || date -d "$d + 1 day" +%Y%m%d)
  done
}

# ECMWF IFS ENS tropical-cyclone tracks as issued (CC BY 4.0), public mirror.
ECMWF_DIR="$RAW/ecmwf/ifs_enfo_tf"
for d in $(days); do
  for h in 00 06 12 18; do
    step=240; [[ "$h" == 06 || "$h" == 18 ]] && step=144
    fetch "https://storage.googleapis.com/ecmwf-open-data/$d/${h}z/ifs/0p25/enfo/${d}${h}0000-${step}h-enfo-tf.bufr" "$ECMWF_DIR"
  done
done
checksum "$ECMWF_DIR"

# Google DeepMind Weather Lab cyclone tracks (data older than 48 h is CC BY 4.0).
WL_BASE="https://deepmind.google.com/science/weatherlab/download/cyclones"
for model in FNV3P2 FNV3_LARGE_ENSEMBLE OPER; do
  for product in ensemble ensemble_mean; do
    dir="$RAW/weatherlab/$model/$product"
    for d in $(days); do
      for h in 00 06 12 18; do
        f="${model}_${d:0:4}_${d:4:2}_${d:6:2}T${h}_00_paired.csv"
        fetch "$WL_BASE/$model/$product/paired/csv/$f" "$dir"
      done
    done
    checksum "$dir"
  done
done

# IBTrACS v04r01 North Indian basin (verification labels only; never a forecast input).
fetch "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NI.list.v04r01.csv" "$RAW/ibtracs/v04r01"
checksum "$RAW/ibtracs/v04r01"

# OASIS CAP 1.2 XSD (vendored into schemas/cap/ by task 1.3).
fetch "https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.xsd" "$RAW/cap/1.2"
checksum "$RAW/cap/1.2"

# Geofabrik OSM extract for Andhra Pradesh (southern-zone, ~531 MB, ODbL).
if [[ "$WITH_OSM" == 1 ]]; then
  url="https://download.geofabrik.de/asia/india/southern-zone-latest.osm.pbf"
  # "latest" redirects to a dated file, e.g. southern-zone-260927.osm.pbf; use that date as the version.
  dated=$(curl -fsSI "$url" | awk -F': ' 'tolower($1)=="location"{print $2}' | tr -d '\r')
  yymmdd=$(basename "$dated" | sed -nE 's/.*-([0-9]{6})\.osm\.pbf/\1/p')
  if [[ -z "$yymmdd" ]]; then echo "FAIL could not resolve Geofabrik version"; exit 1; fi
  version="20${yymmdd:0:2}-${yymmdd:2:2}-${yymmdd:4:2}"
  dir="$RAW/geofabrik/southern-zone/$version"
  fetch "$url" "$dir"
  fetch "$url.md5" "$dir"
  (cd "$dir" && expected=$(awk '{print $1}' southern-zone-latest.osm.pbf.md5) \
    && actual=$(md5 -q southern-zone-latest.osm.pbf 2>/dev/null || md5sum southern-zone-latest.osm.pbf | awk '{print $1}') \
    && [[ "$expected" == "$actual" ]] && echo "MD5  ok ($version)" || echo "MD5  MISMATCH ($version)")
  checksum "$dir"
fi

echo "DONE $(date -u +%FT%TZ)"

# ---- Terrain and water for a bounding box (no sign-in). Set DEM_LAT and DEM_LON ranges as needed.
DEM_LATS="${DEM_LATS:-15 16 17}"
DEM_LONS="${DEM_LONS:-80 81 82}"
DEM_DIR="$RAW/copernicus_dem/glo30"
for lat in $DEM_LATS; do
  for lon in $DEM_LONS; do
    name=$(printf "Copernicus_DSM_COG_10_N%02d_00_E%03d_00_DEM" "$lat" "$lon")
    fetch "https://copernicus-dem-30m.s3.amazonaws.com/$name/$name.tif" "$DEM_DIR"
  done
done
checksum "$DEM_DIR"
# JRC Global Surface Water occurrence v1.4 (2021), 10x10 degree tile covering 80-90 E, 10-20 N.
fetch "https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/occurrence_80E_20Nv1_4_2021.tif" "$RAW/jrc_gsw/v1_4_2021"
checksum "$RAW/jrc_gsw/v1_4_2021"
echo "DONE terrain/water $(date -u +%FT%TZ)"
