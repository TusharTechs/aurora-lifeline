#!/usr/bin/env bash
# Checks the system tools AURORA Lifeline needs. Fails with a clear message if any is missing.
# GDAL and ecCodes come bundled in the rasterio/pyogrio and eccodeslib wheels, so no system
# install is needed; --post-install verifies them once `uv sync` has run.
set -uo pipefail

missing=0
ok()   { printf '  ok      %s\n' "$1"; }
bad()  { printf '  MISSING %s  -> %s\n' "$1" "$2"; missing=1; }
warn() { printf '  warn    %s  -> %s\n' "$1" "$2"; }

have() { command -v "$1" >/dev/null 2>&1; }

major() {  # major <version-string>
  echo "$1" | sed -nE 's/[^0-9]*([0-9]+).*/\1/p'
}

echo "System tools:"
have uv && ok "uv $(uv --version | awk '{print $2}')" || bad uv "https://docs.astral.sh/uv/ (brew install uv)"
have pnpm && ok "pnpm $(pnpm --version)" || bad pnpm "corepack enable pnpm (or brew install pnpm)"
if have node && [ "$(major "$(node --version)")" -ge 22 ]; then ok "node $(node --version)"; else bad "node>=22" "brew install node"; fi
have tippecanoe && ok "tippecanoe $(tippecanoe --version 2>&1 | awk '{print $2}')" || bad tippecanoe "brew install tippecanoe"
if have java && [ "$(major "$(java -version 2>&1 | head -1 | sed -E 's/.*version "?([0-9]+).*/\1/')")" -ge 21 ]; then
  ok "java $(java -version 2>&1 | head -1 | sed -E 's/.*version "?([^" ]+).*/\1/') (Firebase emulators)"
else bad "java>=21" "brew install openjdk@21"; fi
have gcloud && ok "gcloud $(gcloud --version 2>/dev/null | head -1 | awk '{print $4}')" || bad gcloud "https://cloud.google.com/sdk/docs/install"
have gitleaks && ok "gitleaks $(gitleaks version)" || bad gitleaks "brew install gitleaks"
have osmium && ok "osmium-tool (optional, build-time CLI only)" || warn "osmium-tool (optional)" "brew install osmium-tool"

if [ "${1:-}" = "--post-install" ]; then
  echo "Bundled libraries and project tools:"
  if uv run --no-sync python -c "import rasterio, pyogrio; print(rasterio.__gdal_version__)" >/dev/null 2>&1; then
    ok "GDAL $(uv run --no-sync python -c 'import rasterio; print(rasterio.__gdal_version__)') (rasterio/pyogrio wheels)"
  else bad GDAL "uv sync (rasterio and pyogrio wheels bundle GDAL)"; fi
  if uv run --no-sync python -c "import eccodes; eccodes.codes_get_api_version()" >/dev/null 2>&1; then
    ok "ecCodes $(uv run --no-sync python -c 'import eccodes; print(eccodes.codes_get_api_version())') (eccodeslib wheel)"
  else bad ecCodes "uv sync (eccodeslib wheel)"; fi
  if pnpm exec firebase --version >/dev/null 2>&1; then ok "firebase-tools $(pnpm exec firebase --version)"; else bad firebase-tools "pnpm install"; fi
  if ls "${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}" 2>/dev/null | grep -q chromium; then
    ok "Playwright Chromium"
  else warn "Playwright browsers" "pnpm --dir apps/web exec playwright install chromium (needed for the smoke test)"; fi
fi

if [ "$missing" -ne 0 ]; then
  echo "Some required tools are missing (see above). On macOS: brew install uv pnpm node tippecanoe openjdk@21 gitleaks"
  exit 1
fi
