#!/usr/bin/env bash
# Tam üretim hattı: ambalaj dekupesi → müzik/SFX → Remotion render → platform encode.
set -euo pipefail
cd "$(dirname "$0")/.."
CHROME="${REMOTION_CHROME:-}"
BX=(); [ -n "$CHROME" ] && BX=(--browser-executable="$CHROME")

python3 scripts/cutout.py sources/sek-protein-quark-165g_migros.jpg public
python3 scripts/audio.py src/timeline.json public/soundtrack_raw.wav
ffmpeg -hide_banner -loglevel error -y -i public/soundtrack_raw.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 public/soundtrack.wav
rm -f public/soundtrack_raw.wav

npx remotion render src/index.ts SekQuark out/_render.mp4 "${BX[@]}" --concurrency=4
npx remotion still src/index.ts Cover out/cover.png "${BX[@]}"

# Instagram/TikTok: H.264 High, yuv420p (TV range), BT.709, 30 fps, AAC 320k, faststart
ffmpeg -hide_banner -loglevel error -y -i out/_render.mp4 -i public/soundtrack.wav -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 17 -profile:v high -level 4.2 -pix_fmt yuv420p \
  -vf "scale=in_range=full:out_range=tv" -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -r 30 \
  -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart out/final_video.mp4
rm -f out/_render.mp4
echo "Hazır: out/final_video.mp4"
