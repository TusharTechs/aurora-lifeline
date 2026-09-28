#!/usr/bin/env bash
# Builds the static site and deploys it to Firebase Hosting. Run in Cloud Shell from the repo:
#   cd ~/aurora-lifeline && git pull && bash infra/cloudshell/02_deploy_web.sh
# Needs a .env with the browser Maps key and Map ID. If it is missing, either upload your local
# .env with Cloud Shell's "Upload" menu (it lands in ~ and is moved here) or answer the prompts.
set -euo pipefail
PROJECT="${PROJECT:-aurora-lifeline}"
cd "$(git rev-parse --show-toplevel)"
git pull --ff-only

echo "== Generated map data (web-data branch)"
git fetch --depth 1 origin web-data
rm -rf apps/web/public/tiles apps/web/public/runs
git archive --format=tar FETCH_HEAD | tar -xf - -C apps/web/public
ls apps/web/public/runs

echo "== .env"
[ ! -f .env ] && [ -f "$HOME/.env" ] && mv "$HOME/.env" .env && echo "moved uploaded ~/.env"
touch .env && chmod 600 .env
setvar() {  # setvar NAME default secret?
  grep -qE "^$1=.+" .env && return
  local value="$2"
  if [ -z "$value" ]; then
    if [ "${3:-}" = secret ]; then read -rsp "$1 (input hidden): " value; echo
    else read -rp "$1: " value; fi
  fi
  sed -i "/^$1=/d" .env && echo "$1=$value" >> .env
}
setvar NEXT_PUBLIC_MAPS_API_KEY "" secret
setvar NEXT_PUBLIC_MAPS_MAP_ID ""
setvar NEXT_PUBLIC_FIREBASE_PROJECT_ID "$PROJECT"
setvar NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN "$PROJECT.firebaseapp.com"
setvar NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET "$PROJECT.firebasestorage.app"

echo "== Node 22 and pnpm"
if ! node -v 2>/dev/null | grep -qE '^v(2[2-9]|[3-9][0-9])\.'; then
  export NVM_DIR="${NVM_DIR:-/usr/local/nvm}"
  # shellcheck disable=SC1091
  . "$NVM_DIR/nvm.sh" && nvm install 22 >/dev/null && nvm use 22 >/dev/null
fi
command -v pnpm >/dev/null && pnpm -v | grep -q '^11\.' || npm install -g --silent pnpm@11.25.0
echo "node $(node -v), pnpm $(pnpm -v)"

echo "== Build"
pnpm install --frozen-lockfile
pnpm --dir apps/web build
du -sh apps/web/out

echo "== Deploy to Firebase Hosting"
if ! pnpm exec firebase projects:list >/dev/null 2>&1; then
  pnpm exec firebase login --no-localhost
fi
pnpm exec firebase deploy --only hosting --project "$PROJECT" --non-interactive

echo
echo "Live: https://$PROJECT.web.app"
echo "If the map is blank: Credentials > your Maps browser key > Website restrictions must list"
echo "  https://$PROJECT.web.app/*  and  https://$PROJECT.firebaseapp.com/*"
