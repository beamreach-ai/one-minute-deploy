#!/usr/bin/env python3
# Simple-melody soundtracks for a 1-Minute Deploy reel, arranged to the reel's
# own beats (<work>/out/meta.json): a quiet tune under the terminal so the
# keyboard is audible, a flourish exactly on LIVE, a fuller second tune under
# the app demo, and a final chord landing on the outro. Every keystroke and
# click the renderer logged gets its own sound. The bar count under the
# terminal is picked per cut so each track stays near its own tempo. numpy only.
# Usage: music.py <work dir> [track ...]   (default: all five tracks)
#   -> <work>/audio/<track>.wav  (music + keys),  <work>/audio/tracks.json
import json, os, sys, wave
import numpy as np

WORK = os.path.abspath(sys.argv[1]); AUD = os.path.join(WORK, "audio")
META = json.load(open(os.path.join(WORK, "out", "meta.json")))
SR = 44100; DUR = META["dur"]; N = int(SR * DUR); M = META["marks"]
T_TERM, T_LIVE, T_GAME, T_CLEAN, T_OUTRO = M["term"], M["live"], M["game"], M.get("clean"), M["outro"]
rng = np.random.default_rng(11)

NAMES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def hz(name): return 440.0 * 2 ** ((12 * (int(name[-1]) + 1) + NAMES[name[:-1]] - 69) / 12)
def tt(n): return np.arange(n) / SR
def ar(n, a, r):
    e = np.ones(n); ai = max(1, min(n, int(a * SR))); ri = max(1, min(n, int(r * SR)))
    e[:ai] = np.linspace(0, 1, ai); e[n - ri:] *= np.linspace(1, 0, ri); return e
def place(buf, sig, start, amp=1.0):
    i = int(start * SR)
    if i < 0: sig = sig[-i:]; i = 0
    j = min(len(buf), i + len(sig))
    if j > i: buf[i:j] += sig[:j - i] * amp

# ---------------- instruments (f in Hz, dur in seconds) ----------------
def harm(f, n, weights):
    t = tt(n); s = np.zeros(n)
    for h, w in weights:
        if h * f < SR * 0.45: s += w * np.sin(2 * np.pi * h * f * t)
    return s
def pulse(f, dur, duty=0.25):                       # NES-style lead
    n = int(dur * SR); s = harm(f, n, [(h, 2 / (h * np.pi) * np.sin(np.pi * h * duty)) for h in range(1, 24)])
    e = ar(n, 0.004, 0.03); e *= 0.72 + 0.28 * np.exp(-tt(n) * 9); return s * e
def tri(f, dur):
    n = int(dur * SR); s = (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * f * tt(n))); return s * ar(n, 0.005, 0.04)
def musicbox(f, dur):
    n = int(max(dur, 1.5) * SR); t = tt(n)
    s = sum(w * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, w, d in
            [(1, 1.0, 2.6), (2.0, 0.32, 4.5), (3.01, 0.14, 7), (5.42, 0.07, 13)] if f * r < SR * 0.45)
    return s * ar(n, 0.002, 0.2)
def rhodes(f, dur):
    n = int(max(dur, 0.5) * SR + 0.25 * SR); t = tt(n); vib = 1 + 0.003 * np.sin(2 * np.pi * 4.6 * t)
    s = np.sin(2 * np.pi * f * t * vib) + 0.5 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3.2)
    s += 0.22 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 5) + 0.3 * np.sin(2 * np.pi * 7 * f * t) * np.exp(-t * 28)
    return s * np.exp(-t * 1.5) * ar(n, 0.004, 0.25) / 1.4
def saw(f, dur, bright=0.78, a=0.012, r=0.07):
    n = int(dur * SR); w = [(h, bright ** (h - 1) / h) for h in range(1, 18)]
    s = 0.5 * harm(f * 2 ** (6 / 1200), n, w) + 0.5 * harm(f * 2 ** (-6 / 1200), n, w); return s * ar(n, a, r)
def pad(f, dur): return saw(f, dur, bright=0.5, a=0.22, r=0.35)
def pluck(f, dur):                                   # nylon/ukulele-ish string
    n = int(max(dur, 0.9) * SR); t = tt(n)
    s = sum(np.sin(2 * np.pi * h * f * t) / h * np.exp(-t * (2.2 + 1.3 * h)) for h in range(1, 11) if h * f < SR * 0.45)
    return s * ar(n, 0.002, 0.1)
def whistle(f, dur):
    n = int(dur * SR); t = tt(n)
    fr = f * (1 - 0.035 * np.exp(-t / 0.035)) * (1 + 0.006 * np.sin(2 * np.pi * 5.4 * t) * np.clip(t / 0.25, 0, 1))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    breath = np.convolve(rng.standard_normal(n), np.ones(24) / 24, "same") * 0.25
    return (np.sin(ph) + 0.07 * np.sin(2 * ph) + breath) * ar(n, 0.05, 0.09)
def subbass(f, dur):
    n = int(dur * SR); t = tt(n)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.15 * np.sin(6 * np.pi * f * t)
    return s * ar(n, 0.008, 0.08) * (0.6 + 0.4 * np.exp(-t * 4))

def kick(amp=1.0, dur=.26):
    n = int(dur * SR); t = tt(n); f = 48 + 90 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11) * amp
def noise(dur, decay, amp, hp=True):
    n = int(dur * SR); x = rng.standard_normal(n)
    if hp: x = x - np.convolve(x, np.ones(6) / 6, "same")
    return x * np.exp(-tt(n) * decay) * amp
def snare(amp=.6):
    n = int(.19 * SR); t = tt(n)
    return (np.sin(2 * np.pi * 190 * t) * np.exp(-t * 22) * 0.5 + rng.standard_normal(n) * np.exp(-t * 24) * 0.7) * amp
def hat(amp=.25): return noise(.05, 80, amp)
def shaker(amp=.2):
    n = int(.09 * SR); t = tt(n); x = rng.standard_normal(n); x = x - np.convolve(x, np.ones(5) / 5, "same")
    return x * np.sin(np.pi * np.clip(t / 0.09, 0, 1)) ** 2 * amp
def clap(amp=.5):
    s = np.zeros(int(.2 * SR))
    for k, d in enumerate([0, .011, .023]): place(s, noise(.16, 30 if k == 2 else 90, 0.8), d)
    return s * amp
def crash(amp=.4): return noise(1.6, 3.2, amp)
def riser(dur, amp=.3):
    n = int(dur * SR); t = tt(n); e = (t / dur) ** 2
    return (np.sin(2 * np.pi * np.cumsum(np.linspace(300, 1500, n)) / SR) * 0.4 * e + noise(dur, 0, 1) * e * 0.5) * amp

# ---------------- sequencing ----------------
def parse(tokens, bpb):
    out = []; pos = 0.0
    for tok in tokens.split():
        name, d = tok.split(":"); d = float(d)
        if name != "r": out.append((pos, d, name))
        pos += d
    assert abs(pos - bpb) < 1e-6, (tokens, pos)
    return out
def lay(buf, tokens, t0, beat, inst, amp, bpb, swing=0.0, human=0.0, gate=0.95):
    for pos, d, name in parse(tokens, bpb):
        if abs((pos * 2) % 2 - 1) < 1e-6: pos += swing
        j = rng.normal(0, human) if human else 0.0
        place(buf, inst(hz(name), d * beat * gate), t0 + pos * beat + j, amp * (1 + (rng.normal(0, .06) if human else 0)))

CH = {'C': ('C3', ['C4', 'E4', 'G4']), 'G': ('G2', ['B3', 'D4', 'G4']), 'Am': ('A2', ['C4', 'E4', 'A4']),
      'F': ('F2', ['C4', 'F4', 'A4']), 'Em': ('E2', ['B3', 'E4', 'G4']), 'Dm': ('D3', ['D4', 'F4', 'A4']),
      'A#': ('A#2', ['D4', 'F4', 'A#4']), 'D': ('D3', ['D4', 'F#4', 'A4']),
      'Am7': ('A2', ['G3', 'C4', 'E4']), 'Dm7': ('D3', ['F3', 'A3', 'C4']), 'G7': ('G2', ['F3', 'B3', 'D4']),
      'Cmaj7': ('C3', ['E3', 'G3', 'B3']), 'Fmaj7': ('F2', ['E3', 'A3', 'C4']), 'Em7': ('E2', ['D3', 'G3', 'B3'])}

# Per-track accompaniment. lvl: 0 sparse (opening / cleanup), 1 terminal, 2 app demo.
def comp_chip(c, w, ch, t0, beat, lvl, bpb):
    bass, notes = CH[ch]
    for b in ([0, 2] if lvl < 2 else [0, 1, 2, 3]): place(c, tri(hz(bass), beat * .9), t0 + b * beat, .5)
    if lvl:
        step = beat / (2 if lvl == 1 else 4); k = 0
        while k * step < bpb * beat - 1e-6:
            place(w, pulse(hz(notes[k % 3]) * 2, step * .8, duty=.125), t0 + k * step, .09 if lvl == 1 else .11); k += 1
def drum_chip(c, t0, beat, lvl, bpb):
    if lvl == 1:
        for k in range(8): place(c, hat(.09), t0 + k * beat / 2)
    if lvl == 2:
        for b in range(4):
            place(c, kick(.75, .16) if b % 2 == 0 else noise(.1, 38, .34), t0 + b * beat)
            place(c, hat(.13), t0 + b * beat); place(c, hat(.1), t0 + (b + .5) * beat)

def comp_box(c, w, ch, t0, beat, lvl, bpb):          # oom-pah-pah
    bass, notes = CH[ch]
    place(c, musicbox(hz(bass) * 2, beat), t0, .34)
    if lvl:
        for b in (1, 2):
            for nm in notes[1:]: place(w, musicbox(hz(nm), beat), t0 + b * beat, .13 if lvl == 1 else .16)
def drum_box(c, t0, beat, lvl, bpb):
    if lvl == 2:
        place(c, kick(.4, .2), t0)
        for b in (1, 2): place(c, shaker(.12), t0 + b * beat)

def comp_lofi(c, w, ch, t0, beat, lvl, bpb):
    bass, notes = CH[ch]
    place(c, subbass(hz(bass), beat * 1.6), t0, .5); place(c, subbass(hz(bass), beat * .8), t0 + 2.5 * beat, .34)
    for nm in notes: place(w, rhodes(hz(nm), beat * 3), t0 + rng.uniform(0, .012), .2)
    if lvl:
        for nm in notes[1:]: place(w, rhodes(hz(nm), beat), t0 + 2.56 * beat, .11)
def drum_lofi(c, t0, beat, lvl, bpb):
    if lvl:
        a = .55 if lvl == 1 else .8
        place(c, kick(a), t0); place(c, kick(a * .7), t0 + 2.56 * beat)
        place(c, snare(a * .5), t0 + beat); place(c, snare(a * .5), t0 + 3 * beat)
        for k in range(8): place(c, hat(.08 if lvl == 1 else .12), t0 + (k / 2 + (.06 if k % 2 else 0)) * beat)

def comp_pop(c, w, ch, t0, beat, lvl, bpb):
    bass, notes = CH[ch]
    for nm in notes: place(w, pad(hz(nm), bpb * beat), t0, .1 if lvl < 2 else .13)
    if lvl < 2:
        for b in (0, 2): place(c, subbass(hz(bass), beat * 1.5), t0 + b * beat, .45)
    else:
        for k in range(8): place(c, subbass(hz(bass), beat * .42), t0 + k * beat / 2, .42 if k % 2 == 0 else .3)
    if lvl:
        seq = [0, 1, 2, 1, 0, 1, 2, 1]
        for k in range(8): place(w, pluck(hz(notes[seq[k]]) * 2, beat * .4), t0 + k * beat / 2, .1 if lvl == 1 else .12)
def drum_pop(c, t0, beat, lvl, bpb):
    if lvl == 1:
        for b in (0, 2): place(c, kick(.5), t0 + b * beat)
        for b in range(4): place(c, hat(.1), t0 + (b + .5) * beat)
    if lvl == 2:
        for b in range(4):
            place(c, kick(.85), t0 + b * beat); place(c, hat(.16), t0 + (b + .5) * beat)
            if b % 2: place(c, clap(.36), t0 + b * beat)

def comp_uke(c, w, ch, t0, beat, lvl, bpb):
    bass, notes = CH[ch]; strum = notes + [notes[0][:-1] + str(int(notes[0][-1]) + 1)]
    place(c, subbass(hz(bass) * 2, beat * 1.5), t0, .3)
    if lvl == 2: place(c, subbass(hz(bass) * 2, beat), t0 + 2 * beat, .26)
    pat = [(0, 1, .2)] if lvl == 0 else [(0, 1, .2), (1, 1, .15), (1.56, -1, .1), (2.56, -1, .12), (3, 1, .16), (3.56, -1, .1)]
    for pos, dirn, a in pat:
        for k, nm in enumerate(strum if dirn > 0 else strum[::-1]):
            place(w, pluck(hz(nm) * 2, beat * .9), t0 + pos * beat + k * .013, a)
def drum_uke(c, t0, beat, lvl, bpb):
    if lvl:
        for k in range(8): place(c, shaker(.1 if k % 2 == 0 else .15), t0 + (k / 2 + (.06 if k % 2 else 0)) * beat)
    if lvl == 2:
        for b in (0, 2): place(c, kick(.6), t0 + b * beat)
        for b in (1, 3): place(c, clap(.3), t0 + b * beat)

TRACKS = {
 # 127 bpm 4/4, C major — bouncy 8-bit
 "1_chiptune": dict(dom='G', bpb=4, bpm=124, quant=4, lead=pulse, leadA=.3, leadB=.3, comp=comp_chip, drum=drum_chip, swing=0, human=0,
    chA=['C', 'G', 'Am', 'F'], chB=['F', 'G', 'Em', 'Am', 'F', 'G', 'C', 'C'], final='C', top='C6',
    flo=['C5', 'E5', 'G5', 'C6', 'E6', 'G6', 'C7'],
    melA=["E5:.5 E5:.5 G5:1 E5:.5 D5:.5 C5:1", "D5:.5 D5:.5 G5:1 D5:.5 B4:.5 D5:1",
          "C5:.5 C5:.5 E5:1 A5:1 G5:.5 E5:.5", "F5:1 E5:.5 D5:.5 C5:2",
          "E5:.5 E5:.5 G5:1 E5:.5 D5:.5 C5:1", "D5:.5 D5:.5 G5:1 D5:.5 B4:.5 D5:1",
          "C5:.5 C5:.5 E5:1 A5:1 G5:.5 E5:.5", "F5:.5 A5:.5 G5:1 D5:1 G5:1"],
    melB=["A5:.5 C6:.5 A5:.5 F5:.5 A5:1 C6:1", "B5:.5 D6:.5 B5:.5 G5:.5 B5:1 D6:1",
          "G5:.5 B5:.5 E6:1 D6:.5 B5:.5 G5:1", "A5:1 C6:1 E6:2",
          "A5:.5 C6:.5 A5:.5 F5:.5 A5:1 C6:1", "B5:.5 D6:.5 B5:.5 G5:.5 B5:1 D6:1",
          "E6:.5 D6:.5 C6:1 G5:1 E5:1", "C6:.5 G5:.5 C6:3"]),
 # 143 bpm 3/4, F major — music-box waltz
 "2_musicbox": dict(dom='C', bpb=3, bpm=140, quant=4, lead=musicbox, leadA=.42, leadB=.46, comp=comp_box, drum=drum_box, swing=0, human=.004,
    chA=['F', 'C', 'Dm', 'A#', 'F', 'C', 'A#', 'C'], chB=['A#', 'F', 'C', 'F'], final='F', top='F6',
    flo=['F5', 'A5', 'C6', 'F6', 'A6', 'C7', 'F7'],
    melA=["A5:1 C6:1 F6:1", "E6:2 C6:1", "F5:1 A5:1 D6:1", "D6:1.5 C6:.5 A#5:1",
          "A5:1 C6:1 F6:1", "G6:2 E6:1", "F6:1 D6:1 A#5:1", "C6:3"],
    melB=["D6:.5 F6:.5 D6:1 A#5:1", "C6:.5 F6:.5 C6:1 A5:1", "E6:.5 G6:.5 E6:1 C6:1", "F6:2 A5:1",
          "D6:.5 F6:.5 D6:1 A#5:1", "C6:.5 F6:.5 C6:1 A5:1", "G6:1 E6:1 C6:1", "F6:3"]),
 # 96 bpm 4/4, A minor — lo-fi electric piano
 "3_lofi": dict(dom='G7', bpb=4, bpm=90, quant=2, lead=rhodes, leadA=.5, leadB=.52, comp=comp_lofi, drum=drum_lofi, swing=.07, human=.008,
    chA=['Am7', 'Dm7', 'G7', 'Cmaj7'], chB=['Fmaj7', 'G7', 'Em7', 'Am7'], final='Cmaj7', top='E5', hiss=.006,
    flo=['C5', 'E5', 'G5', 'B5', 'D6', 'G6'],
    melA=["r:.5 E5:.5 G5:1 E5:.5 D5:.5 C5:1", "D5:1.5 F5:.5 A5:2", "r:.5 D5:.5 G5:1 F5:.5 D5:.5 B4:1", "E5:1 D5:.5 C5:.5 B4:2",
          "r:.5 E5:.5 G5:1 E5:.5 D5:.5 C5:1", "D5:1.5 F5:.5 A5:2", "r:.5 D5:.5 G5:1 F5:.5 D5:.5 B4:1", "C5:1 E5:1 G5:2"],
    melB=["A5:.5 G5:.5 A5:1 C6:1 A5:1", "B5:.5 A5:.5 B5:1 D6:1 B5:1", "G5:1 E5:.5 G5:.5 B5:1 G5:1", "A5:1 E5:1 A5:2",
          "A5:.5 G5:.5 A5:1 C6:1 A5:1", "B5:.5 A5:.5 B5:1 D6:1 B5:1", "G5:1 E5:.5 G5:.5 B5:1 G5:1", "C6:1 B5:.5 A5:.5 E5:2"]),
 # 127 bpm 4/4, A minor -> C — synth-pop
 "4_synthpop": dict(dom='G', bpb=4, bpm=124, quant=4, lead=saw, leadA=.26, leadB=.3, comp=comp_pop, drum=drum_pop, swing=0, human=0,
    chA=['Am', 'F', 'C', 'G'], chB=['F', 'G', 'Am', 'C', 'F', 'G', 'Am', 'Am'], final='C', top='C6',
    flo=['A4', 'C5', 'E5', 'A5', 'C6', 'E6', 'A6'],
    melA=["E5:1.5 D5:.5 C5:1 A4:1", "F5:1.5 E5:.5 C5:2", "E5:1.5 D5:.5 C5:1 G4:1", "D5:1.5 E5:.5 D5:1 B4:1",
          "E5:1.5 D5:.5 C5:1 A4:1", "F5:1.5 E5:.5 C5:2", "E5:1.5 D5:.5 C5:1 G4:1", "D5:1 E5:1 G5:2"],
    melB=["A5:.5 A5:.5 C6:1 A5:.5 G5:.5 F5:1", "B5:.5 B5:.5 D6:1 B5:.5 A5:.5 G5:1",
          "C6:.5 C6:.5 E6:1 C6:.5 B5:.5 A5:1", "G5:1 C6:1 E6:2",
          "A5:.5 A5:.5 C6:1 A5:.5 G5:.5 F5:1", "B5:.5 B5:.5 D6:1 B5:.5 A5:.5 G5:1",
          "C6:.5 C6:.5 E6:1 C6:.5 B5:.5 A5:1", "E6:1 D6:.5 C6:.5 A5:2"]),
 # 96 bpm 4/4, G major — ukulele strum + whistle
 "5_ukulele": dict(dom='D', bpb=4, bpm=96, quant=2, lead=whistle, leadA=.3, leadB=.32, comp=comp_uke, drum=drum_uke, swing=.06, human=.006,
    chA=['G', 'Em', 'C', 'D'], chB=['C', 'G', 'D', 'G'], final='G', top='G6', flo_inst=pluck,
    flo=['G5', 'B5', 'D6', 'G6', 'B6', 'D7'],
    melA=["B5:1 D6:1 B5:.5 A5:.5 G5:1", "E5:1 G5:1 B5:2", "C6:1 E6:1 C6:.5 B5:.5 A5:1", "A5:1 B5:1 D6:2",
          "B5:1 D6:1 B5:.5 A5:.5 G5:1", "E5:1 G5:1 B5:2", "C6:1 E6:1 C6:.5 B5:.5 A5:1", "A5:1 F#5:1 D5:1 r:1"],
    melB=["E6:.5 D6:.5 C6:1 E6:1 G6:1", "D6:.5 C6:.5 B5:1 D6:1 G6:1", "F#6:.5 E6:.5 D6:1 A5:1 D6:1", "B5:1 D6:1 G6:2",
          "E6:.5 D6:.5 C6:1 E6:1 G6:1", "D6:.5 C6:.5 B5:1 D6:1 G6:1", "F#6:.5 E6:.5 D6:1 A5:1 D6:1", "G6:1 D6:1 G5:2"]),
}

def arrange(tr):
    c = np.zeros(N); w = np.zeros(N)                 # centre bus, wide bus
    bpb = tr["bpb"]; q = tr["quant"]; L0 = bpb * 60.0 / tr["bpm"]
    barsA = max(q, q * round((T_LIVE - T_TERM) / (L0 * q))); L = (T_LIVE - T_TERM) / barsA; beat = L / bpb
    nB = barsA + max(1, round((T_GAME - T_LIVE) / L))
    nE = int((T_OUTRO - T_TERM) / L + 0.12)      # last full bar line at/before the outro
    nC = nE if T_CLEAN is None else min(nE, int(np.ceil((T_CLEAN - 0.4 - T_TERM) / L)))
    bt = lambda n: T_TERM + n * L
    lead = tr["lead"]; kw = dict(bpb=bpb, swing=tr["swing"], human=tr["human"]); flo_i = tr.get("flo_inst", lead)
    pa = lambda n: (n - barsA) % 8             # phrase position: the last bar before LIVE is the turnaround
    bass0, notes0 = CH[tr["chA"][pa(0) % len(tr["chA"])]]
    # intro: a sparkle on the hook, a held chord on the title, two pickup notes
    for k, nm in enumerate(tr["flo"][:5]): place(c, flo_i(hz(nm), .3), 0.06 + k * .1, tr["leadA"] * .9)
    for nm in notes0: place(w, tr["lead"](hz(nm), 1.4) if lead in (musicbox, rhodes) else pad(hz(nm), 1.5), 1.0, .16)
    first = parse(tr["melA"][pa(0) % len(tr["melA"])], bpb)[0][2]
    place(c, lead(hz(first) * 2 ** (-5 / 12), beat * .45), T_TERM - beat, tr["leadA"] * .8)
    place(c, lead(hz(first) * 2 ** (-2 / 12), beat * .45), T_TERM - beat / 2, tr["leadA"] * .8)
    # A: the terminal
    for n in range(barsA):
        lvl = 0 if n < max(1, barsA // 4) else 1
        lay(c, tr["melA"][pa(n) % len(tr["melA"])], bt(n), beat, lead, tr["leadA"], **kw)
        tr["comp"](c, w, tr["chA"][pa(n) % len(tr["chA"])], bt(n), beat, lvl, bpb)
        tr["drum"](c, bt(n), beat, lvl, bpb)
    place(c, riser(min(2.4, L * 1.2), .22), T_LIVE - min(2.4, L * 1.2))
    # LIVE: chord + rising arpeggio, exactly on the banner
    bassF, notesF = CH[tr["final"]]
    place(c, crash(.3), T_LIVE); place(c, kick(.9), T_LIVE); place(c, subbass(hz(bassF), (nB - barsA) * L), T_LIVE, .5)
    for nm in notesF: place(w, pad(hz(nm), (nB - barsA) * L), T_LIVE, .2)
    for k, nm in enumerate(tr["flo"]): place(c, flo_i(hz(nm), .5), T_LIVE + k * .085, tr["leadB"] * 1.05)
    for k, nm in enumerate(tr["flo"][::-1][:4]): place(c, flo_i(hz(nm), .4), bt(nB) - beat * 2 + k * beat / 2, tr["leadB"] * .7)
    # B: the app demo
    for n in range(nB, nC):
        k = n - nB
        lay(c, tr["melB"][k % len(tr["melB"])], bt(n), beat, lead, tr["leadB"], **kw)
        tr["comp"](c, w, tr["chB"][k % len(tr["chB"])], bt(n), beat, 2, bpb)
        tr["drum"](c, bt(n), beat, 2, bpb)
    # cleanup: thin reprise of A
    for n in range(nC, nE):
        k = n - nC
        lay(c, tr["melA"][k % len(tr["melA"])], bt(n), beat, lead, tr["leadA"] * .9, **kw)
        tr["comp"](c, w, tr["chA"][k % len(tr["chA"])], bt(n), beat, 0, bpb)
    # the final chord lands exactly on the outro; any gap after the last full
    # bar is a held dominant with a short run-up (a stop-time ending)
    te = max(T_OUTRO, bt(nE)); gap = te - bt(nE); ring = max(1.2, DUR - te)
    if gap > 0.3:
        bassD, notesD = CH[tr["dom"]]
        place(c, subbass(hz(bassD), gap), bt(nE), .45); place(c, kick(.7), bt(nE))
        for nm in notesD: place(w, (pad if lead not in (musicbox, rhodes) else lead)(hz(nm), gap), bt(nE), .2)
        run = [notesD[0], notesD[1], notesD[2]]; step = min(.16, gap / 4)
        for k, nm in enumerate(run): place(c, flo_i(hz(nm) * 2, step * 1.5), te - (3 - k) * step, tr["leadB"] * .8)
    place(c, subbass(hz(bassF), ring), te, .5); place(c, kick(.6), te)
    for nm in notesF: place(w, (pad if lead not in (musicbox, rhodes) else lead)(hz(nm), ring), te, .2)
    for k, nm in enumerate([tr["flo"][0], tr["flo"][2], tr["top"]]): place(c, flo_i(hz(nm), ring), te + k * .09, tr["leadB"] * .9)
    if tr.get("hiss"): c += rng.standard_normal(N) * tr["hiss"]
    # stereo: wide bus gets a short Haas delay on the right
    d = int(.011 * SR); wr = np.concatenate([np.zeros(d), w[:-d]])
    st = np.stack([c + w, c + wr], axis=1)
    # level ride: quiet under typing, up for the payoff and the demo
    pts = [(0, .85), (T_TERM - .2, .85), (T_TERM + .3, .6), (T_LIVE - .5, .62), (T_LIVE, 1.0), (bt(nC) - .2, 1.0)]
    if nE > nC: pts += [(bt(nC) + .4, .62), (te - .1, .66)]
    pts += [(te, .95), (DUR - .7, .95), (DUR, 0.0)]
    g = np.interp(np.arange(N) / SR, [p[0] for p in pts], [p[1] for p in pts])
    i0, i1 = int(bt(nB) * SR), int(bt(nC) * SR)
    st = st / (np.sqrt(np.mean(st[i0:i1] ** 2)) + 1e-9) * 0.15       # same demo-section loudness for every track
    info = dict(bpm=round(60 / beat, 1), bar=round(L, 3), B=round(bt(nB), 2), thin=round(bt(nC), 2), final=round(te, 2))
    info["bars"] = barsA; info["bpm0"] = tr["bpm"]
    return st * g[:, None], info

# ---------------- keyboard ----------------
def keysound(kind):
    n = int(.16 * SR); t = tt(n); s = np.zeros(n)
    if kind == "click":                                               # mouse button: two short bright ticks
        for d, a in ((0, .5), (.07, .3)):
            k = int(.03 * SR); u = tt(k); x = rng.standard_normal(k); x = x - np.convolve(x, np.ones(3) / 3, "same")
            place(s, (x * np.exp(-u * 700) + np.sin(2 * np.pi * 3100 * u) * np.exp(-u * 420) * .5) * a, d)
        return s
    low = {"space": 135, "enter": 115, "back": 205, "arrow": 230}.get(kind, rng.uniform(190, 300))
    amp = {"space": 1.15, "enter": 1.35, "arrow": .7}.get(kind, 1.0) * rng.uniform(.8, 1.1)
    mid = rng.uniform(1300, 2400)
    def hit(a):
        m = int(.06 * SR); u = tt(m); x = rng.standard_normal(m); x = x - np.convolve(x, np.ones(4) / 4, "same")
        return (x * np.exp(-u * 380) * .9 + np.sin(2 * np.pi * low * u) * np.exp(-u * 55) * .8
                + np.sin(2 * np.pi * mid * u) * np.exp(-u * 170) * .35) * a
    place(s, hit(1.0), 0)                                             # bottom-out
    place(s, hit(.38), rng.uniform(.065, .1) + (.03 if kind in ("space", "enter") else 0))   # release
    if kind == "enter": place(s, np.sin(2 * np.pi * 82 * t) * np.exp(-t * 30) * .5, 0)
    return s * amp
def keys_bus():
    st = np.zeros((N, 2))
    for t0, kind in META["keys"]:
        s = keysound(kind); pan = rng.uniform(-.18, .18)
        place(st[:, 0], s, t0, .21 * (1 - pan)); place(st[:, 1], s, t0, .21 * (1 + pan))
    return st

def write_wav(path, st):
    pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())

if __name__ == "__main__":
    os.makedirs(AUD, exist_ok=True)
    want = sys.argv[2:] or list(TRACKS)
    kb = keys_bus(); infos = {}
    for name in want:
        mus, info = arrange(TRACKS[name]); infos[name] = info
        mix = np.tanh((mus + kb) * 1.6) / np.tanh(1.6) * 0.89         # soft limiter
        write_wav(os.path.join(AUD, name + ".wav"), mix)
        print("%-12s %5.1f bpm, %2d bars to LIVE  demo@%.2f final@%.2f  %d key/click sounds  peak %.2f" % (
            name, info["bpm"], info["bars"], info["B"], info["final"], len(META["keys"]), np.max(np.abs(mix))))
    json.dump(infos, open(os.path.join(AUD, "tracks.json"), "w"), indent=1)
