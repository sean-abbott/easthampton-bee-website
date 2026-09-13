#!/usr/bin/env bash
# Copies the Plant Safari widget's runtime files from the base
# iNat-place-safari project into this site's static/plant-safari/, so it's
# servable at /plant-safari/safari.{css,js} and /plant-safari/inat-safari.json.
#
# Re-run this after re-generating inat-safari.json in the base repo (monthly,
# per its own README) to keep this site's copy current.
#
# Usage: scripts/sync-plant-safari.sh [path-to-iNat-place-safari]
set -euo pipefail

SOURCE_REPO="${1:-$HOME/projects/pws/iNat-place-safari}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO_ROOT/static/plant-safari"

mkdir -p "$DEST"
cp "$SOURCE_REPO/safari.js" "$SOURCE_REPO/safari.css" "$SOURCE_REPO/inat-safari.json" "$DEST/"

echo "Synced Plant Safari assets from $SOURCE_REPO into $DEST"
