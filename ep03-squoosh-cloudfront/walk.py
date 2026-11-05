# Walkthrough for ep.03: open one of Squoosh's own demo photos, compare before
# and after with the divider, then pull the quality down and watch the size drop.
# 640 px wide is about the narrowest Squoosh shows its side-by-side layout at.
import asyncio, re, time

async def glide(w, x, y, ms):                      # pointer move on a real-time clock
    x0, y0 = w.x, w.y; t0 = time.time()
    while True:
        p = min(1.0, (time.time() - t0) * 1000 / ms); e = p * p * (3 - 2 * p)
        await w.page.mouse.move(x0 + (x - x0) * e, y0 + (y - y0) * e)
        if p >= 1: break
        await asyncio.sleep(0.012)
    w.x, w.y = x, y

async def sizes(p):                                # the file sizes shown under the two sides
    return re.findall(r"[\d.]+\s*[kM]B", await p.evaluate("document.body.innerText"))

async def walk(w):
    p = w.page; cx, cy = w.width / 2, w.height / 2
    async with w.cut():
        demo = p.locator("button.unbutton", has_text="MB").first
        await demo.wait_for(); await w.wait(2500)
        d = p.locator("button", has_text="dismiss")            # "Ready to work offline" toast
        if await d.count(): await d.first.click()
        await demo.scroll_into_view_if_needed(); await w.wait(900)
        b = await demo.bounding_box()
    await w.wait(250)
    await glide(w, b["x"] + b["width"] / 2, b["y"] + b["height"] / 2 - 12, 350)     # the red panda demo photo
    await p.mouse.down(); w.ev("click"); await asyncio.sleep(0.05); await p.mouse.up(); await w.wait(200)
    async with w.cut():                                        # loading + the first encode
        await p.wait_for_selector("range-input[name=quality]")
        for _ in range(100):
            if len(await sizes(p)) >= 2: break
            await w.wait(200)
        await w.wait(1200)
    first = await sizes(p)
    await w.wait(300)
    # before | after: pull the divider left, then right
    await glide(w, cx, cy, 250); await p.mouse.down(); w.ev("click")
    await glide(w, 140, cy, 400); await glide(w, 430, cy, 500); await glide(w, cx, cy, 250); await p.mouse.up()
    # quality 75 -> about 10
    box = await p.locator("range-input[name=quality]").bounding_box()
    y = box["y"] + box["height"] / 2; x75 = box["x"] + box["width"] * 0.75; x10 = box["x"] + box["width"] * 0.10
    await glide(w, x75, y, 300); await p.mouse.down(); w.ev("click")
    await glide(w, x10, y, 600); await p.mouse.up(); await w.wait(150)
    async with w.cut():                                        # the re-encode
        for _ in range(150):
            if await sizes(p) != first: break
            await w.wait(100)
        await w.wait(500)
    await w.wait(350)
    await glide(w, cx, cy, 250); await p.mouse.down(); w.ev("click")
    await glide(w, 130, cy, 550); await glide(w, 300, cy, 600); await p.mouse.up()
    await glide(w, 300, cy + 150, 250)
    await w.wait(900)
