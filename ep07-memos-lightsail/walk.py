# Walkthrough for ep.07: on a fresh Memos the first visitor creates the admin
# account; then write a memo and save it.
# Re-runnable: if the account already exists (a second take against the same
# container) it signs in instead, off camera.
USER, PASSWORD = "demo", "throwaway-123"          # throwaway: the service is deleted after the recording
MEMO = "My notes, my own server #aws"

async def center(loc):                            # looked up off camera, so the pointer moves without a pause
    b = await loc.bounding_box(); return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2

async def shown(w):                               # after a cut: nudge the pointer so a fresh frame is recorded
    await w.move(w.x + 2, w.y, 40)

async def keys(w, text, delay=38):
    # Type in one browser call (steady pace even when the Mac is busy) and log
    # one key sound per character, spread over the time the typing really took.
    t0 = w.now(); await w.page.keyboard.type(text, delay=delay); t1 = w.now()
    for i, ch in enumerate(text):
        w.events.append({"t": round(t0 + (t1 - t0) * (i + 0.5) / len(text), 3), "kind": "space" if ch == " " else "key"})

async def walk(w):
    p = w.page
    async with w.cut():
        await p.wait_for_selector("input[type=password]", timeout=60000); await w.wait(600)
        fresh = "/auth/signup" in p.url
        if fresh:
            user = await center(p.locator("input[placeholder=Username]"))
            submit = await center(p.locator("button[type=submit]"))
        else:                                         # account exists already: sign in off camera
            await p.fill("input[placeholder=Username]", USER); await p.fill("input[type=password]", PASSWORD)
            await p.click("button[type=submit]")
    if fresh:                                         # first run: create the admin account
        await shown(w); await w.wait(250)
        await w.click(user, ms=110, after=60)
        await keys(w, USER, 60)
        await w.press("Tab", after=80)
        await keys(w, PASSWORD, 32)
        await w.click(submit, ms=120, after=60)
    async with w.cut():                               # the app loads; the first login opens a welcome guide: skip it
        await p.wait_for_selector(".memo-editor-root", timeout=30000); await w.wait(1500)
        skip = p.get_by_role("button", name="Skip")
        if await skip.count(): await skip.click(); await w.wait(700)
        editor = await center(p.locator(".memo-editor-root"))
        save = await center(p.get_by_role("button", name="Save"))
    await shown(w); await w.wait(250)
    await w.click(editor, ms=120, after=60)
    await keys(w, MEMO)
    await w.wait(250)
    await w.click(save, ms=120, after=100)
    await w.move(300, 520, 90)
    await w.wait(1500)
