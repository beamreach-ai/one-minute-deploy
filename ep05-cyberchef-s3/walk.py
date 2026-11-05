# Walkthrough for ep.05: type some text, add "To Base64" to the recipe, then
# search for ROT13 and stack it on top. The output updates live.
async def walk(w):
    p = w.page
    await w.wait(250)
    await w.click("#input-text .cm-content", ms=350, after=100)
    await w.type("deployed in one minute", cps=17)
    await w.wait(200)
    await w.dblclick(p.locator("#categories li.operation", has_text="To Base64").first, ms=380, after=200)
    await w.move(640, 900, 300); await w.wait(300)            # off the list, so its tooltip closes
    await w.click("#search", ms=350, after=100)
    await w.type("rot13", cps=15)
    await w.wait(250)
    await w.dblclick(p.locator("#search-results li.operation").first, ms=350, after=200)
    await w.move(640, 900, 300); await w.wait(1800)
