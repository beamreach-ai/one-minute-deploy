# Walkthrough for ep.12: a second device opens the same address, shows up on
# this one, and sends a picture across.
#
# The second device is another browser context that is not recorded: a
# phone-sized window with a phone's user agent, on the same network, so
# PairDrop puts both in one room. What the recorded page shows is what really
# arrives from it.
import asyncio, io, time
from PIL import Image, ImageDraw

PHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")

def picture():                                  # a small drawn image for the phone to send
    im = Image.new("RGB", (900, 600)); d = ImageDraw.Draw(im)
    for y in range(600): d.line((0, y, 900, y), fill=(255 - y // 4, 150 - y // 6, 90 + y // 5))
    d.ellipse((620, 90, 780, 250), fill=(255, 236, 170))
    d.polygon([(0, 600), (260, 300), (480, 600)], fill=(40, 50, 90))
    d.polygon([(300, 600), (600, 360), (900, 600)], fill=(30, 38, 70))
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()

CENTER = "s => { const r = document.querySelector(s).getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2] }"

async def glide(w, x, y, ms=400):
    # the pointer, paced by the clock (w.move counts steps, and runs slow on a busy machine)
    x0, y0 = w.x, w.y; t0 = time.time()
    while True:
        q = min(1.0, (time.time() - t0) * 1000 / ms); e = q * q * (3 - 2 * q)
        await w.page.mouse.move(x0 + (x - x0) * e, y0 + (y - y0) * e)
        if q >= 1: break
        await asyncio.sleep(0.012)
    w.x, w.y = x, y

async def click(w, selector, ms=400):
    x, y = await w.page.evaluate(CENTER, selector)
    await glide(w, x, y, ms); await asyncio.sleep(0.08)
    await w.page.mouse.down(); w.ev("click"); await asyncio.sleep(0.06); await w.page.mouse.up()

async def walk(w):
    p = w.page; url = p.url
    async with w.cut():
        await p.wait_for_selector("x-no-peers", timeout=30000)
        phone_ctx = await p.context.browser.new_context(viewport={"width": 390, "height": 844},
                                                        user_agent=PHONE_UA, locale="en-US")
        phone = await phone_ctx.new_page()
        png = picture()
        await w.wait(2500)
        await w.move(400, 520, 200)
    await asyncio.sleep(0.7)                                  # alone in the room
    async with w.cut():                                       # the phone opens the same address (a few seconds)
        await phone.goto(url, wait_until="load", timeout=60000)
        await p.wait_for_selector("x-peer", state="attached", timeout=30000)
    await asyncio.sleep(1.3)                                  # ...and shows up here
    await phone.locator("x-peer input[type=file]").set_input_files(
        {"name": "sunset.png", "mimeType": "image/png", "buffer": png})   # the phone sends a picture
    await p.wait_for_selector("#receive-request-dialog[show] #accept-request", timeout=20000)
    await asyncio.sleep(1.0)
    await click(w, "#accept-request", ms=450)
    await p.wait_for_selector("#receive-file-dialog[show] #download-btn", timeout=20000)
    await asyncio.sleep(1.9)
    await click(w, "#receive-file-dialog button[close]", ms=420)
    await asyncio.sleep(0.3)
    await glide(w, 400, 560, 350)
    await asyncio.sleep(1.7)
