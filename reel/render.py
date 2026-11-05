#!/usr/bin/env python3
"""1-Minute Deploy reel renderer.

Draws one episode from its spec (<episode dir>/episode.py, the EP dict) and its
real capture (<work>/cap, written by capture.py): white-on-black slides, a
deep-navy terminal that re-types the real commands and replays their real
output, then the recorded walkthrough in a browser frame.

The terminal section plays at TERM_SPEED; long waits are shortened and labelled
with the real elapsed time. Frames are piped straight to ffmpeg. The picture is
silent: <work>/out/meta.json carries section marks and every keystroke/click
for music.py.

Usage: render.py <episode dir> <work dir>  -> <work>/out/video.mp4, meta.json
"""
import bisect, json, os, random, re, runpy, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

EP_DIR = os.path.abspath(sys.argv[1]); WORK = os.path.abspath(sys.argv[2])
EP = runpy.run_path(os.path.join(EP_DIR, "episode.py"))["EP"]
CAP = os.path.join(WORK, "cap"); OUTD = os.path.join(WORK, "out"); os.makedirs(OUTD, exist_ok=True)
TERM_SPEED = 1.8                              # terminal section speed-up
W, H, FPS = 1080, 1920, 30
BLACK = (0, 0, 0)
TERM_BG = (11, 17, 32); CHROME = (14, 22, 38); BORDER = (34, 48, 74)
TXT = (205, 227, 255); DIM = (95, 114, 145); CYAN = (79, 209, 255)
GREEN = (61, 220, 132); AMBER = (255, 194, 74); RED = (255, 92, 108); SLIDE_TX = (242, 246, 255)
COLORS = {"txt": TXT, "dim": DIM, "cyan": CYAN, "green": GREEN, "amber": AMBER, "red": RED}
random.seed(EP["num"] * 97 + 5)

MONO = "/System/Library/Fonts/Menlo.ttc"; SANS = "/System/Library/Fonts/HelveticaNeue.ttc"
def ft(p, s, index=0): return ImageFont.truetype(p, s, index=index)
f_code = ft(MONO, 32); f_title = ft(MONO, 24); f_big = ft(MONO, 40, 1); f_cap = ft(MONO, 30)
f_slide = ft(SANS, 78); f_sub = ft(SANS, 36); f_kick = ft(MONO, 28); f_url = ft(MONO, 24); f_badge = ft(MONO, 28, 1)
def fit(text, path, size, maxw, index=0):       # largest font <= size that fits maxw
    while size > 30:
        f = ft(path, size, index)
        if f.getlength(text) <= maxw: return f
        size -= 4
    return ft(path, size, index)

# ---- real data from the capture ----
URL = open(os.path.join(CAP, "url.raw")).read().strip()
SECURE = URL.startswith("https://"); HOST = re.sub(r"^https?://", "", URL).rstrip("/")
TIMES = {l.split()[0]: float(l.split()[2].rstrip("s")) for l in open(os.path.join(CAP, "timings.txt")) if l.strip()}
REAL_TOTAL = int(round(sum(TIMES.values())))
def human(sec):
    sec = int(round(sec))
    return "%d seconds" % sec if sec < 90 else "%d min %02d s" % (sec // 60, sec % 60)
def clock(sec): sec = int(round(sec)); return "%d:%02d" % (sec // 60, sec % 60)

def mask(s): return re.sub(r"\b\d{12}\b", "************", s)        # never show an AWS account id
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")
def final_lines(path):                          # last state of each \r-updated line, ANSI stripped
    out = []
    for ln in ANSI.sub("", open(path, errors="replace").read()).split("\n"):
        seg = [s for s in ln.split("\r") if s.strip()]
        if seg: out.append(mask(seg[-1].rstrip().expandtabs(4)))
    return out
def last_per_counter(lines):                    # collapse progress counters to their final value
    seen = {}; order = []
    for l in lines:
        k = re.match(r"[^0-9]*", l).group(0).strip()
        if k not in seen: order.append(k)
        seen[k] = l
    return [seen[k] for k in order]
def step_output(step, name):
    p = os.path.join(CAP, name + ".raw")
    if step.get("hide_output") or not os.path.exists(p): return []
    if step.get("filter"):
        lines = [mask(m.group(0).rstrip()) for m in re.finditer(step["filter"], ANSI.sub("", open(p, errors="replace").read()))]
    else: lines = final_lines(p)
    if step.get("progress"): lines = last_per_counter(lines)
    if step.get("head"): lines = lines[:step["head"]]
    if step.get("tail"): lines = lines[-step["tail"]:]
    return lines[:step.get("max_lines", 40)]

WALK = json.load(open(os.path.join(CAP, "walk", "walk.json")))
# kept timeline: recorded time with the cut intervals removed
_cuts = sorted(WALK.get("cuts", []))
def kept(t):
    off = 0.0
    for a, b in _cuts:
        if t >= b: off += b - a
        elif t > a: return a - off
    return t - off
def in_cut(t): return any(a <= t < b for a, b in _cuts)
G_FR = [(kept(f["t"]), f["f"]) for f in WALK["frames"] if not in_cut(f["t"])]
G_T = [t for t, _ in G_FR]; G_END = max(G_T[-1], kept(WALK["dur"]))    # a still last frame holds to the end
G_EV = [(kept(e["t"]), e["kind"]) for e in WALK["events"] if not in_cut(e["t"])]

# ---- output: raw frames -> ffmpeg ----
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
    "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-c:v", "libx264",
    "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", os.path.join(OUTD, "video.mp4")],
    stdin=subprocess.PIPE)
idx = 0; clk = 0.0; SPEED = 1.0; KEYS = []; MARK = {}
def save(im, n=1, check=None):
    # n frames of screen time at normal speed; SPEED > 1 shortens the hold
    # (a state can fall between frames, its keystroke still lands on the clock)
    global idx, clk
    clk += n / SPEED
    m = int(clk + 1e-6) - idx
    if m > 0:
        b = im.tobytes()
        for _ in range(m): ff.stdin.write(b)
        idx += m
    if check: im.save(os.path.join(OUTD, "check_%s.png" % check))
def now(): return clk / FPS
def key(kind="key"): KEYS.append([round(now(), 3), kind])
def mark(name): MARK[name] = round(now(), 3)

# ---- terminal ----
WIN_X, WIN_W = 28, 1024; WIN_Y, WIN_H = 150, 1630; TITLE_H = 62; PADX, PADY = 20, 18
BODY_X = WIN_X + PADX; BODY_Y = WIN_Y + TITLE_H + PADY
BODY_W = WIN_W - 2 * PADX; BODY_H = WIN_H - TITLE_H - 2 * PADY
CW = f_code.getlength("M"); LINE_H = 44; MAXCH = int(BODY_W / CW); VIS = int(BODY_H / LINE_H) - 1
TERM_TITLE = EP.get("term_title", "aws: public-demo · us-west-1 — zsh")

def clip(s): return s if len(s) <= MAXCH else s[:MAXCH - 1] + "…"
def wrapc(s):
    out = []; cur = ""
    for w in s.split(" "):
        if cur and len(cur) + 1 + len(w) > MAXCH: out.append(cur); cur = "    " + w
        else: cur = (cur + " " + w) if cur else w
    return out + [cur]
def colorize(line, rules):
    for sub, c in rules:
        if sub in line: return COLORS[c]
    return TXT
def centered(d, y, text, font, fill):
    w = d.textlength(text, font=font); d.text(((W - w) // 2, y), text, font=font, fill=fill)

def term_base(caption=None):
    im = Image.new("RGB", (W, H), BLACK); d = ImageDraw.Draw(im)
    if caption: centered(d, 78, caption, f_cap, CYAN)
    d.rounded_rectangle((WIN_X, WIN_Y, WIN_X + WIN_W, WIN_Y + WIN_H), radius=18, fill=CHROME, outline=BORDER, width=2)
    cy = WIN_Y + TITLE_H // 2
    for k, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = WIN_X + 26 + k * 26; d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=c)
    tb = d.textbbox((0, 0), TERM_TITLE, font=f_title)
    d.text((WIN_X + (WIN_W - (tb[2] - tb[0])) // 2, cy - (tb[3] - tb[1]) // 2 - 2), TERM_TITLE, font=f_title, fill=DIM)
    d.line((WIN_X, WIN_Y + TITLE_H, WIN_X + WIN_W, WIN_Y + TITLE_H), fill=BORDER, width=1)
    d.rectangle((WIN_X + 2, WIN_Y + TITLE_H + 1, WIN_X + WIN_W - 2, WIN_Y + WIN_H - 2), fill=TERM_BG)
    return im, d

def draw_row(d, y, row):
    x = BODY_X
    for t, c in row:
        d.text((x, y), t, font=f_code, fill=c); x += CW * len(t)
    return x
def P(cmd): return [("❯ ", GREEN), (cmd, TXT)]       # prompt row
def R(t, c=TXT): return [(t, c)]

def draw_term(rows, caption=None, cursor=False, banner=None, blink=False, badge=None):
    im, d = term_base(caption)
    vis = VIS - ((len(banner[0]) + 4) if banner else 0) - (2 if badge else 0)
    shown = rows[-vis:]; x = BODY_X
    for i, row in enumerate(shown): x = draw_row(d, BODY_Y + i * LINE_H, row)
    if cursor and shown:
        y = BODY_Y + (len(shown) - 1) * LINE_H
        d.rectangle((x + 2, y + 2, x + CW - 1, y + LINE_H - 8), fill=TXT)
    if banner:
        lines, col = banner; bh = 62 + (len(lines) - 1) * 42 + 30
        by = WIN_Y + WIN_H - 24 - bh
        d.rounded_rectangle((BODY_X, by, BODY_X + BODY_W, by + bh), radius=12,
                            fill=(8, 24, 16) if col == GREEN else (30, 22, 8), outline=col, width=2)
        d.text((BODY_X + 24, by + 18), ("● " if blink else "  ") + lines[0], font=f_big, fill=col)
        for j, extra in enumerate(lines[1:]):
            d.text((BODY_X + 24, by + 18 + 56 + j * 42), extra, font=f_code, fill=TXT)
    if badge:
        bw = d.textlength(badge, font=f_badge) + 44; by = WIN_Y + WIN_H - 24 - 58
        d.rounded_rectangle((BODY_X + BODY_W - bw, by, BODY_X + BODY_W, by + 58), radius=29,
                            fill=(30, 22, 8), outline=AMBER, width=2)
        d.text((BODY_X + BODY_W - bw + 22, by + 12), badge, font=f_badge, fill=AMBER)
    return im

def type_cmd(history, cmd_lines, caption, pre=8, pause=24):
    # human typing with a key event per character, then a beat before Enter
    for l in cmd_lines: assert len(l) <= MAXCH - 2, "command line too long for the terminal (%d > %d): %s" % (len(l), MAXCH - 2, l)
    def rows_for(sub):
        parts = sub.split("\n")
        return list(history) + [P(parts[0])] + [R(p) for p in parts[1:]]
    full = "\n".join(cmd_lines)
    save(draw_term(rows_for(""), caption, cursor=True), pre)
    for n in range(1, len(full) + 1):
        ch = full[n - 1]
        key("space" if ch == " " else "enter" if ch == "\n" else "key")
        hold = random.choice([2, 2, 2, 2, 3, 3, 1]) + (1 if ch in " \n" else 0)
        save(draw_term(rows_for(full[:n]), caption, cursor=True), hold)
    on = draw_term(rows_for(full), caption, cursor=True); off = draw_term(rows_for(full), caption)
    for k in range(pause // 6): save(on if k % 2 == 0 else off, 6)
    key("enter"); rows = rows_for(full)
    save(draw_term(rows, caption), 3)
    return rows

def out_rows(lines, rules, wrap):
    out = []
    for l in lines:
        c = colorize(l, rules); out += [R(p, c) for p in (wrapc(l) if wrap else [clip(l)])]
    return out

def reveal(history, lines, rules, frames, caption, wrap=False, check=None):
    out = out_rows(lines, rules, wrap); N = len(out)
    if not N: return list(history)
    for fr in range(frames):
        shown = min(N, max(1, round((fr + 1) / frames * N)))
        save(draw_term(list(history) + out[:shown], caption), check=check if fr == frames - 1 else None)
    return list(history) + out

def waited(history, lines, rules, frames, caption, real, wrap=False, check=None):
    # a long real wait, compressed: output trickles in under a real-time counter,
    # and the last line only lands when the counter reaches the real duration
    out = out_rows(lines, rules, wrap); N = len(out)
    badge = lambda p: ">> fast-forward · real time %s" % clock(p * real)
    for fr in range(frames):
        p = fr / max(1, frames - 1); shown = min(max(N - 1, 0), 1 + int(p * max(N - 1, 0))) if N else 0
        save(draw_term(list(history) + out[:shown], caption, badge=badge(p)), check=check if fr == int(frames * .6) else None)
    rows = list(history) + out
    save(draw_term(rows, caption, badge=badge(1)), 18)
    return rows

# ---- pico (what `nano` opens on macOS) ----
PICO_ROWS = VIS - 6
def draw_pico(fname, lines, top, cur, caption, modified=False, status=None, hl_row=None):
    im, d = term_base(caption)
    def inv(y, text, x=BODY_X):
        d.rectangle((x, y, x + CW * len(text), y + LINE_H - 4), fill=TXT); d.text((x, y), text, font=f_code, fill=TERM_BG)
    y0 = BODY_Y
    d.rectangle((BODY_X, y0, BODY_X + BODY_W, y0 + LINE_H - 4), fill=TXT)
    d.text((BODY_X + CW * 2, y0), "UW PICO 5.09", font=f_code, fill=TERM_BG)
    d.text((BODY_X + CW * 19, y0), clip("File: " + fname)[:22], font=f_code, fill=TERM_BG)
    if modified: d.text((BODY_X + CW * (MAXCH - 10), y0), "Modified", font=f_code, fill=TERM_BG)
    for i, l in enumerate(lines[top:top + PICO_ROWS]):
        y = y0 + (i + 2) * LINE_H; l = l[:MAXCH]
        if top + i == hl_row and ": " in l:
            k, v = l.split(": ", 1)
            d.text((BODY_X, y), k + ": ", font=f_code, fill=TXT)
            d.text((BODY_X + CW * (len(k) + 2), y), v, font=f_code, fill=AMBER)
        else: d.text((BODY_X, y), l, font=f_code, fill=AMBER if top + i == hl_row else TXT)
    r, c = cur; c = min(c, MAXCH - 1); cx = BODY_X + CW * c; cy = y0 + (r - top + 2) * LINE_H
    ch = lines[r][c] if c < len(lines[r]) else " "
    d.rectangle((cx, cy + 2, cx + CW - 1, cy + LINE_H - 8), fill=TXT); d.text((cx, cy), ch, font=f_code, fill=TERM_BG)
    fy = y0 + (VIS - 2) * LINE_H
    if status: inv(fy - LINE_H, status, x=BODY_X + (BODY_W - CW * len(status)) // 2)
    foot = [[("^G", "Get Help"), ("^O", "WriteOut"), ("^K", "Cut Text"), ("^C", "Cur Pos")],
            [("^X", "Exit"), ("^J", "Justify"), ("^W", "Where is"), ("^U", "UnCut")]]
    for j, rowf in enumerate(foot):
        for k, (kk, lab) in enumerate(rowf):
            x = BODY_X + k * CW * 12.6
            inv(fy + j * LINE_H, kk, x=x); d.text((x + CW * 3, fy + j * LINE_H), lab, font=f_code, fill=TXT)
    return im

def pico_edit(edit, caption, check=None):
    # open the file, walk down to the line, replace `find` (which must end its
    # line) with `replace`, write out, exit
    fname = edit["file"]; old, new = edit["find"], edit["replace"]
    lines = [l.expandtabs(2) for l in open(os.path.join(EP_DIR, fname)).read().rstrip("\n").split("\n")]
    row = next(i for i, l in enumerate(lines) if old in l)
    assert lines[row].rstrip().endswith(old), "edit.find must be at the end of its line: %r" % lines[row]
    top = max(0, min(row - 6, len(lines) - PICO_ROWS)) if len(lines) > PICO_ROWS else 0
    pic = lambda cur, **k: draw_pico(fname, lines, top, cur, caption, hl_row=row if k.pop("hl", True) else None, **k)
    save(pic((top, 0), hl=False, status="[ Read %d lines ]" % len(lines)), 22)
    for r in range(top + 1, row + 1):                              # arrow down to the line
        key("arrow"); save(pic((r, 0)), 4 if row - top <= 8 else 2)
    key("key"); save(pic((row, len(lines[row]))), 8)               # ^E end of line
    for _ in old:                                                  # backspace the placeholder
        lines[row] = lines[row][:-1]; key("back")
        save(pic((row, len(lines[row])), modified=True), random.choice([2, 3]))
    save(pic((row, len(lines[row])), modified=True), 8)
    for ch in new:
        lines[row] += ch; key("key")
        save(pic((row, len(lines[row])), modified=True), random.choice([2, 2, 2, 3, 3, 1]))
    save(pic((row, len(lines[row])), modified=True), 24, check=check)
    key("key")                                                     # ^O
    save(pic((row, len(lines[row])), modified=True, status="File Name to write : " + fname), 16)
    key("enter")
    save(pic((row, len(lines[row])), status="[ Wrote %d lines ]" % len(lines)), 16)
    key("key")                                                     # ^X

# ---- slides ----
def title_slide(frames):
    t = EP["title"]; im = Image.new("RGB", (W, H), BLACK); d = ImageDraw.Draw(im); cy = H // 2
    centered(d, cy - 330, "// 1-MINUTE DEPLOY · ep.%02d" % EP["num"], f_kick, CYAN)
    f1 = fit(t["app"], SANS, 120, 960, 1); centered(d, cy - 240 + (120 - f1.size) // 2, t["app"], f1, SLIDE_TX)
    if t.get("sub"): centered(d, cy - 90, t["sub"], f_sub, DIM)
    aw = 86; f2 = fit(t["target"], SANS, 84, 960 - aw - 28, 1)
    tw = d.textlength(t["target"], font=f2); x0 = (W - tw - aw - 28) // 2; ay = cy + 52
    d.line((x0, ay, x0 + aw - 6, ay), fill=CYAN, width=11)         # hand-drawn arrow (Helvetica Neue has none)
    d.polygon([(x0 + aw, ay), (x0 + aw - 34, ay - 26), (x0 + aw - 34, ay + 26)], fill=CYAN)
    d.text((x0 + aw + 28, cy + (84 - f2.size) // 2), t["target"], font=f2, fill=CYAN)
    centered(d, cy + 130, t["how"], f_sub, SLIDE_TX)
    save(im, frames, check="title")

def slide(main, sub=None, kicker=None, frames=40, col=CYAN, sub2=None, check=None):
    im = Image.new("RGB", (W, H), BLACK); d = ImageDraw.Draw(im); cy = H // 2
    if kicker: centered(d, cy - 150, kicker, f_kick, col)
    centered(d, cy - 60, main, f_slide, SLIDE_TX)
    if sub: centered(d, cy + 60, sub, fit(sub, SANS, 36, 1000), DIM)
    if sub2: centered(d, cy + 116, sub2, fit(sub2, SANS, 36, 1000), DIM)
    save(im, frames, check=check)

# ---- browser ----
BW_X, BW_W, BT_H, BW_Y = 60, 960, 66, 290; PAGE_H = 1298
_gcache = {}
PAGE_MASK = Image.new("L", (BW_W, PAGE_H), 0)
ImageDraw.Draw(PAGE_MASK).rounded_rectangle((2, -40, BW_W - 3, PAGE_H - 3), radius=15, fill=255)
def walk_img(i):
    if i not in _gcache:
        if len(_gcache) > 40: _gcache.clear()
        im = Image.open(os.path.join(CAP, "walk", G_FR[i][1])).convert("RGB")
        _gcache[i] = im.resize((BW_W, PAGE_H), Image.LANCZOS)
    return _gcache[i]
def walk_at(t): return walk_img(max(0, bisect.bisect_right(G_T, t) - 1))
def fit_url(d, url, maxw):
    if d.textlength(url, font=f_url) <= maxw: return url
    while url and d.textlength(url + "…", font=f_url) > maxw: url = url[:-1]
    return url + "…"

def draw_browser(page, kicker, kcol, url="", caret=False):
    im = Image.new("RGB", (W, H), BLACK); d = ImageDraw.Draw(im)
    centered(d, 200, kicker, f_cap, kcol)
    win_h = BT_H + PAGE_H
    d.rounded_rectangle((BW_X, BW_Y, BW_X + BW_W, BW_Y + win_h), radius=16, fill=CHROME, outline=BORDER, width=2)
    cyb = BW_Y + BT_H // 2
    for k, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        cx = BW_X + 26 + k * 26; d.ellipse((cx - 7, cyb - 7, cx + 7, cyb + 7), fill=c)
    px = BW_X + 112; pw = BW_W - 112 - 22; py = cyb - 19
    d.rounded_rectangle((px, py, px + pw, py + 38), radius=19, fill=(9, 14, 24), outline=BORDER, width=1)
    if SECURE and url:                                                             # padlock for https
        d.rectangle((px + 16, py + 17, px + 30, py + 29), fill=GREEN); d.arc((px + 18, py + 9, px + 28, py + 23), start=180, end=360, fill=GREEN, width=2)
    else:                                                                          # "not https" info dot
        d.ellipse((px + 14, py + 10, px + 32, py + 28), outline=DIM, width=2); d.text((px + 19, py + 6), "i", font=ft(MONO, 18, 1), fill=DIM)
    shown = fit_url(d, url, pw - 60); d.text((px + 44, py + 5), shown, font=f_url, fill=(170, 190, 215))
    if caret:
        cx = px + 44 + d.textlength(shown, font=f_url) + 2; d.rectangle((cx, py + 7, cx + 2, py + 31), fill=(170, 190, 215))
    if page is None: d.rectangle((BW_X + 2, BW_Y + BT_H, BW_X + BW_W - 2, BW_Y + win_h - 4), fill=(17, 24, 39))
    else: im.paste(page, (BW_X, BW_Y + BT_H), PAGE_MASK)
    d.rounded_rectangle((BW_X, BW_Y, BW_X + BW_W, BW_Y + win_h), radius=16, outline=BORDER, width=2)
    d.line((BW_X, BW_Y + BT_H, BW_X + BW_W, BW_Y + BT_H), fill=BORDER, width=1)
    return im

def play(t0, t1, kicker, kcol, sound=True, check=None):
    start = now(); n = int(round((t1 - t0) * FPS))
    if sound:
        for t, kind in G_EV:
            if t0 <= t < t1: KEYS.append([round(start + t - t0, 3), kind])
    for f in range(n):
        save(draw_browser(walk_at(t0 + f / FPS), kicker, kcol, url=HOST), check=check if f == int(n * 0.8) else None)

def url_lines(url):
    if len(url) <= MAXCH - 3: return [url]
    dots = [i for i, c in enumerate(url) if c in "./" and 8 < i < len(url) - 4]
    cut = min(dots, key=lambda i: abs(i - len(url) / 2)) if dots else len(url) // 2
    return [url[:cut], "  " + clip(url[cut:])[:MAXCH - 5]]

# ================= EPISODE =================
B = EP.get("browser", {}); B_START = B.get("start", 0.0); B_LEN = min(B.get("seconds", 8.0), G_END - B_START)
mark("hook")                                   # 1 s payoff: the finished thing, running
hk = max(0.0, min(B.get("hook_at", B_START + B_LEN - 2.0), G_END - 1.0))
play(hk, hk + 1.0, "// " + EP.get("hook", "live on AWS in %s" % human(REAL_TOTAL)), GREEN, sound=False, check="hook")
mark("title"); title_slide(48)

mark("term"); SPEED = TERM_SPEED
rows = []; steps = EP["steps"]
for i, step in enumerate(steps):
    name = step.get("out") or "step%d" % (i + 1); cap = "// %d · %s" % (i + 1, step["caption"])
    if i: MARK["step%d" % (i + 1)] = round(now(), 3)
    rows = type_cmd(rows + ([R("")] if rows else []), step["cmd"], cap)
    if "edit" in step:
        pico_edit(step["edit"], cap, check="edit"); save(draw_term(rows, cap), 4); continue
    lines = step_output(step, name); rules = step.get("rules", []); real = TIMES.get(name, 0.0)
    if i == len(steps) - 1: real += TIMES.get("ready", 0.0)        # time until the app answered counts too
    if step.get("wait", real >= 8.0):
        rows = waited(rows, lines, rules, step.get("frames", 60), cap, real, wrap=step.get("wrap", False), check="step%d" % (i + 1))
    else:
        rows = reveal(rows, lines, rules, step.get("frames", max(14, min(44, len(lines) * 3))), cap,
                      wrap=step.get("wrap", False), check="step%d" % (i + 1))
        save(draw_term(rows, cap), 8)
SPEED = 1.0; mark("live")
LIVE = (["LIVE  in %s" % human(REAL_TOTAL)] + url_lines(URL), GREEN)
lastcap = "// %d · %s" % (len(steps), steps[-1]["caption"])
for k in range(42): save(draw_term(rows, lastcap, banner=LIVE, blink=(k // 6) % 2 == 0), check="live" if k == 30 else None)

mark("browser")
KB = "// " + B.get("open", "open the public URL")
save(draw_browser(None, KB, CYAN, url="", caret=True), 10)
key("key"); save(draw_browser(None, KB, CYAN, url=HOST, caret=True), 24, check="url")     # paste, then a beat
key("enter"); save(draw_browser(None, KB, CYAN, url=HOST), 4)
mark("game")
play(B_START, B_START + B_LEN, "// " + B.get("live", "it's live"), GREEN, check="demo")

mark("outro")
slide("Links in the description", sub="github.com/beamreach-ai/one-minute-deploy",
      sub2="template + every command · " + EP.get("credit", ""), kicker="// try it yourself", frames=42, check="outro1")
slide("Follow for more", sub="like · comment · share", kicker="// 1-minute deploy", frames=44, check="outro2")
mark("end")

ff.stdin.close(); ff.wait()
t = EP["title"]
json.dump({"slug": EP["slug"], "num": EP["num"], "app": t["app"], "target": t["target"], "how": t["how"], "url": URL,
           "dur": round(idx / FPS, 3), "marks": MARK, "keys": KEYS, "real_total": REAL_TOTAL,
           "term_seconds": round(MARK["live"] - MARK["term"], 2), "demo_seconds": round(B_LEN, 2),
           "steps": [s["caption"] for s in steps], "note": EP.get("note", "")},
          open(os.path.join(OUTD, "meta.json"), "w"))
print("%s: %d frames  %.1fs  terminal %.1fs  demo %.1fs  %d sounds  (real deploy %s)" % (
    EP["slug"], idx, idx / FPS, MARK["live"] - MARK["term"], B_LEN, len(KEYS), human(REAL_TOTAL)))
if MARK["live"] - MARK["term"] > 22: print("WARNING: terminal section is long (%.1fs); shorten the commands" % (MARK["live"] - MARK["term"]))
