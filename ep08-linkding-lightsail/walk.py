# Walkthrough for ep.08: log in as the user the deployment created, add a
# bookmark (linkding fetches the page title by itself), and see it in the list.
# Re-runnable: logging in always works; a second take just edits the same bookmark.
USER, PASSWORD = "demo", "throwaway-123"          # throwaway: the service is deleted after the recording
LINK = "https://github.com/sissbruecker/linkding"

async def center(loc):                            # looked up off camera, so the pointer moves without a pause
    b = await loc.bounding_box(); return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2

async def shown(w):                               # after a cut: nudge the pointer so a fresh frame is recorded
    await w.move(w.x + 2, w.y, 40)

async def keys(w, text, delay=34):
    # Type in one browser call (steady pace even when the Mac is busy) and log
    # one key sound per character, spread over the time the typing really took.
    t0 = w.now(); await w.page.keyboard.type(text, delay=delay); t1 = w.now()
    for i, ch in enumerate(text):
        w.events.append({"t": round(t0 + (t1 - t0) * (i + 0.5) / len(text), 3), "kind": "space" if ch == " " else "key"})

async def walk(w):
    p = w.page
    async with w.cut():
        await p.wait_for_selector("input[name=username]", timeout=60000); await w.wait(500)
        await p.focus("input[name=username]")
    await shown(w); await w.wait(250)
    await keys(w, USER, 60)                           # the login form: user, Tab, password, Enter
    await w.press("Tab", after=80)
    await keys(w, PASSWORD, 32)
    await w.press("Enter", after=60)
    async with w.cut():                               # the (empty) bookmark list loads
        await p.wait_for_selector("input[name=q]", timeout=30000); await w.wait(700)
        add = await center(p.locator("a[href='/bookmarks/new']:visible").first)
    await shown(w); await w.wait(350)
    await w.click(add, ms=120, after=60)
    async with w.cut():                               # the form loads, the URL field has focus
        await p.wait_for_selector("#id_url", timeout=30000); await w.wait(600)
    await shown(w); await w.wait(150)
    await keys(w, LINK)
    async with w.cut():                               # linkding looks the page up and fills in the title
        await p.wait_for_function("document.querySelector('#id_title').value.length > 0", timeout=20000)
        await w.wait(400)
        save = p.locator("input[type=submit][value=Save]")
        await save.scroll_into_view_if_needed(); save = await center(save)
    await shown(w); await w.wait(500)
    await w.click(save, ms=130, after=60)
    async with w.cut():                               # back to the list
        await p.wait_for_selector("a[href='%s']" % LINK, timeout=30000); await w.wait(600)
    await w.move(300, 500, 90)
    await w.wait(1500)
