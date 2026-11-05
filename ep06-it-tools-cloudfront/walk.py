# Walkthrough for ep.06: open "Hash text" and type (the digests update live),
# then jump to the QR code generator through the search box and make a code.
import asyncio, time

async def glide(w, x, y, ms):                      # pointer move on a real-time clock
    x0, y0 = w.x, w.y; t0 = time.time()
    while True:
        p = min(1.0, (time.time() - t0) * 1000 / ms); e = p * p * (3 - 2 * p)
        await w.page.mouse.move(x0 + (x - x0) * e, y0 + (y - y0) * e)
        if p >= 1: break
        await asyncio.sleep(0.012)
    w.x, w.y = x, y

async def tap(w, target, ms=300, after=120):       # glide to a Locator or (x, y) and click it
    if isinstance(target, tuple): x, y = target
    else:
        b = await target.bounding_box(); x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    await glide(w, x, y, ms)
    await w.page.mouse.down(); w.ev("click"); await asyncio.sleep(0.05); await w.page.mouse.up()
    await w.wait(after)

async def walk(w):
    p = w.page
    card = p.locator("a[href='/hash-text']", has_text="Hash a text string")     # the card, not the side-menu link
    async with w.cut():
        await card.wait_for(); await w.wait(1100)
    await w.wait(400)
    await tap(w, card)
    async with w.cut():
        box = p.locator("textarea").first
        await box.wait_for(); await w.wait(1000)
    await tap(w, box)
    await w.type("one minute deploy", cps=18)
    await w.wait(450)
    await tap(w, p.locator("button", has_text="Search"), after=350)
    await w.type("qr", cps=8)
    await w.wait(300)
    await w.press("Enter", after=200)
    async with w.cut():
        text = p.locator("textarea").first
        await p.wait_for_url("**/qrcode-generator"); await text.wait_for(); await w.wait(1200)
    await tap(w, text)
    await p.keyboard.press("ControlOrMeta+a"); await w.wait(120)
    await w.type("beamreach.ai", cps=16)
    await glide(w, 430, 420, 250)
    await w.wait(1100)
