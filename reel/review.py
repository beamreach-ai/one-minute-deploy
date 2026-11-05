#!/usr/bin/env python3
"""Build one review page for every built episode under a data root.

Scans <root>/*/out/meta.json (written by build.py), and writes
<root>/review/index.html: an episode list, a player with section jump buttons,
and an approve / needs-changes verdict with notes per reel. "Copy feedback"
puts every verdict and note on the clipboard.

Usage: review.py <data root>
"""
import glob, json, os, sys

ROOT = os.path.abspath(sys.argv[1]); OUT = os.path.join(ROOT, "review"); os.makedirs(OUT, exist_ok=True)
TRACK_NAMES = {"1_chiptune": "Chiptune", "2_musicbox": "Music box", "3_lofi": "Lo-fi keys",
               "4_synthpop": "Synth-pop", "5_ukulele": "Ukulele + whistle"}
def human(sec): return "%d s" % sec if sec < 90 else "%d min %02d s" % (sec // 60, sec % 60)

eps = []
for mp in sorted(glob.glob(os.path.join(ROOT, "*", "out", "meta.json"))):
    m = json.load(open(mp)); epdir = os.path.basename(os.path.dirname(os.path.dirname(mp)))
    reel = os.path.join(ROOT, epdir, "reels", m["slug"] + ".mp4")
    if not os.path.exists(reel): continue
    marks = []; steps = m.get("steps", [])
    for k, t in m["marks"].items():
        if k == "term": marks.append({"label": "Step 1", "tip": steps[0] if steps else "", "t": t})
        elif k.startswith("step"): n = int(k[4:]); marks.append({"label": "Step %d" % n, "tip": steps[n - 1] if len(steps) >= n else "", "t": t})
        elif k in ("hook", "title", "live", "browser", "outro"): marks.append({"label": {"live": "LIVE"}.get(k, k.capitalize()), "tip": "", "t": t})
        elif k == "game": marks.append({"label": "Demo", "tip": "", "t": t})
    eps.append({"id": m["slug"], "num": m["num"], "app": m["app"], "target": m["target"], "how": m["how"], "dur": m["dur"],
                "track": TRACK_NAMES.get(m.get("track"), m.get("track", "")), "real": human(m["real_total"]),
                "term": m.get("term_seconds"), "demo": m.get("demo_seconds"), "note": m.get("note", ""),
                "src": "../%s/reels/%s.mp4" % (epdir, m["slug"]), "marks": sorted(marks, key=lambda x: x["t"])})
eps.sort(key=lambda e: e["num"])

HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>1-Minute Deploy review</title>
<style>
:root{--bg:#070b14;--panel:#0e1626;--raise:#142036;--line:#22304a;--tx:#cde3ff;--dim:#7e8ca3;--acc:#4fd1ff;--ok:#3ddc84;--warn:#ffc24a;--bad:#ff5c6c}
@media (prefers-color-scheme: light){:root{--bg:#f3f5f9;--panel:#fff;--raise:#eef2f8;--line:#d3dae6;--tx:#152033;--dim:#5a6a82;--acc:#0878a8;--ok:#0f7a45;--warn:#9a6200;--bad:#c22a3a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.wrap{max-width:1220px;margin:0 auto;padding:20px 16px 40px;display:grid;grid-template-columns:minmax(0,auto) minmax(330px,1fr);gap:24px;align-items:start}
@media (max-width:820px){.wrap{grid-template-columns:1fr}}
h1{font-size:19px;margin:0 0 2px} h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);margin:0 0 10px;font-weight:600}
.sub{color:var(--dim);font-size:13px;margin:0 0 16px}
.stage{position:sticky;top:16px}
video{display:block;height:min(76vh,840px);aspect-ratio:9/16;max-width:100%;background:#000;border-radius:14px;border:1px solid var(--line);cursor:pointer}
.bar{display:flex;align-items:center;gap:10px;margin-top:10px}
button{font:inherit;color:var(--tx);background:var(--raise);border:1px solid var(--line);border-radius:9px;padding:7px 12px;cursor:pointer}
button:hover{border-color:var(--acc)} button.primary{background:var(--acc);border-color:var(--acc);color:#04121c;font-weight:600;min-width:84px}
.time{font:13px ui-monospace,Menlo,monospace;color:var(--dim);white-space:nowrap}
.seek{position:relative;flex:1;height:26px}
.seek input{position:absolute;inset:0;width:100%;margin:0;accent-color:var(--acc)}
.ticks{position:absolute;left:8px;right:8px;top:0;height:5px;pointer-events:none}
.ticks i{position:absolute;top:0;width:2px;height:5px;background:var(--warn);border-radius:1px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;max-width:calc(min(76vh,840px)*9/16)}
.chips button{padding:4px 9px;font-size:12.5px} .chips button.on{border-color:var(--acc);color:var(--acc)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:16px}
.ep{display:flex;gap:12px;align-items:center;width:100%;text-align:left;margin-bottom:8px;padding:9px 12px}
.ep:last-child{margin-bottom:0}
.ep .n{font:600 13px ui-monospace,Menlo,monospace;color:var(--dim);width:22px}
.ep b{display:block} .ep span.m{color:var(--dim);font-size:13px}
.ep.on{border-color:var(--acc);box-shadow:inset 3px 0 0 var(--acc)}
.ep .st{margin-left:auto;font-size:12px;white-space:nowrap;font-weight:600}
.st.ok{color:var(--ok)} .st.fix{color:var(--bad)} .st.none{color:var(--dim);font-weight:400}
.facts{display:grid;grid-template-columns:auto 1fr;gap:3px 14px;font-size:13.5px;margin:0 0 12px} .facts dt{color:var(--dim)} .facts dd{margin:0}
.verdict{display:flex;gap:8px;margin-bottom:10px} .verdict button{flex:1}
.verdict button.on.ok{border-color:var(--ok);color:var(--ok);font-weight:600} .verdict button.on.fix{border-color:var(--bad);color:var(--bad);font-weight:600}
textarea{width:100%;min-height:84px;background:var(--raise);color:var(--tx);border:1px solid var(--line);border-radius:9px;padding:9px;font:inherit;resize:vertical}
.acts{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}
.hint{color:var(--dim);font-size:12.5px;margin:10px 0 0} kbd{font:12px ui-monospace,Menlo,monospace;border:1px solid var(--line);border-radius:5px;padding:0 5px;background:var(--raise)}
.note{color:var(--warn);font-size:13px;margin:0 0 10px}
</style></head><body>
<div class="wrap">
  <div class="stage">
    <video id="v" playsinline preload="metadata"></video>
    <div class="bar">
      <button class="primary" id="play">Play</button>
      <div class="seek"><div class="ticks" id="ticks"></div><input id="seek" type="range" min="0" step="0.01" value="0" aria-label="Position"></div>
      <span class="time" id="time"></span>
    </div>
    <div class="chips" id="chips"></div>
  </div>
  <div>
    <h1>1-Minute Deploy · review</h1>
    <p class="sub" id="sub"></p>
    <div class="card"><h2 id="cur"></h2>
      <dl class="facts" id="facts"></dl><p class="note" id="note"></p>
      <div class="verdict"><button id="ok" class="ok">Approve</button><button id="fix" class="fix">Needs changes</button></div>
      <textarea id="notes" placeholder="Notes for this reel: timing, text, music, anything to change"></textarea>
      <div class="acts"><button id="copy">Copy all feedback</button><span class="hint" id="copied" style="margin:0"></span></div>
      <p class="hint">Copy all feedback puts every reel's verdict and notes on the clipboard, ready to paste into the chat.</p></div>
    <div class="card"><h2>Reels</h2><div id="eps"></div>
      <p class="hint"><kbd>Space</kbd> play / pause · <kbd>←</kbd> <kbd>→</kbd> 2 s · <kbd>↑</kbd> <kbd>↓</kbd> previous / next reel · <kbd>A</kbd> approve · <kbd>N</kbd> needs changes</p></div>
  </div>
</div>
<script>
const EPS = __DATA__;
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const store = { get(k, d){ try { const x = localStorage.getItem('omd2.' + k); return x === null ? d : JSON.parse(x); } catch(e){ return d; } },
                set(k, x){ try { localStorage.setItem('omd2.' + k, JSON.stringify(x)); } catch(e){} } };
const v = $('v'), seek = $('seek');
let state = store.get('state', {});            // id -> {verdict, notes}
let cur = Math.max(0, EPS.findIndex(e => e.id === store.get('cur', null)));
const st = id => state[id] || (state[id] = {verdict: '', notes: ''});
const total = EPS.reduce((a, e) => a + e.dur, 0);

function drawList(){
  $('eps').innerHTML = EPS.map((e, i) => { const s = st(e.id);
    return '<button class="ep' + (i === cur ? ' on' : '') + '" data-i="' + i + '"><span class="n">' + String(e.num).padStart(2, '0') + '</span><div><b>' + esc(e.app) + ' → ' + esc(e.target) +
      '</b><span class="m">' + esc(e.how) + ' · ' + e.dur.toFixed(1) + ' s · ' + esc(e.track) + '</span></div><span class="st ' + (s.verdict || 'none') + '">' +
      (s.verdict === 'ok' ? '✓ approved' : s.verdict === 'fix' ? '✕ needs changes' : 'not reviewed') + '</span></button>'; }).join('');
  const done = EPS.filter(e => st(e.id).verdict).length;
  $('sub').textContent = EPS.length + ' reels · ' + (total / 60).toFixed(1) + ' min in total · ' + done + ' reviewed';
}
function load(i, autoplay){
  cur = i; const e = EPS[i]; store.set('cur', e.id);
  v.src = e.src; v.load(); seek.max = e.dur; seek.value = 0;
  $('cur').textContent = 'ep.' + String(e.num).padStart(2, '0') + ' · ' + e.app + ' → ' + e.target;
  $('facts').innerHTML = [['How', e.how], ['Length', e.dur.toFixed(1) + ' s (terminal ' + e.term + ' s, demo ' + e.demo + ' s)'],
    ['Real deploy time', e.real], ['Soundtrack', e.track]].map(r => '<dt>' + esc(r[0]) + '</dt><dd>' + esc(r[1]) + '</dd>').join('');
  $('note').textContent = e.note || ''; $('note').style.display = e.note ? '' : 'none';
  $('ticks').innerHTML = e.marks.filter(m => m.t > 0).map(m => '<i style="left:' + (m.t / e.dur * 100).toFixed(2) + '%"></i>').join('');
  $('chips').innerHTML = e.marks.map((m, k) => '<button data-k="' + k + '" title="' + esc(m.tip) + '">' + esc(m.label) + '</button>').join('');
  $('notes').value = st(e.id).notes; drawVerdict(); drawList(); paint();
  if (autoplay) v.play().catch(() => {});
}
function drawVerdict(){ const s = st(EPS[cur].id); $('ok').classList.toggle('on', s.verdict === 'ok'); $('fix').classList.toggle('on', s.verdict === 'fix'); }
function verdict(x){ const s = st(EPS[cur].id); s.verdict = s.verdict === x ? '' : x; store.set('state', state); drawVerdict(); drawList(); }
function toggle(){ if (v.paused){ if (v.ended) v.currentTime = 0; v.play().catch(() => {}); } else v.pause(); }
function jump(t){ v.currentTime = Math.max(0, Math.min(EPS[cur].dur - 0.05, t)); paint(); }
function paint(){
  const e = EPS[cur], t = v.currentTime || 0; if (document.activeElement !== seek) seek.value = t;
  let k = 0; e.marks.forEach((m, i) => { if (t >= m.t - 0.02) k = i; });
  $('time').textContent = t.toFixed(1) + ' / ' + e.dur.toFixed(1) + ' s';
  document.querySelectorAll('#chips button').forEach((b, i) => b.classList.toggle('on', i === k));
  $('play').textContent = v.paused ? 'Play' : 'Pause';
}
$('play').onclick = toggle; v.onclick = toggle;
seek.oninput = () => jump(+seek.value);
$('chips').onclick = ev => { const b = ev.target.closest('button'); if (b) jump(EPS[cur].marks[+b.dataset.k].t); };
$('eps').onclick = ev => { const b = ev.target.closest('.ep'); if (b) load(+b.dataset.i, true); };
$('ok').onclick = () => verdict('ok'); $('fix').onclick = () => verdict('fix');
$('notes').oninput = () => { st(EPS[cur].id).notes = $('notes').value; store.set('state', state); };
$('copy').onclick = () => {
  const text = '1-Minute Deploy review\n' + EPS.map(e => { const s = st(e.id);
    return 'ep.' + String(e.num).padStart(2, '0') + ' ' + e.app + ' → ' + e.target + ': ' + (s.verdict === 'ok' ? 'APPROVED' : s.verdict === 'fix' ? 'NEEDS CHANGES' : 'not reviewed') +
      (s.notes.trim() ? '\n   ' + s.notes.trim().replace(/\n/g, '\n   ') : ''); }).join('\n');
  const done = ok => { $('copied').textContent = ok ? 'Copied.' : 'Copy failed: the text is in the notes box, select and copy it.'; if (!ok) $('notes').value = text; };
  (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(() => done(true), () => done(false));
};
['timeupdate', 'play', 'pause', 'ended', 'seeked'].forEach(n => v.addEventListener(n, paint));
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'TEXTAREA' || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.code === 'Space'){ e.preventDefault(); toggle(); }
  else if (e.key === 'ArrowLeft'){ e.preventDefault(); jump(v.currentTime - 2); }
  else if (e.key === 'ArrowRight'){ e.preventDefault(); jump(v.currentTime + 2); }
  else if (e.key === 'ArrowDown' && cur < EPS.length - 1){ e.preventDefault(); load(cur + 1, true); }
  else if (e.key === 'ArrowUp' && cur > 0){ e.preventDefault(); load(cur - 1, true); }
  else if (e.key === 'a' || e.key === 'A') verdict('ok');
  else if (e.key === 'n' || e.key === 'N') verdict('fix');
});
load(cur, false);
</script></body></html>
"""
open(os.path.join(OUT, "index.html"), "w").write(HTML.replace("__DATA__", json.dumps(eps)))
print("review page: %s  (%d reels)" % (os.path.join(OUT, "index.html"), len(eps)))
