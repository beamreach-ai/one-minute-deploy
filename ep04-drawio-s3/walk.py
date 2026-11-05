# Walkthrough for ep.04: drag two shapes from the palette onto the canvas, name
# them, and connect them with an arrow.
import asyncio, time

ARROW = 'img[title^="Click to connect"]'                      # the blue arrows around a hovered shape
BOTTOM_ARROW = """() => { const b = [...document.querySelectorAll('img[title^="Click to connect"]')]
    .map(a => a.getBoundingClientRect()).sort((p, q) => q.y - p.y)[0]; return [b.x + b.width / 2, b.y + b.height / 2] }"""

async def glide(w, x, y, ms=350):
    # the pointer, paced by the clock instead of by a fixed number of steps:
    # draw.io answers each mouse move slowly (40 ms and more), so w.move would
    # take several times as long as asked
    x0, y0 = w.x, w.y; t0 = time.time()
    while True:
        q = min(1.0, (time.time() - t0) * 1000 / ms); e = q * q * (3 - 2 * q)
        await w.page.mouse.move(x0 + (x - x0) * e, y0 + (y - y0) * e)
        if q >= 1: break
    w.x, w.y = x, y

async def drag(w, x1, y1, x2, y2, ms=450, after=150):
    await glide(w, x1, y1, 300); await w.page.mouse.down(); w.ev("click")
    await glide(w, x2, y2, ms); await asyncio.sleep(0.05); await w.page.mouse.up()
    await w.page.wait_for_timeout(after)

async def click(w, x, y, ms=220, after=120):
    await glide(w, x, y, ms); await w.page.mouse.down(); w.ev("click"); await asyncio.sleep(0.05)
    await w.page.mouse.up(); await w.page.wait_for_timeout(after)

async def shapes_open(p):
    return await p.evaluate("() => { const s = document.querySelector('.geSidebarContainer'); return !!s && s.getBoundingClientRect().width > 100 }")

async def walk(w):
    p = w.page
    async with w.cut():
        await p.wait_for_selector(".geDiagramContainer", timeout=60000)
        await w.wait(2500)
        if not await shapes_open(p):                          # narrow windows start with the palette closed
            await p.click('.geButton[title^="View (Space"]')
            await p.locator(".mxPopupMenu tr.mxPopupMenuItem", has_text="Shapes").first.click()
            await p.wait_for_selector(".geSidebarContainer a.geItem", timeout=20000)
        for _ in range(2):                                    # zoom in, so the shapes read on a phone
            await p.click('.geButton[title^="Zoom In"]'); await w.wait(300)
        await w.wait(600)
        items = p.locator(".geSidebarContainer a.geItem")
        rect = await w._point(items.nth(0)); cyl = await w._point(items.nth(12))
        await w.move(470, 700, 200)
    await w.wait(150)
    await drag(w, rect[0], rect[1], 390, 250)                 # a rectangle from the palette
    await w.type("your code", cps=15)
    await w.wait(120)
    await drag(w, cyl[0], cyl[1], 433, 560)                   # a cylinder
    await w.type("S3", cps=9)
    await w.wait(150)
    await click(w, 640, 440)                                  # empty canvas: done typing
    await glide(w, 476, 300, 260)                             # hover the rectangle: its arrows appear
    await p.wait_for_selector(ARROW, timeout=5000)
    ax, ay = await p.evaluate(BOTTOM_ARROW)                   # the one below the shape
    await drag(w, ax, ay, 482, 654, ms=500, after=200)        # pull it onto the cylinder (below its label)
    await click(w, 640, 440, ms=250, after=100)               # deselect
    await glide(w, 660, 820, 300)
    await w.wait(1900)
