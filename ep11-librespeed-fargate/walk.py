# Walkthrough for ep.11: press Start and watch the gauges run against your own
# server. The reel shows the first seconds of the test as they happened; the
# rest of the run is cut and the finished result is only used for the opener.
#
# LibreSpeed prints the visitor's IP address under the title. That is personal
# data, so it is blurred (visibly) before the test starts; nothing else on the
# page is touched.
BLUR = """
#privacy-warning { color: transparent !important; text-shadow: 0 0 11px rgba(255,255,255,.85) !important; }
#privacy-warning span { text-shadow: none !important; }
"""

async def walk(w):
    p = w.page
    async with w.cut():
        await p.wait_for_selector("#start-button", timeout=60000)
        await p.add_style_tag(content=BLUR)
        await w.move(330, 400, 100)                            # this page animates heavily and pointer
        await w.wait(700)                                      # moves are slow: park near the button first
    t0 = w.now()
    await w.wait(350)
    await w.click("#start-button", ms=64, after=120)
    await w.move(272, 668, 64)                                 # off the button, below the gauges
    while w.now() - t0 < 8.6: await w.wait(100)                # the test, running, uncut
    async with w.cut():                                        # the rest of the run (about 20 s)
        await p.wait_for_function(
            "document.querySelector('#start-button').innerText.trim().toLowerCase() === 'restart'", timeout=150000)
        await w.wait(600)
    await w.move(300, 690, 64)                                 # finished result (the opener)
    await w.wait(2300)
