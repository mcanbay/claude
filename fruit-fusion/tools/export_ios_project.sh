#!/usr/bin/env bash
# Generates the Xcode project for Fruit Fusion (works on Linux and macOS; the .ipa itself needs Xcode).
#   TEAM_ID=XXXXXXXXXX BUNDLE_ID=com.yourcompany.fruitfusion tools/export_ios_project.sh [output dir]
# The team ID and bundle ID are injected into a temporary copy, so they never land in the repository.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${TEAM_ID:?Set TEAM_ID to your 10-character Apple Developer Team ID}"
: "${BUNDLE_ID:?Set BUNDLE_ID to the App ID registered at developer.apple.com}"
GODOT="${GODOT:-godot}"
OUT="$(mkdir -p "${1:-build/ios}" && cd "${1:-build/ios}" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
tar --exclude=.godot --exclude=build --exclude=store/screenshots -cf - . | tar -xf - -C "$WORK"
sed -i.bak -e "s/app_store_team_id=\"\"/app_store_team_id=\"$TEAM_ID\"/" \
  -e "s/com\.example\.fruitfusion/$BUNDLE_ID/" "$WORK/export_presets.cfg"
"$GODOT" --headless --path "$WORK" --import >/dev/null 2>&1 || true
"$GODOT" --headless --path "$WORK" --export-release "iOS" "$OUT/FruitFusion.xcodeproj"
echo "Xcode project written to $OUT/FruitFusion.xcodeproj"
