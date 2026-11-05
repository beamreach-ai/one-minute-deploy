#!/usr/bin/env python3
# Build the review page for one episode: the picture (with the keyboard sounds
# baked in) plus every soundtrack as a separate stem, so the reviewer can
# switch music while the video keeps playing and balance music against keys.
# Usage: review.py <work dir> [title]  ->  <work>/review/index.html (+ media/)
import json, os, subprocess, sys

WORK = os.path.abspath(sys.argv[1]); TITLE = sys.argv[2] if len(sys.argv) > 2 else "1-Minute Deploy · ep.01 · 2048 → S3"
OUT = os.path.join(WORK, "review"); MEDIA = os.path.join(OUT, "media"); os.makedirs(MEDIA, exist_ok=True)
FF = "ffmpeg"
META = json.load(open(os.path.join(WORK, "out", "meta.json")))
TRACKS = json.load(open(os.path.join(WORK, "audio", "tracks.json")))
ABOUT = {
    "1_chiptune": ("Chiptune", "8-bit square lead, bouncy; matches the game"),
    "2_musicbox": ("Music box", "gentle waltz on a music box; calm and light"),
    "3_lofi": ("Lo-fi keys", "electric piano over a slow boom-bap beat; relaxed"),
    "4_synthpop": ("Synth-pop", "saw lead, four-on-the-floor in the demo; energetic"),
    "5_ukulele": ("Ukulele + whistle", "strummed ukulele with a whistled tune; cheerful"),
}
LABELS = {"hook": "Hook", "title": "Title", "term": "Clone", "nano": "Edit config", "deploy": "Deploy",
          "upload": "Upload", "live": "LIVE", "browser": "Browser", "game": "Gameplay", "outro": "Outro"}

def run(*a): subprocess.run([FF, "-y", "-loglevel", "error", *a], check=True)
run("-i", os.path.join(WORK, "out", "video.mp4"), "-i", os.path.join(WORK, "audio", "keys.wav"),
    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
    os.path.join(MEDIA, "video_keys.mp4"))
tracks = []
for tid, info in TRACKS.items():
    run("-i", os.path.join(WORK, "audio", tid + "_music.wav"), "-c:a", "aac", "-b:a", "160k", os.path.join(MEDIA, tid + ".m4a"))
    label, desc = ABOUT.get(tid, (tid, ""))
    tracks.append({"id": tid, "label": label, "desc": desc, "bpm": round(info["bpm"]), "src": "media/%s.m4a" % tid,
                   "reel": "../reels/%s_%s.mp4" % (META.get("slug", "ep01_2048_s3"), tid)})
marks = [{"id": k, "label": LABELS[k], "t": v} for k, v in META["marks"].items() if k in LABELS]
DATA = {"title": TITLE, "dur": META["dur"], "marks": marks, "tracks": tracks, "keys": len(META["keys"])}

HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reel review</title>
<style>
:root{--bg:#070b14;--panel:#0e1626;--raise:#142036;--line:#22304a;--tx:#cde3ff;--dim:#7e8ca3;--acc:#4fd1ff;--ok:#3ddc84;--warn:#ffc24a}
@media (prefers-color-scheme: light){:root{--bg:#f3f5f9;--panel:#fff;--raise:#eef2f8;--line:#d3dae6;--tx:#152033;--dim:#5a6a82;--acc:#0878a8;--ok:#0f7a45;--warn:#9a6200}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:20px 16px 40px;display:grid;grid-template-columns:minmax(0,auto) minmax(320px,1fr);gap:24px;align-items:start}
@media (max-width:820px){.wrap{grid-template-columns:1fr}}
h1{font-size:19px;margin:0 0 2px} h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);margin:0 0 10px;font-weight:600}
.sub{color:var(--dim);font-size:13px;margin:0 0 18px}
.stage{position:sticky;top:16px}
video{display:block;height:min(78vh,860px);aspect-ratio:9/16;max-width:100%;background:#000;border-radius:14px;border:1px solid var(--line);cursor:pointer}
.bar{display:flex;align-items:center;gap:10px;margin-top:10px}
button{font:inherit;color:var(--tx);background:var(--raise);border:1px solid var(--line);border-radius:9px;padding:7px 12px;cursor:pointer}
button:hover{border-color:var(--acc)} button.primary{background:var(--acc);border-color:var(--acc);color:#04121c;font-weight:600;min-width:84px}
.time{font:13px ui-monospace,Menlo,monospace;color:var(--dim);white-space:nowrap}
.seek{position:relative;flex:1;height:26px}
.seek input{position:absolute;inset:0;width:100%;margin:0;accent-color:var(--acc)}
.ticks{position:absolute;left:8px;right:8px;top:0;height:5px;pointer-events:none}
.ticks i{position:absolute;top:0;width:2px;height:5px;background:var(--warn);border-radius:1px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;max-width:calc(min(78vh,860px)*9/16)}
.chips button{padding:4px 9px;font-size:12.5px} .chips button.on{border-color:var(--acc);color:var(--acc)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:16px}
.track{display:flex;gap:12px;align-items:center;width:100%;text-align:left;margin-bottom:8px;padding:10px 12px}
.track:last-child{margin-bottom:0}
.track .n{font:600 13px ui-monospace,Menlo,monospace;color:var(--dim);width:18px}
.track b{display:block} .track span{color:var(--dim);font-size:13px}
.track.on{border-color:var(--acc);box-shadow:inset 3px 0 0 var(--acc)}
.track .pick{margin-left:auto;font-size:12px;color:var(--ok);visibility:hidden;white-space:nowrap} .track.picked .pick{visibility:visible}
.row{display:grid;grid-template-columns:86px 1fr 46px;gap:10px;align-items:center;margin-bottom:8px}
.row input{width:100%;accent-color:var(--acc)} .row output{font:13px ui-monospace,Menlo,monospace;color:var(--dim);text-align:right}
textarea{width:100%;min-height:92px;background:var(--raise);color:var(--tx);border:1px solid var(--line);border-radius:9px;padding:9px;font:inherit;resize:vertical}
.acts{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}
.hint{color:var(--dim);font-size:12.5px;margin:10px 0 0} kbd{font:12px ui-monospace,Menlo,monospace;border:1px solid var(--line);border-radius:5px;padding:0 5px;background:var(--raise)}
a{color:var(--acc)}
</style></head><body>
<div class="wrap">
  <div class="stage">
    <video id="v" playsinline preload="auto" src="media/video_keys.mp4"></video>
    <div class="bar">
      <button class="primary" id="play">Play</button>
      <div class="seek"><div class="ticks" id="ticks"></div><input id="seek" type="range" min="0" step="0.01" value="0" aria-label="Position"></div>
      <span class="time" id="time"></span>
    </div>
    <div class="chips" id="chips"></div>
  </div>
  <div>
    <h1 id="title"></h1>
    <p class="sub" id="sub"></p>
    <div class="card"><h2>Soundtrack</h2><div id="tracks"></div>
      <p class="hint">Switch while the video plays; the music stays in sync. The keyboard sounds are part of the video.</p></div>
    <div class="card"><h2>Balance</h2>
      <div class="row"><label for="mv">Music</label><input id="mv" type="range" min="0" max="100" value="100"><output id="mvo"></output></div>
      <div class="row"><label for="kv">Keyboard</label><input id="kv" type="range" min="0" max="100" value="100"><output id="kvo"></output></div>
      <p class="hint">100 / 100 is the balance in the exported reels.</p></div>
    <div class="card"><h2>Your review</h2>
      <textarea id="notes" placeholder="Notes: timing, text, music, anything to change"></textarea>
      <div class="acts"><button id="pick">Pick this soundtrack</button><button id="copy">Copy feedback</button><span class="hint" id="copied" style="margin:0"></span></div>
      <p class="hint">Copy feedback puts your pick, the two volumes and your notes on the clipboard, ready to paste into the chat.</p></div>
    <div class="card"><h2>Exported reels</h2><div id="reels"></div>
      <p class="hint"><kbd>Space</kbd> play / pause · <kbd>1</kbd>–<kbd>5</kbd> soundtrack · <kbd>0</kbd> no music · <kbd>←</kbd> <kbd>→</kbd> 2 s</p></div>
  </div>
</div>
<script>
const DATA = __DATA__;
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const store = { get(k, d){ try { const x = localStorage.getItem('omd.' + k); return x === null ? d : JSON.parse(x); } catch(e){ return d; } },
                set(k, x){ try { localStorage.setItem('omd.' + k, JSON.stringify(x)); } catch(e){} } };
const v = $('v'), seek = $('seek');
const QUIET = 0.001;   // -60 dB, not 0: Chrome parks a fully silent stem on a different clock, so it would come in ~0.2 s late
const audios = {}; DATA.tracks.forEach(t => { const a = new Audio(t.src); a.preload = 'auto'; a.volume = QUIET; audios[t.id] = a; });
let sel = store.get('sel', DATA.tracks[0].id), picked = store.get('pick', null);
if (sel !== 'none' && !audios[sel]) sel = DATA.tracks[0].id;

$('title').textContent = DATA.title;
$('sub').textContent = DATA.dur.toFixed(1) + ' s · ' + DATA.keys + ' keystroke sounds · ' + DATA.tracks.length + ' soundtracks';
seek.max = DATA.dur;
$('ticks').innerHTML = DATA.marks.filter(m => m.t > 0).map(m => '<i style="left:' + (m.t / DATA.dur * 100).toFixed(2) + '%" title="' + esc(m.label) + '"></i>').join('');
$('chips').innerHTML = DATA.marks.map((m, i) => '<button data-i="' + i + '">' + esc(m.label) + ' <span style="opacity:.6">' + m.t.toFixed(1) + '</span></button>').join('');
$('tracks').innerHTML = DATA.tracks.map((t, i) => '<button class="track" data-id="' + esc(t.id) + '"><span class="n">' + (i + 1) + '</span><div><b>' + esc(t.label) +
  '</b><span>' + esc(t.desc) + ' · ' + esc(t.bpm) + ' bpm</span></div><span class="pick">✓ picked</span></button>').join('') +
  '<button class="track" data-id="none"><span class="n">0</span><div><b>No music</b><span>keyboard sounds only</span></div><span class="pick"></span></button>';
$('reels').innerHTML = DATA.tracks.map(t => '<div><a href="' + esc(t.reel) + '">' + esc(t.reel.split('/').pop()) + '</a></div>').join('');

function applyAudio(){
  const mv = $('mv').value / 100; v.volume = $('kv').value / 100;
  for (const id in audios) audios[id].volume = id === sel ? Math.max(mv, QUIET) : QUIET;
  $('mvo').textContent = $('mv').value; $('kvo').textContent = $('kv').value;
  document.querySelectorAll('.track').forEach(b => { b.classList.toggle('on', b.dataset.id === sel); b.classList.toggle('picked', b.dataset.id === picked); });
}
// Keep every stem on the video clock. Small drift is closed by nudging the
// stem's speed (a hard seek stalls the stem ~0.2 s and would trigger the next
// one); only a real jump seeks.
function sync(force){
  for (const id in audios){ const a = audios[id], d = a.currentTime - v.currentTime;
    if (force || Math.abs(d) > 0.4){ a.currentTime = v.currentTime; a.playbackRate = 1; }
    else a.playbackRate = Math.abs(d) < 0.02 ? 1 : 1 - Math.max(-0.1, Math.min(0.1, d * 0.6)); }
}
function play(){ if (v.ended || v.currentTime >= DATA.dur - 0.05) v.currentTime = 0; sync(true); v.play(); for (const id in audios) audios[id].play().catch(() => {}); }
function pause(){ v.pause(); for (const id in audios) audios[id].pause(); }
function toggle(){ v.paused ? play() : pause(); }
function select(id){ sel = id; store.set('sel', id); applyAudio(); }
function jump(t){ v.currentTime = Math.max(0, Math.min(DATA.dur - 0.05, t)); sync(true); paint(); }
function paint(){
  const t = v.currentTime; if (document.activeElement !== seek) seek.value = t;
  let cur = 0; DATA.marks.forEach((m, i) => { if (t >= m.t - 0.02) cur = i; });
  $('time').textContent = t.toFixed(1) + ' / ' + DATA.dur.toFixed(1) + ' s';
  document.querySelectorAll('#chips button').forEach((b, i) => b.classList.toggle('on', i === cur));
  $('play').textContent = v.paused ? 'Play' : 'Pause';
}
$('play').onclick = toggle; v.onclick = toggle;
seek.oninput = () => jump(+seek.value);
$('chips').onclick = e => { const b = e.target.closest('button'); if (b) jump(DATA.marks[+b.dataset.i].t); };
$('tracks').onclick = e => { const b = e.target.closest('.track'); if (b) select(b.dataset.id); };
$('mv').oninput = () => { store.set('mv', $('mv').value); applyAudio(); };
$('kv').oninput = () => { store.set('kv', $('kv').value); applyAudio(); };
$('notes').oninput = () => store.set('notes', $('notes').value);
$('pick').onclick = () => { picked = sel; store.set('pick', picked); applyAudio(); };
$('copy').onclick = () => {
  const name = id => id === 'none' ? 'no music' : id ? (DATA.tracks.find(t => t.id === id) || {}).label + ' (' + id + ')' : 'none yet';
  const text = DATA.title + ' — review\nsoundtrack pick: ' + name(picked) + '\nmusic ' + $('mv').value + ' / keyboard ' + $('kv').value + '\nnotes: ' + ($('notes').value.trim() || '(none)');
  const done = ok => { $('copied').textContent = ok ? 'Copied.' : 'Copy failed: select the text below.'; if (!ok) { $('notes').value = text; } };
  (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(() => done(true), () => done(false));
};
v.addEventListener('timeupdate', paint); v.addEventListener('play', paint); v.addEventListener('pause', paint);
v.addEventListener('seeked', () => sync(true));
v.addEventListener('waiting', () => { for (const id in audios) audios[id].pause(); });
v.addEventListener('playing', () => { sync(true); for (const id in audios) audios[id].play().catch(() => {}); });
v.addEventListener('ended', () => { for (const id in audios) audios[id].pause(); paint(); });
setInterval(() => { if (!v.paused) sync(false); }, 100);
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'TEXTAREA' || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.code === 'Space'){ e.preventDefault(); toggle(); }
  else if (e.key === 'ArrowLeft'){ e.preventDefault(); jump(v.currentTime - 2); }
  else if (e.key === 'ArrowRight'){ e.preventDefault(); jump(v.currentTime + 2); }
  else if (e.key === '0') select('none');
  else if (/^[1-9]$/.test(e.key) && DATA.tracks[+e.key - 1]) select(DATA.tracks[+e.key - 1].id);
});
$('mv').value = store.get('mv', 100); $('kv').value = store.get('kv', 100); $('notes').value = store.get('notes', '');
applyAudio(); paint();
</script></body></html>
"""
open(os.path.join(OUT, "index.html"), "w").write(HTML.replace("__DATA__", json.dumps(DATA)))
print("review page:", os.path.join(OUT, "index.html"))
