#!/usr/bin/env python3
"""Run an episode for real and record it.

Reads <episode dir>/episode.py (the EP dict), runs every step's command in a
fresh <work>/run directory, and saves each command's output and wall time to
<work>/cap/. Then waits for the app to answer, and records the walkthrough
(<episode dir>/walk.py) against the live URL.

The site is left UP afterwards: run the episode's cleanup.sh when done.

Usage: AWS_PROFILE=<profile> capture.py <episode dir> <work dir> [--walk-only]
"""
import asyncio, os, runpy, shutil, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import walklib

def load_ep(ep_dir): return runpy.run_path(os.path.join(ep_dir, "episode.py"))["EP"]

def shell_of(step):
    if step.get("run"): return step["run"]
    return " ".join(l.strip().rstrip("\\").strip() for l in step["cmd"])

def main():
    ep_dir = os.path.abspath(sys.argv[1]); work = os.path.abspath(sys.argv[2]); walk_only = "--walk-only" in sys.argv
    EP = load_ep(ep_dir); run = os.path.join(work, "run"); cap = os.path.join(work, "cap")
    env = dict(os.environ, AWS_PAGER="", **EP.get("env", {}))
    os.makedirs(cap, exist_ok=True)
    if not walk_only:
        shutil.rmtree(run, ignore_errors=True); os.makedirs(run)
        for f in EP.get("files", []): shutil.copy(os.path.join(ep_dir, f), os.path.join(run, f))
        timings = []
        for i, step in enumerate(EP["steps"]):
            name = step.get("out") or "step%d" % (i + 1)
            if "edit" in step:
                e = step["edit"]; path = os.path.join(run, e["file"]); src = open(path).read()
                assert src.count(e["find"]) == 1, "edit target %r must occur exactly once in %s" % (e["find"], e["file"])
                open(path, "w").write(src.replace(e["find"], e["replace"])); print("edit  %s: %s -> %s" % (e["file"], e["find"], e["replace"]))
                continue
            cmd = shell_of(step); t0 = time.time()
            with open(os.path.join(cap, name + ".raw"), "wb") as out:
                rc = subprocess.run(["/bin/bash", "-c", cmd], cwd=os.path.join(run, step.get("cwd", "")), env=env,
                                    stdout=out, stderr=subprocess.STDOUT).returncode
            dt = time.time() - t0; timings.append("%s rc=%d %.1fs" % (name, rc, dt)); print(timings[-1], " $", cmd)
            if rc != 0:
                print(open(os.path.join(cap, name + ".raw"), errors="replace").read()[-2000:]); sys.exit("step failed: " + name)
        live = EP["live"]
        if live.get("url_cmd"):
            url = subprocess.run(["/bin/bash", "-c", live["url_cmd"]], cwd=run, env=env, capture_output=True, text=True).stdout.strip()
        else: url = live["url"]
        assert url.startswith("http"), "no URL: %r" % url
        open(os.path.join(cap, "url.raw"), "w").write(url + "\n")
        # readiness: time until the app first answers (part of the honest "live in ...")
        t0 = time.time(); ok = False; want = live.get("ready_status", (200,))
        while time.time() - t0 < live.get("ready_timeout", 600):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "one-minute-deploy"})
                import ssl; code = urllib.request.urlopen(req, timeout=8, context=ssl._create_unverified_context()).status
            except urllib.error.HTTPError as e: code = e.code
            except Exception: code = 0
            if code in want: ok = True; break
            time.sleep(3)
        if not ok: sys.exit("app never answered at " + url)
        timings.append("ready rc=0 %.1fs" % (time.time() - t0)); print(timings[-1], " ", url)
        open(os.path.join(cap, "timings.txt"), "w").write("\n".join(timings) + "\n")
    url = open(os.path.join(cap, "url.raw")).read().strip()
    wp = os.path.join(ep_dir, "walk.py")
    walk = runpy.run_path(wp)["walk"]
    asyncio.run(walklib.record(url, os.path.join(cap, "walk"), walk, width=EP.get("browser", {}).get("width", 540)))

if __name__ == "__main__":
    main()
