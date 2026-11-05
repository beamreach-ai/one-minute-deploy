# Walkthrough for ep.09: create the admin account (throwaway), add an HTTP
# monitor for https://example.com, and watch the first check come back "Up".
# Re-runnable: if the admin already exists it logs in off camera instead.
USER, PASSWORD = "demo", "throwaway1"           # throwaway; the fields show dots

async def walk(w):
    p = w.page
    async with w.cut():
        await p.wait_for_selector("#floatingInput", timeout=60000)
        fresh = "/setup" in p.url
        if not fresh:                                          # already set up: log in, not shown
            await p.fill("#floatingInput", USER); await p.fill("#floatingPassword", PASSWORD)
            await p.click("button[type=submit]")
        else: await w.wait(400)
    if fresh:                                                  # first run: create the admin
        await w.click("#floatingInput", ms=200, after=50); await w.type(USER, cps=22)
        await w.press("Tab", after=90); await w.type(PASSWORD, cps=40)
        await w.press("Tab", after=90); await w.type(PASSWORD, cps=40)
        await w.press("Enter", after=300)
    async with w.cut():
        await p.wait_for_url("**/dashboard**", timeout=60000)
        await p.wait_for_selector("a.nav-link[href='/add']", timeout=30000)
        await p.locator(".Vue-Toastification__toast").first.wait_for(state="detached", timeout=20000)
        await w.wait(300)
    await w.click("a.nav-link[href='/add']", ms=200, after=80)
    async with w.cut():
        await p.wait_for_selector("#url", timeout=30000); await w.wait(400)
    await w.click("#url", ms=200, after=50)
    await w.type("example.com", cps=30)
    await w.press("Enter", after=100)
    await p.wait_for_url("**/dashboard/*", timeout=60000)      # saved: the page shows "Unknown"
    await w.move(445, 250, 180)
    await w.wait(300)
    async with w.cut():                                        # the first check is on its way
        await p.locator(".badge", has_text="Up").first.wait_for(timeout=90000)
    await w.wait(2000)
