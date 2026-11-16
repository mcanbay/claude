#!/usr/bin/env bash
# Renders App Store screenshots (TR + EN) from the real game under a virtual display.
# Needs: godot 4.7.1, xvfb-run, Mesa software GL. Output: store/screenshots/<locale>/<size>/*.png
set -euo pipefail
cd "$(dirname "$0")/.."
GODOT="${GODOT:-godot}"
# name  width height safe-top safe-bottom (insets in 720-wide canvas units)
SIZES=("1320x2868 1320 2868 101 56" "1206x2622 1206 2622 106 61")
for entry in "${SIZES[@]}"; do
  read -r name w h top bottom <<<"$entry"
  for pair in "tr tr" "en en-US"; do
    read -r lang dir <<<"$pair"
    out="$PWD/store/screenshots/$dir/$name"
    mkdir -p "$out"
    xvfb-run -a -s "-screen 0 ${w}x${h}x24" "$GODOT" --path . --rendering-driver opengl3 \
      --resolution "${w}x${h}" --fixed-fps 60 --audio-driver Dummy res://tools/screenshot_driver.tscn \
      -- --lang="$lang" --out="$out" --safe-top="$top" --safe-bottom="$bottom" 2>&1 | grep -E "saved|ERROR|SCRIPT" || true
  done
done
