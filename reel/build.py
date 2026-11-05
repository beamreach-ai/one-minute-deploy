#!/usr/bin/env python3
"""Build one episode's reel from its capture: picture -> soundtrack -> mux.

The soundtrack is picked at random per reel, from a shuffled bag so that five
consecutive episodes get five different tracks (stable across rebuilds).
Pass --track <name> to override.

Usage: build.py <episode dir> <work dir> [--track 3_lofi]
  -> <work>/reels/<slug>.mp4 (+ <work>/out/meta.json, check_*.png, sheet.png)
"""
import json, os, random, re, runpy, subprocess, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TRACKS = ["1_chiptune", "2_musicbox", "3_lofi", "4_synthpop", "5_ukulele"]
def pick(num):
    bag = TRACKS[:]; random.Random(20261105 + (num - 1) // 5).shuffle(bag); return bag[(num - 1) % 5]

ep_dir = os.path.abspath(sys.argv[1]); work = os.path.abspath(sys.argv[2])
EP = runpy.run_path(os.path.join(ep_dir, "episode.py"))["EP"]
track = sys.argv[sys.argv.index("--track") + 1] if "--track" in sys.argv else pick(EP["num"])
py = sys.executable
subprocess.run([py, os.path.join(HERE, "render.py"), ep_dir, work], check=True)
subprocess.run([py, os.path.join(HERE, "music.py"), work, track], check=True)
wav = os.path.join(work, "audio", track + ".wav")
log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav, "-af", "ebur128", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
gain = round(-14.0 - float(re.findall(r"^\s+I:\s+(-?[\d.]+) LUFS", log, re.M)[-1]), 2)      # every reel at -14 LUFS
os.makedirs(os.path.join(work, "reels"), exist_ok=True)
for f in os.listdir(os.path.join(work, "reels")):
    if f.endswith(".mp4"): os.remove(os.path.join(work, "reels", f))
out = os.path.join(work, "reels", EP["slug"] + ".mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(work, "out", "video.mp4"), "-i", wav,
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "volume=%sdB,alimiter=limit=0.89:level=disabled" % gain,
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", "-shortest", out], check=True)
mp = os.path.join(work, "out", "meta.json"); meta = json.load(open(mp)); meta["track"] = track
json.dump(meta, open(mp, "w"))
# contact sheet of the check frames, for a quick visual review
names = [n for n in ["hook", "title"] + ["step%d" % i for i in range(1, 9)] + ["edit", "live", "url", "demo", "outro1"]
         if os.path.exists(os.path.join(work, "out", "check_%s.png" % n))]
ims = [Image.open(os.path.join(work, "out", "check_%s.png" % n)).resize((360, 640), Image.LANCZOS) for n in names]
cols = 6; rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 370 - 10, rows * 650 - 10), (60, 60, 60))
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 370, (i // cols) * 650))
sheet.save(os.path.join(work, "out", "sheet.png"))
print("reel: %s  (%.1f s, track %s, gain %s dB)   sheet: %s" % (out, meta["dur"], track, gain, os.path.join(work, "out", "sheet.png")))
