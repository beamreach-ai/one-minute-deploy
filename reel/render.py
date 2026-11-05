#!/usr/bin/env python3
# 1-Minute Deploy reel renderer (ep.01: 2048 -> S3 website via CloudFormation).
# Same look as the 1-Minute Hacking engine: white-on-black slides, deep-navy
# terminal. Everything on screen comes from the real run in <work>/cap
# (command output, timings, gameplay frames). Frames are piped straight to
# ffmpeg. The terminal section plays at TERM_SPEED; the picture is silent, and
# out/meta.json carries the section marks + every keystroke for music.py.
# Usage: render.py <work dir>   -> <work>/out/video.mp4, <work>/out/meta.json
import bisect, json, os, random, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.abspath(sys.argv[1])
CAP = os.path.join(WORK, "cap"); OUTD = os.path.join(WORK, "out"); os.makedirs(OUTD, exist_ok=True)
TERM_SPEED = 1.8                              # terminal section speed-up (owner: "about x1.8")
W, H, FPS = 1080, 1920, 30
BLACK = (0, 0, 0)
TERM_BG = (11, 17, 32); CHROME = (14, 22, 38); BORDER = (34, 48, 74)
TXT = (205, 227, 255); DIM = (95, 114, 145); CYAN = (79, 209, 255)
GREEN = (61, 220, 132); AMBER = (255, 194, 74); RED = (255, 92, 108); SLIDE_TX = (242, 246, 255)
random.seed(5)

MONO = "/System/Library/Fonts/Menlo.ttc"; SANS = "/System/Library/Fonts/HelveticaNeue.ttc"
def ft(p, s, index=0): return ImageFont.truetype(p, s, index=index)
f_code = ft(MONO, 32); f_title = ft(MONO, 24); f_big = ft(MONO, 40, 1); f_cap = ft(MONO, 30)
f_h1 = ft(SANS, 120, 1); f_h2 = ft(SANS, 84, 1); f_slide = ft(SANS, 78); f_sub = ft(SANS, 36)
f_kick = ft(MONO, 28); f_url = ft(MONO, 24); f_badge = ft(MONO, 28, 1)

# ---- real data from the capture ----
URL = open(os.path.join(CAP, "url.raw")).read().strip()
HOST = URL.replace("http://", "")
TIMES = {l.split()[0]: float(l.split()[2].rstrip("s")) for l in open(os.path.join(CAP, "timings.txt"))}
REAL_DEPLOY = TIMES["deploy"]; REAL_TOTAL = round(TIMES["clone"] + TIMES["deploy"] + TIMES["sync"])

def final_lines(path):                       # keep the last state of each \r-updated line
    out = []
    for ln in open(path, errors="replace").read().split("\n"):
        seg = [s for s in ln.split("\r") if s.strip()]
        if seg: out.append(seg[-1].rstrip())
    return out
def last_per_counter(lines):
    seen = {}; order = []
    for l in lines:
        k = re.match(r"[^0-9]*", l).group(0).strip()
        if k not in seen: order.append(k)
        seen[k] = l
    return [seen[k] for k in order]
CLONE = last_per_counter(final_lines(os.path.join(CAP, "clone.raw")))
DEPLOY = [l for l in final_lines(os.path.join(CAP, "deploy.raw")) if l.strip()]
SYNC = [m.group(0).rstrip() for m in re.finditer(r"upload: [^\r\n]*?(?=Completed|\r|\n|$)",
        open(os.path.join(CAP, "sync.raw"), errors="replace").read())]
YAML_SRC = open(os.path.join(REPO, "ep01-2048-s3", "site.yaml")).read().rstrip("\n").split("\n")
GAME = json.load(open(os.path.join(CAP, "game", "game.json")))
G_T = [f["t"] for f in GAME["frames"]]

# ---- output: raw frames -> ffmpeg ----
ff = subprocess.Popen(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
    "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-c:v", "libx264",
    "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", os.path.join(OUTD, "video.mp4")],
    stdin=subprocess.PIPE)
idx = 0; clock = 0.0; SPEED = 1.0; KEYS = []; MARK = {}
def save(im, n=1, check=None):
    # n frames of screen time at normal speed; SPEED > 1 shortens the hold
    # (a state can fall between frames, its keystroke still lands on the clock)
    global idx, clock
    clock += n / SPEED
    m = int(clock + 1e-6) - idx
    if m > 0:
        b = im.tobytes()
        for _ in range(m): ff.stdin.write(b)
        idx += m
    if check: im.save(os.path.join(OUTD, "check_%s.png" % check))
def now(): return clock / FPS
def key(kind="key"): KEYS.append([round(now(), 3), kind])
def mark(name): MARK[name] = round(now(), 3)

# ---- terminal ----
WIN_X, WIN_W = 28, 1024; WIN_Y, WIN_H = 150, 1630; TITLE_H = 62; PADX, PADY = 20, 18
BODY_X = WIN_X + PADX; BODY_Y = WIN_Y + TITLE_H + PADY
BODY_W = WIN_W - 2 * PADX; BODY_H = WIN_H - TITLE_H - 2 * PADY
CW = f_code.getlength("M"); LINE_H = 44; MAXCH = int(BODY_W / CW); VIS = int(BODY_H / LINE_H) - 1
TERM_TITLE = "aws: public-demo · us-west-1 — zsh"

def clip(s): return s if len(s) <= MAXCH else s[:MAXCH - 1] + "…"
def wrapc(s):
    out = []; cur = ""
    for w in s.split(" "):
        if cur and len(cur) + 1 + len(w) > MAXCH: out.append(cur); cur = "    " + w
        else: cur = (cur + " " + w) if cur else w
    return out + [cur]
def colorize(line, rules):
    for sub, c in rules:
        if sub in line: return c
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
    vis = VIS - (7 if banner else 0) - (2 if badge else 0)
    shown = rows[-vis:]
    x = BODY_X
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
    # slow, human typing (≈14 chars/s) with a key event per character, then a
    # 0.8 s beat before Enter so the viewer can read the command
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

def reveal(history, lines, rules, frames, caption, wrap=False, badge_fn=None, check=None):
    out = []
    for l in lines:
        c = colorize(l, rules)
        out += [R(p, c) for p in (wrapc(l) if wrap else [clip(l)])]
    N = max(1, len(out))
    for fr in range(frames):
        shown = min(N, max(1, round((fr + 1) / frames * N)))
        save(draw_term(list(history) + out[:shown], caption,
                       badge=badge_fn(fr / max(1, frames - 1)) if badge_fn else None),
             check=check if fr == frames - 1 else None)
    return list(history) + out

# ---- pico (macOS `nano`) ----
def draw_pico(lines, cur, caption, modified=False, status=None, hl_row=None):
    im, d = term_base(caption)
    def inv(y, text, x=BODY_X, w=None):
        w = w or CW * len(text)
        d.rectangle((x, y, x + w, y + LINE_H - 4), fill=TXT); d.text((x, y), text, font=f_code, fill=TERM_BG)
    y0 = BODY_Y
    d.rectangle((BODY_X, y0, BODY_X + BODY_W, y0 + LINE_H - 4), fill=TXT)
    d.text((BODY_X + CW * 2, y0), "UW PICO 5.09", font=f_code, fill=TERM_BG)
    d.text((BODY_X + CW * 19, y0), "File: site.yaml", font=f_code, fill=TERM_BG)
    if modified: d.text((BODY_X + CW * (MAXCH - 10), y0), "Modified", font=f_code, fill=TERM_BG)
    for i, l in enumerate(lines):
        y = y0 + (i + 2) * LINE_H
        if i == hl_row and ": " in l:
            k, v = l.split(": ", 1)
            d.text((BODY_X, y), k + ": ", font=f_code, fill=TXT)
            d.text((BODY_X + CW * (len(k) + 2), y), v, font=f_code, fill=AMBER)
        else:
            d.text((BODY_X, y), l, font=f_code, fill=TXT)
    r, c = cur; cx = BODY_X + CW * c; cy = y0 + (r + 2) * LINE_H
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

def pico_edit(caption):
    lines = list(YAML_SRC); row = next(i for i, l in enumerate(lines) if "CHANGE-ME" in l)
    old, new = "CHANGE-ME", "beamreach-2048"
    save(draw_pico(lines, (0, 0), caption, status="[ Read %d lines ]" % len(lines)), 22)
    for r in range(1, row + 1):                                    # arrow down to the line
        key("arrow"); save(draw_pico(lines, (r, 0), caption, hl_row=row), 4)
    key("key"); save(draw_pico(lines, (row, len(lines[row])), caption, hl_row=row), 8)   # ^E end of line
    for _ in old:                                                  # backspace the placeholder
        lines[row] = lines[row][:-1]; key("back")
        save(draw_pico(lines, (row, len(lines[row])), caption, modified=True, hl_row=row), random.choice([2, 3]))
    save(draw_pico(lines, (row, len(lines[row])), caption, modified=True, hl_row=row), 8)
    for ch in new:
        lines[row] += ch; key("key")
        save(draw_pico(lines, (row, len(lines[row])), caption, modified=True, hl_row=row), random.choice([2, 2, 2, 3, 3, 1]))
    save(draw_pico(lines, (row, len(lines[row])), caption, modified=True, hl_row=row), 24, check="pico")
    key("key")                                                     # ^O
    save(draw_pico(lines, (row, len(lines[row])), caption, modified=True, hl_row=row,
                   status="File Name to write : site.yaml"), 16)
    key("enter")
    save(draw_pico(lines, (row, len(lines[row])), caption, hl_row=row, status="[ Wrote %d lines ]" % len(lines)), 16)
    key("key")                                                     # ^X

# ---- slides ----
def title_slide(frames):
    im = Image.new("RGB", (W, H), BLACK); d = ImageDraw.Draw(im); cy = H // 2
    centered(d, cy - 330, "// 1-MINUTE DEPLOY · ep.01", f_kick, CYAN)
    centered(d, cy - 240, "2048", f_h1, SLIDE_TX)
    centered(d, cy - 90, "the game", f_sub, DIM)
    t = "S3 bucket"; tw = d.textlength(t, font=f_h2); aw = 86; x0 = (W - tw - aw - 28) // 2; ay = cy + 52
    d.line((x0, ay, x0 + aw - 6, ay), fill=CYAN, width=11)
    d.polygon([(x0 + aw, ay), (x0 + aw - 34, ay - 26), (x0 + aw - 34, ay + 26)], fill=CYAN)
    d.text((x0 + aw + 28, cy), t, font=f_h2, fill=CYAN)
    centered(d, cy + 130, "with CloudFormation · AWS", f_sub, SLIDE_TX)
    save(im, frames, check="title")

def slide(main, sub=None, kicker=None, frames=40, col=CYAN, sub2=None, check=None):
    im = Image.new("RGB", (W, H), BLACK); d = ImageDraw.Draw(im); cy = H // 2
    if kicker: centered(d, cy - 150, kicker, f_kick, col)
    centered(d, cy - 60, main, f_slide, SLIDE_TX)
    if sub: centered(d, cy + 60, sub, f_sub, DIM)
    if sub2: centered(d, cy + 116, sub2, f_sub, DIM)
    save(im, frames, check=check)

# ---- browser ----
BW_X, BW_W, BT_H, BW_Y = 60, 960, 66, 290; PAGE_H = 1298
_gcache = {}
PAGE_MASK = Image.new("L", (BW_W, PAGE_H), 0)
ImageDraw.Draw(PAGE_MASK).rounded_rectangle((2, -40, BW_W - 3, PAGE_H - 3), radius=15, fill=255)
def game_img(i):
    if i not in _gcache:
        if len(_gcache) > 40: _gcache.clear()
        im = Image.open(os.path.join(CAP, "game", GAME["frames"][i]["f"])).convert("RGB")
        _gcache[i] = im.resize((BW_W, PAGE_H), Image.LANCZOS)
    return _gcache[i]
def game_at(t): return game_img(max(0, bisect.bisect_right(G_T, t) - 1))

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
    d.ellipse((px + 14, py + 10, px + 32, py + 28), outline=DIM, width=2)          # "not https" info dot
    d.text((px + 19, py + 6), "i", font=ft(MONO, 18, 1), fill=DIM)
    d.text((px + 44, py + 5), url, font=f_url, fill=(170, 190, 215))
    if caret:
        cx = px + 44 + d.textlength(url, font=f_url) + 2; d.rectangle((cx, py + 7, cx + 2, py + 31), fill=(170, 190, 215))
    if page is None: d.rectangle((BW_X + 2, BW_Y + BT_H, BW_X + BW_W - 2, BW_Y + win_h - 4), fill=(17, 24, 39))
    else: im.paste(page, (BW_X, BW_Y + BT_H), PAGE_MASK)
    d.rounded_rectangle((BW_X, BW_Y, BW_X + BW_W, BW_Y + win_h), radius=16, outline=BORDER, width=2)
    d.line((BW_X, BW_Y + BT_H, BW_X + BW_W, BW_Y + BT_H), fill=BORDER, width=1)
    return im

def play(t0, t1, kicker, kcol, sound=True, check=None):
    start = now(); n = int(round((t1 - t0) * FPS))
    if sound:
        for k in GAME["keys"]:
            if t0 <= k["wall"] < t1: KEYS.append([round(start + k["wall"] - t0, 3), "arrow"])
    for f in range(n):
        save(draw_browser(game_at(t0 + f / FPS), kicker, kcol, url=HOST),
             check=check if f == int(n * 0.8) else None)

# ================= EPISODE =================
G_END = GAME["frames"][-1]["t"]
mark("hook")                                   # 1 s payoff: the finished thing, running
play(G_END - 2.6, G_END - 1.6, "// live on AWS in %d seconds" % REAL_TOTAL, GREEN, sound=False, check="hook")
mark("title"); title_slide(48)

mark("term"); SPEED = TERM_SPEED
C1 = "// 1 · get the code"; C2 = "// 2 · name your bucket"
C3 = "// 3 · create the bucket"; C4 = "// 4 · upload the site"
rows = type_cmd([], ["git clone https://github.com/gabrielecirulli/2048"], C1)
rows = reveal(rows, CLONE, [("done.", DIM), ("remote:", DIM)], 26, C1)
save(draw_term(rows + [R("")], C1), 8, check="clone")
mark("nano")
rows = type_cmd(rows + [R("")], ["nano site.yaml"], C2)
pico_edit(C2)
save(draw_term(rows, C2), 4)
mark("deploy")
rows = type_cmd(rows + [R("")], ["aws cloudformation deploy \\", "  --stack-name play-2048 \\", "  --template-file site.yaml"], C3)
def ff_badge(p): s = int(round(p * REAL_DEPLOY)); return ">> fast-forward · real time %d:%02d" % (s // 60, s % 60)
h = rows + [R("")]
for fr in range(60):                           # the real 41 s wait, compressed and labelled
    p = fr / 59; shown = [R(DEPLOY[0], DIM)] + ([R(DEPLOY[1], DIM)] if p > 0.22 else [])
    save(draw_term(h + shown, C3, badge=ff_badge(p)), check="deploy" if fr == 40 else None)
rows = h + [R(DEPLOY[0], DIM), R(DEPLOY[1], DIM), R(clip(DEPLOY[2]), GREEN)]
save(draw_term(rows, C3, badge=ff_badge(1)), 18)
mark("upload")
rows = type_cmd(rows + [R("")], ["aws s3 sync 2048 s3://beamreach-2048 \\", '  --exclude ".git*"'], C4)
rows = reveal(rows, SYNC, [("index.html", CYAN)], 38, C4)
SPEED = 1.0; mark("live")
LIVE = (["LIVE  in %d seconds" % REAL_TOTAL, "http://beamreach-2048", "  .s3-website-us-west-1.amazonaws.com"], GREEN)
for k in range(42): save(draw_term(rows, C4, banner=LIVE, blink=(k // 6) % 2 == 0), check="live" if k == 30 else None)

mark("browser")
KB = "// open the bucket's public URL"
save(draw_browser(None, KB, CYAN, url="", caret=True), 10)
key("key"); save(draw_browser(None, KB, CYAN, url=HOST, caret=True), 24, check="url")     # paste, then the 0.8 s beat
key("enter"); save(draw_browser(None, KB, CYAN, url=HOST), 4)
mark("game")
play(0.0, G_END - 0.6, "// it's live — and it plays", GREEN, check="game")

mark("outro")
slide("Links in the description", sub="github.com/beamreach-ai/one-minute-deploy", sub2="template + every command · app by gabrielecirulli",
      kicker="// try it yourself", frames=42, check="outro1")
slide("Follow for more", sub="like · comment · share", kicker="// 1-minute deploy", frames=44, check="outro2")
mark("end")

ff.stdin.close(); ff.wait()
json.dump({"slug": "ep01_2048_s3", "dur": round(idx / FPS, 3), "marks": MARK, "keys": KEYS, "real_total": REAL_TOTAL},
          open(os.path.join(OUTD, "meta.json"), "w"))
print("frames %d  %.1fs  keys %d" % (idx, idx / FPS, len(KEYS)))
for k, v in MARK.items(): print("  %-8s %6.2f" % (k, v))
