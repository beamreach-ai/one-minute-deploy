#!/usr/bin/env python3
"""Record an app walkthrough for a reel.

An episode's walk.py defines `async def walk(w)` and drives the live app
through a Walk: a visible pointer glides to what it clicks, typing happens key
by key, and every click / keystroke is logged with its time so the soundtrack
can put a sound on it. The page is captured as 1080x1460 frames (CDP
screencast, ~50 fps) with timestamps.

Dead air (page loads, waiting for a server) goes inside `async with w.cut():`
and is dropped from the reel.
"""
import asyncio, base64, json, os, random, time
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright

FRAME_W, FRAME_H = 1080, 1460

# A pointer drawn inside the page; it follows the real (headless) mouse.
CURSOR_JS = r"""
(() => {
  if (window.__omd) return; window.__omd = true;
  const NS = 'http://www.w3.org/2000/svg';
  let x = 0, y = 0;
  try { const s = JSON.parse(sessionStorage.getItem('__omd_xy') || 'null'); if (s) { x = s[0]; y = s[1]; } } catch (e) {}
  let cur = null, shown = true;
  try { shown = sessionStorage.getItem('__omd_show') !== '0'; } catch (e) {}
  window.__omdShow = v => { shown = !!v; try { sessionStorage.setItem('__omd_show', v ? '1' : '0'); } catch (e) {} place(); };
  const make = () => {
    if (!document.documentElement) return;
    if (cur && cur.isConnected) return;
    cur = document.createElement('div');
    const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('width', '26'); svg.setAttribute('height', '26'); svg.setAttribute('viewBox', '0 0 24 24');
    const p = document.createElementNS(NS, 'path'); p.setAttribute('d', 'M4 2l15 9-7 1.6L9 20z');
    p.setAttribute('fill', '#fff'); p.setAttribute('stroke', '#111'); p.setAttribute('stroke-width', '1.6'); p.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(p); cur.appendChild(svg);
    cur.style.cssText = 'position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;margin:-2px 0 0 -4px;filter:drop-shadow(0 1px 2px rgba(0,0,0,.45))';
    document.documentElement.appendChild(cur); place();
  };
  const place = () => { if (cur) { cur.style.transform = 'translate(' + x + 'px,' + y + 'px)'; cur.style.display = shown ? '' : 'none'; } };
  const ripple = () => {
    if (!document.documentElement) return;
    const r = document.createElement('div');
    r.style.cssText = 'position:fixed;z-index:2147483646;pointer-events:none;left:' + (x - 18) + 'px;top:' + (y - 18) + 'px;width:36px;height:36px;border-radius:50%;border:3px solid rgba(79,209,255,.95);background:rgba(79,209,255,.25);transition:transform .32s ease-out,opacity .32s ease-out;transform:scale(.3);opacity:1';
    document.documentElement.appendChild(r);
    requestAnimationFrame(() => { r.style.transform = 'scale(1.5)'; r.style.opacity = '0'; });
    setTimeout(() => r.remove(), 380);
  };
  window.addEventListener('mousemove', e => { x = e.clientX; y = e.clientY; make(); place(); try { sessionStorage.setItem('__omd_xy', JSON.stringify([x, y])); } catch (e) {} }, true);
  window.addEventListener('mousedown', () => { make(); if (shown) ripple(); }, true);
  document.addEventListener('DOMContentLoaded', make); setInterval(make, 300); make();
})();
"""


class Walk:
    def __init__(self, page, cdp, outdir, width, height):
        self.page, self.cdp, self.out = page, cdp, outdir
        self.width, self.height = width, height
        self.frames, self.events, self.cuts = [], [], []
        self.t0 = None; self.x, self.y = width * 0.5, height * 0.6
        self.rng = random.Random(7)

    # ---- clock / log ----
    def now(self): return time.time() - self.t0
    def ev(self, kind): self.events.append({"t": round(self.now(), 3), "kind": kind})

    async def _start(self):
        def on_frame(ev):
            name = "s%05d.jpg" % len(self.frames)
            with open(os.path.join(self.out, name), "wb") as f: f.write(base64.b64decode(ev["data"]))
            self.frames.append({"t": round(ev["metadata"]["timestamp"] - self.t0, 4), "f": name})
            asyncio.ensure_future(self._ack(ev["sessionId"]))
        self.cdp.on("Page.screencastFrame", on_frame)
        self.t0 = time.time()
        await self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 93, "everyNthFrame": 1})
        await self.page.mouse.move(self.x, self.y)

    async def _ack(self, sid):
        try: await self.cdp.send("Page.screencastFrameAck", {"sessionId": sid})
        except Exception: pass

    # ---- actions ----
    async def wait(self, ms): await self.page.wait_for_timeout(ms)

    async def cursor(self, show):
        """Show or hide the drawn pointer (hide it for keyboard-only demos)."""
        await self.page.evaluate("v => window.__omdShow && window.__omdShow(v)", bool(show))

    @asynccontextmanager
    async def cut(self):
        """Everything inside is dropped from the reel (loads, waits)."""
        a = self.now()
        try: yield
        finally:
            await self.page.wait_for_timeout(120)          # let the settled frame arrive
            self.cuts.append([round(a, 3), round(self.now(), 3)])

    async def move(self, x, y, ms=420):
        x0, y0 = self.x, self.y; n = max(2, int(ms / 16))
        for i in range(1, n + 1):
            p = i / n; e = p * p * (3 - 2 * p)                 # ease in-out
            await self.page.mouse.move(x0 + (x - x0) * e, y0 + (y - y0) * e)
            await asyncio.sleep(ms / n / 1000)
        self.x, self.y = x, y

    async def _point(self, target):
        if isinstance(target, (tuple, list)): return float(target[0]), float(target[1])
        loc = self.page.locator(target).first if isinstance(target, str) else target
        await loc.scroll_into_view_if_needed(timeout=15000)
        box = await loc.bounding_box()
        if not box: raise RuntimeError("no box for %r" % (target,))
        return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2

    async def click(self, target, ms=420, after=250):
        """Glide to a selector / Locator / (x, y) and click it."""
        x, y = await self._point(target)
        await self.move(x, y, ms); await asyncio.sleep(0.08)
        await self.page.mouse.down(); self.ev("click"); await asyncio.sleep(0.06); await self.page.mouse.up()
        await self.page.wait_for_timeout(after)

    async def dblclick(self, target, ms=420, after=300):
        """Glide to the target and double-click it (two audible clicks)."""
        x, y = await self._point(target)
        await self.move(x, y, ms); await asyncio.sleep(0.08)
        await self.page.mouse.down(); self.ev("click"); await self.page.mouse.up(); await asyncio.sleep(0.09)
        await self.page.mouse.down(click_count=2); self.ev("click"); await self.page.mouse.up(click_count=2)
        await self.page.wait_for_timeout(after)

    async def drag(self, x1, y1, x2, y2, ms=700, after=200):
        await self.move(x1, y1, 350); await self.page.mouse.down(); self.ev("click")
        await self.move(x2, y2, ms); await self.page.mouse.up(); await self.page.wait_for_timeout(after)

    async def type(self, text, cps=13):
        """Type into whatever has focus, one audible key at a time."""
        for ch in text:
            await self.page.keyboard.type(ch); self.ev("space" if ch == " " else "key")
            await asyncio.sleep(max(0.03, self.rng.gauss(1.0 / cps, 0.018)))

    async def press(self, key, after=200):
        await self.page.keyboard.press(key)
        self.ev("enter" if key == "Enter" else "arrow" if key.startswith("Arrow") else "back" if key == "Backspace" else "key")
        await self.page.wait_for_timeout(after)

    async def scroll(self, dy, ms=500):
        n = max(2, int(ms / 30))
        for _ in range(n):
            await self.page.mouse.wheel(0, dy / n); await asyncio.sleep(ms / n / 1000)


async def record(url, outdir, walk_fn, width=540, headless=True):
    """Open `url` at `width` CSS px (frames are always 1080x1460) and run walk_fn(w)."""
    scale = FRAME_W / width; height = int(round(FRAME_H / scale))
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        if f.endswith(".jpg") or f == "walk.json": os.remove(os.path.join(outdir, f))
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=headless, args=["--force-device-scale-factor=%s" % scale])
        ctx = await b.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale,
                                  ignore_https_errors=True, locale="en-US")
        await ctx.add_init_script(CURSOR_JS)
        page = await ctx.new_page()
        await page.goto(url, wait_until="load", timeout=90000)
        cdp = await ctx.new_cdp_session(page)
        w = Walk(page, cdp, outdir, width, height)
        await w._start()
        await walk_fn(w)
        await page.wait_for_timeout(300)
        await cdp.send("Page.stopScreencast")
        dur = round(w.now(), 3)
        json.dump({"frames": w.frames, "events": w.events, "cuts": w.cuts, "dur": dur, "width": width},
                  open(os.path.join(outdir, "walk.json"), "w"))
        kept = dur - sum(b_ - a_ for a_, b_ in w.cuts)
        print("walk: %d frames, %.1f s recorded, %.1f s kept, %d events" % (len(w.frames), dur, kept, len(w.events)))
        await b.close()
