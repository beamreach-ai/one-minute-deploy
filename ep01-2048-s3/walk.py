# Walkthrough for ep.01: actually play 2048 on the live site with the arrow keys.
import json, random

KEYS = {"down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight", "up": "ArrowUp"}

def slide(row):                               # slide/merge one row toward index 0
    v = [x for x in row if x]; out = []; gain = 0; i = 0
    while i < len(v):
        if i + 1 < len(v) and v[i] == v[i + 1]: out.append(v[i] * 2); gain += v[i] * 2; i += 2
        else: out.append(v[i]); i += 1
    return out + [0] * (4 - len(out)), gain

def move(g, d):                               # g[row][col]
    n = [[0] * 4 for _ in range(4)]; gain = 0
    for k in range(4):
        line = g[k] if d == "left" else g[k][::-1] if d == "right" else [g[r][k] for r in range(4)]
        if d == "down": line = line[::-1]
        res, gg = slide(line); gain += gg
        if d in ("right", "down"): res = res[::-1]
        for j in range(4):
            if d in ("left", "right"): n[k][j] = res[j]
            else: n[j][k] = res[j]
    return n, gain

def pick(g):                                  # greedy: merge, keep space, keep the big tile in a corner
    best = None
    for pref, d in enumerate(["down", "left", "right", "up"]):
        n, gain = move(g, d)
        if n == g: continue
        empties = sum(x == 0 for r in n for x in r)
        corner = 40 if n[3][0] == max(max(r) for r in n) else 0
        score = gain * 2 + empties * 6 + corner - pref * 3 - (60 if d == "up" else 0)
        if best is None or score > best[0]: best = (score, d)
    return best[1] if best else None

async def walk(w):
    rnd = random.Random(11)
    async with w.cut():
        await w.cursor(False)                                 # keyboard-only demo: no pointer
        await w.page.evaluate("window.scrollTo(0, 60)"); await w.wait(400)
    await w.wait(700)
    for _ in range(40):
        st = json.loads(await w.page.evaluate("localStorage.getItem('gameState')"))
        cells = st["grid"]["cells"]                           # cells[x][y]
        g = [[(cells[x][y] or {}).get("value", 0) for x in range(4)] for y in range(4)]
        d = pick(g)
        if d is None: break
        await w.press(KEYS[d], after=rnd.choice([240, 260, 290, 310, 340, 400]))
    await w.wait(700)
