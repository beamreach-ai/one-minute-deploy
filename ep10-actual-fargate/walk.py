# Walkthrough for ep.10: set the server password (throwaway), sign in, open the
# demo budget and change one number in it.
# Re-runnable: if the password is already set it starts at the sign-in screen.
PASSWORD = "throwaway1"                         # throwaway; the fields show dots

async def walk(w):
    p = w.page
    pw = p.locator("input[type=password]")
    async with w.cut():
        await pw.first.wait_for(timeout=90000); await w.wait(900)
        fresh = await pw.count() > 1                           # two fields: nobody has set a password yet
    if fresh:                                                  # first run: set the server password
        await w.click(pw.nth(0), ms=220, after=50); await w.type(PASSWORD, cps=34)
        await w.press("Tab", after=90); await w.type(PASSWORD, cps=34)
        await w.press("Enter", after=250)
        async with w.cut():
            await p.wait_for_url("**/login**", timeout=60000)
            await pw.first.wait_for(timeout=60000); await w.wait(500)
    await w.click(pw.nth(0), ms=180, after=50); await w.type(PASSWORD, cps=34)   # sign in
    await w.press("Enter", after=250)
    demo = p.get_by_role("button", name="Try the demo")
    async with w.cut():
        await demo.wait_for(timeout=60000); await w.wait(500)
    await w.click(demo, ms=260, after=60)
    async with w.cut():                                        # the demo budget is generated in the browser
        await p.get_by_text("Usual Expenses").first.wait_for(timeout=120000)
        await p.get_by_role("button", name="Take the tour").wait_for(timeout=30000)
        await w.wait(900)
    await w.wait(300)
    await w.click(p.get_by_role("button", name="Close").first, ms=240, after=250)   # dismiss the tour offer
    await w.click(p.get_by_text("400.00", exact=True).first, ms=240, after=150)     # Food: budget less
    await w.type("350", cps=12)
    await w.press("Enter", after=300)
    await w.move(400, 300, 220)
    await w.wait(1600)
