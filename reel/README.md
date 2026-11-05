# Reel tooling

One episode file drives everything: the real deploy, the recording of the app,
and the video. What is on screen is what was run.

```
capture.py <episode dir> <work dir>   run the steps for real, record output + timings, record the walkthrough
build.py   <episode dir> <work dir>   picture -> soundtrack -> <work>/reels/<slug>.mp4 (+ out/sheet.png)
review.py  <data root>                one review page for every built episode
```

`<work dir>` is scratch space outside the repo (captures and frames are big).
Needs Python 3 with `numpy`, `pillow`, `playwright` (+ `playwright install
chromium`) and `ffmpeg`. Fonts and the editor screen assume macOS.

## An episode folder

```
epNN-<app>-<target>/
  episode.py     the EP dict (below)
  walk.py        async def walk(w): the on-camera tour of the live app
  <template>     whatever the deploy needs (CloudFormation template, JSON, ...)
  cleanup.sh     deletes everything the episode created, waits until it is gone
  README.md      the commands for people following along
```

## episode.py

```python
EP = {
    "num": 1, "slug": "ep01_2048_s3",
    "title": {"app": "2048", "sub": "the game",            # title slide: app, small subtitle,
              "target": "S3 bucket",                        #   "-> target",
              "how": "with CloudFormation · AWS"},          #   one line on how
    "credit": "app by gabrielecirulli",                     # closing slide
    "term_title": "aws: public-demo · us-west-1 — zsh",     # terminal title bar (default shown)
    "env": {},                                              # extra env for the commands, e.g. AWS_REGION
    "files": ["site.yaml"],                                 # copied from the episode folder into the run dir
    "steps": [ ... ],
    "live": {"url_cmd": "<shell that prints the URL>"},     # or {"url": "http://..."}
    "browser": {"open": "open the bucket's public URL",     # caption while the URL is pasted
                "live": "it's live — and it plays",         # caption over the walkthrough
                "seconds": 8, "start": 0.0,                 # how much of the walkthrough to show, from where
                "hook_at": 10.5,                            # the 1 s teaser that opens the reel starts here
                "width": 540},                              # CSS px the app is rendered at (frame is always 1080x1460)
}
```

`live` also takes `ready_status` (default `(200,)`) and `ready_timeout`
(seconds, default 600): after the last step capture.py polls the URL until the
app answers, and that wait counts in the "LIVE in ..." time.

### Steps

Each step is typed into the terminal, then its real output is replayed.

| key | meaning |
|-----|---------|
| `caption` | text above the terminal, shown as `// N · caption` |
| `cmd` | list of lines exactly as typed; continue a line with a trailing `\`; **max 49 characters per line** |
| `run` | the shell string actually executed, when it must differ from `cmd` (default: the `cmd` lines joined). Only for flags that change output format, e.g. `git clone --progress`. Never to do something different. |
| `out` | name for the capture file `cap/<out>.raw` and the timing entry (default `stepN`) |
| `cwd` | sub-directory of the run dir to run in |
| `edit` | `{"file", "find", "replace"}`: the step is a `nano <file>` edit. `find` must occur once and end its line; capture.py applies the same edit to the real file. `cmd` should be `["nano <file>"]`. |
| `progress` | collapse `\r` progress counters to their last value |
| `filter` | regex; only its matches are shown as output lines |
| `head` / `tail` / `max_lines` | trim the output |
| `rules` | `[[substring, color]]`, first match colours the line: `txt dim cyan green amber red` |
| `frames` | how long the output takes to appear (frames at 30 fps, before the 1.8x speed-up) |
| `wait` | `True`/`False` to force or forbid the fast-forward badge (default: on when the step really took 8 s or more) |
| `wrap` | word-wrap long output lines instead of clipping them |
| `hide_output` | show no output |

A step that really took a while is shown compressed with a
`>> fast-forward · real time m:ss` badge counting up to the measured time.
Twelve-digit numbers (AWS account ids) are masked in all output.

Keep the terminal short: the whole section should land under about 20 s
(render.py prints it and warns above 22 s). That means roughly five steps and
250 typed characters.

## walk.py

```python
async def walk(w):
    async with w.cut():                 # anything in here is dropped from the reel (loads, waits)
        await w.page.wait_for_selector("#app")
    await w.click("#new")               # pointer glides there, clicks (selector, Locator or (x, y))
    await w.type("hello")               # one audible key at a time, into whatever has focus
    await w.press("Enter")
    await w.dblclick(locator); await w.drag(x1, y1, x2, y2); await w.scroll(400); await w.move(x, y)
    await w.cursor(False)               # hide the pointer for keyboard-only demos
    await w.wait(800)
```

`w.page` is the Playwright page for anything else. Every click and key press is
logged and gets a sound in the reel. Aim for about 8 s of kept action that shows
the app doing its main thing; re-record with `capture.py ... --walk-only` while
the site is up.

## Soundtrack

`music.py` writes five simple-melody tracks arranged to the reel's own timing.
`build.py` picks one per reel from a shuffled bag (five consecutive episodes get
five different tracks; `--track <name>` overrides) and levels every reel to
-14 LUFS.
