#!/usr/bin/env bash
# Publishes the generated web data (apps/web/public/tiles and runs, git-ignored on main) as a
# single-commit orphan branch "web-data", replacing the previous one. Cloud Shell's deploy
# script (infra/cloudshell/02_deploy_web.sh) unpacks it into apps/web/public before building.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
src=apps/web/public
test -d "$src/tiles" && test -d "$src/runs" || { echo "no $src/tiles or $src/runs; run make tiles first" >&2; exit 1; }
runs=$(ls "$src/runs" | tr '\n' ' ')
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
index="$tmpdir/index"
export GIT_INDEX_FILE="$index"
git --work-tree="$src" add --force -- tiles runs
tree=$(git write-tree)
unset GIT_INDEX_FILE
commit=$(git commit-tree "$tree" -m "data: generated web tiles and run JSON ($runs)")
git push --force origin "$commit:refs/heads/web-data"
echo "web-data -> $commit ($(du -sh "$src/tiles" "$src/runs" | awk '{print $1}' | paste -sd+ -))"
