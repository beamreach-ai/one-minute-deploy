#!/usr/bin/env python3
# Play 2048 on the live S3 URL and record it: CDP screencast frames (timestamped)
# plus the time of every key press. Usage: game.py <url> <outdir> [moves]
import asyncio, base64, json, os, random, sys, time
from playwright.async_api import async_playwright

URL, OUT = sys.argv[1], sys.argv[2]
MOVES = int(sys.argv[3]) if len(sys.argv) > 3 else 40
os.makedirs(OUT, exist_ok=True)
random.seed(11)
KEYS = {"down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight", "up": "ArrowUp"}

def slide(row):                       # slide/merge one row toward index 0
    v = [x for x in row if x]; out = []; gain = 0; i = 0
    while i < len(v):
        if i + 1 < len(v) and v[i] == v[i + 1]:
            out.append(v[i] * 2); gain += v[i] * 2; i += 2
        else:
            out.append(v[i]); i += 1
    return out + [0] * (4 - len(out)), gain

def move(g, d):                       # g[row][col]
    n = [[0] * 4 for _ in range(4)]; gain = 0
    for k in range(4):
        if d == "left":   line = g[k]
        elif d == "right": line = g[k][::-1]
        elif d == "up":   line = [g[r][k] for r in range(4)]
        else:             line = [g[r][k] for r in range(4)][::-1]
        res, gg = slide(line); gain += gg
        if d == "right" or d == "down": res = res[::-1]
        for j in range(4):
            if d in ("left", "right"): n[k][j] = res[j]
            else: n[j][k] = res[j]
    return n, gain

def pick(g):
    best = None
    for pref, d in enumerate(["down", "left", "right", "up"]):
        n, gain = move(g, d)
        if n == g: continue
        empties = sum(x == 0 for r in n for x in r)
        corner = 40 if n[3][0] == max(max(r) for r in n) else 0
        score = gain * 2 + empties * 6 + corner - pref * 3 - (60 if d == "up" else 0)
        if best is None or score > best[0]: best = (score, d)
    return best[1] if best else None

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1460}, device_scale_factor=1)
        await pg.goto(URL); await pg.wait_for_timeout(800)
        await pg.evaluate("document.documentElement.style.zoom=2; window.scrollTo(0,120)"); await pg.wait_for_timeout(300)
        cdp = await pg.context.new_cdp_session(pg)
        frames = []; t0 = [None]
        async def ack(sid): 
            try: await cdp.send("Page.screencastFrameAck", {"sessionId": sid})
            except Exception: pass
        def on_frame(ev):
            ts = ev["metadata"]["timestamp"]
            if t0[0] is None: t0[0] = ts
            name = "s%05d.jpg" % len(frames)
            open(os.path.join(OUT, name), "wb").write(base64.b64decode(ev["data"]))
            frames.append({"t": round(ts - t0[0], 4), "f": name})
            asyncio.ensure_future(ack(ev["sessionId"]))
        cdp.on("Page.screencastFrame", on_frame)
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 95, "everyNthFrame": 1})
        wall0 = time.time()
        await pg.wait_for_timeout(900)
        keys = []
        for i in range(MOVES):
            st = json.loads(await pg.evaluate("localStorage.getItem('gameState')"))
            cells = st["grid"]["cells"]      # cells[x][y]
            g = [[(cells[x][y] or {}).get("value", 0) for x in range(4)] for y in range(4)]
            d = pick(g)
            if d is None: break
            keys.append({"wall": round(time.time() - wall0, 4), "dir": d})
            await pg.keyboard.press(KEYS[d])
            await pg.wait_for_timeout(random.choice([240, 260, 290, 310, 340, 400]))
        await pg.wait_for_timeout(900)
        await cdp.send("Page.stopScreencast")
        st = json.loads(await pg.evaluate("localStorage.getItem('gameState')"))
        g = [[(st["grid"]["cells"][x][y] or {}).get("value", 0) for x in range(4)] for y in range(4)]
        json.dump({"frames": frames, "keys": keys, "score": st["score"], "grid": g,
                   "dur": round(time.time() - wall0, 3)}, open(os.path.join(OUT, "game.json"), "w"))
        print("frames", len(frames), "last t", frames[-1]["t"], "wall", round(time.time() - wall0, 2),
              "keys", len(keys), "score", st["score"]); [print(r) for r in g]
        await b.close()
asyncio.run(main())
