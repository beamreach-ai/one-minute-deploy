#!/bin/bash
# Build one episode from its capture: picture -> soundtracks -> five muxed
# reels at -14 LUFS -> review page.   Usage: build.sh <work dir>
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; W="$(cd "$1" && pwd)"; PY="${PY:-python3}"
"$PY" "$HERE/render.py" "$W"
"$PY" "$HERE/music.py" "$W"
SLUG=$("$PY" -c "import json,sys;print(json.load(open(sys.argv[1]))['slug'])" "$W/out/meta.json")
mkdir -p "$W/reels"; rm -f "$W/reels/"*.mp4
for stem in "$W"/audio/*_music.wav; do
  t=$(basename "$stem" _music.wav)
  I=$(ffmpeg -hide_banner -nostats -i "$W/audio/$t.wav" -af ebur128 -f null - 2>&1 | grep -E "^ +I:" | tail -1 | awk '{print $2}')
  G=$("$PY" -c "print(round(-14.0-($I),2))")
  ffmpeg -y -loglevel error -i "$W/out/video.mp4" -i "$W/audio/$t.wav" -map 0:v -map 1:a -c:v copy \
    -af "volume=${G}dB,alimiter=limit=0.89:level=disabled" -c:a aac -b:a 192k -ar 44100 -movflags +faststart -shortest \
    "$W/reels/${SLUG}_$t.mp4"
  echo "reel ${SLUG}_$t.mp4  (gain ${G} dB)"
done
"$PY" "$HERE/review.py" "$W"
