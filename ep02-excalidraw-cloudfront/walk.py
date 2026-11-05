# Walkthrough for ep.02: draw a box and label it, draw an ellipse and label it,
# then join the two with an arrow. Excalidraw at 540 px wide uses its phone
# layout: the toolbar sits at the bottom.
import asyncio, time

async def glide(w, x, y, ms):
    # pointer move on a real-time clock: Excalidraw redraws on every mouse move,
    # so walklib's fixed number of steps takes several times longer than asked
    x0, y0 = w.x, w.y; t0 = time.time()
    while True:
        p = min(1.0, (time.time() - t0) * 1000 / ms); e = p * p * (3 - 2 * p)
        await w.page.mouse.move(x0 + (x - x0) * e, y0 + (y - y0) * e)
        if p >= 1: break
        await asyncio.sleep(0.012)
    w.x, w.y = x, y

async def tap(w, target, ms=260, after=70, n=1):    # glide to a selector or (x, y) and click it
    x, y = await w._point(target)
    await glide(w, x, y, ms)
    for k in range(1, n + 1):
        await w.page.mouse.down(click_count=k); w.ev("click"); await asyncio.sleep(0.04)
        await w.page.mouse.up(click_count=k); await asyncio.sleep(0.05)
    await w.wait(after)

async def draw(w, x1, y1, x2, y2, go=250, ms=520):  # press, drag, release
    await glide(w, x1, y1, go); await w.page.mouse.down(); w.ev("click")
    await glide(w, x2, y2, ms); await w.page.mouse.up(); await w.wait(70)

async def label(w, x, y, text, cps):               # double-click a shape, type its label
    await tap(w, (x, y), ms=180, after=120, n=2)
    await w.type(text, cps=cps)
    await w.press("Escape", after=60)

async def walk(w):
    p = w.page
    async with w.cut():
        await p.wait_for_selector('[data-testid="toolbar-rectangle"]')
        await p.evaluate("document.fonts.ready"); await w.wait(1500)
    await w.wait(450)
    await tap(w, (247, 698))                                     # rectangle tool
    await draw(w, 45, 110, 300, 250)
    await label(w, 172, 180, "CloudFront", 16)
    await tap(w, (247, 698), after=200)                          # same button again: its shape picker opens
    await tap(w, '[data-testid="toolbar-ellipse"]', ms=120)
    await draw(w, 240, 400, 495, 560)
    await label(w, 368, 480, "S3", 8)
    await tap(w, '[data-testid="toolbar-arrow"]')
    await draw(w, 190, 256, 340, 408, ms=520)
    await glide(w, 110, 470, 240)                                # pointer off the drawing
    await w.wait(900)
