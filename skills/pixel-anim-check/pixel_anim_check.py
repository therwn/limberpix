"""Pixel-art animation check: finds the faults that make a sprite animation look broken, before anyone sees it.

    python pixel_anim_check.py --loop idle=idle.png --loop move=walk.png --frame 32 [options]
    python pixel_anim_check.py --selftest
    python pixel_anim_check.py --help

A loop is a horizontal sprite strip, a folder of frame PNGs, or a GIF. Every loop of a creature must have frames of
one size, the figure in place (not trimmed per frame). A strip is cut by --frame (one frame's width) or --frames (how
many frames it holds); with neither, its frames are taken as square, and a strip whose width is not a whole number
of its height is refused. A folder is read in file-name order: zero-pad the numbers (f00.png, f01.png, ...). A GIF
is read at its own timing: each image is held for its duration at --fps (an image of 130 ms at 30 fps is 4 frames),
since exporters store a held pose as one image with a longer duration. Colours are #rrggbb, any case, the #
optional. Options:
  --frame W           a strip's frame width in px          --frames N   how many frames each strip holds
  --eye #rrggbb       the eye's colour: checked on every frame, the head round it must move (frozen), its row track
                      must not tick (tick), and the face round it must keep its shape (reshape)
  --flier             it flies: its shadow (--shadow colours, the bottom row) must not slide; no feet check; its body
                      height track is read for ticks; its idle wing stroke is judged against its move (shallow)
  --facing right|left which way the head faces (default right): where the face window of reshape lies
  --ink #hex,...      the outline colours (default: every colour darker than lightness 40)
  --shadow #hex,...   a flier's ground shadow colours
  --effects #hex,...  colours of effects drawn apart from the figure on purpose (sparks, rings, auras)
  --allow loop=N      pieces up to N px may sit apart from the figure in that loop (a thrown coin)
  --glows-eye loop    the eye is recoloured by a glow in that loop (not checked there)
  --idle NAME --move NAME   which loops are the rest and the travel loop (default idle, move)
  --legless           it crawls without legs (a snake, a slug): no body rise asked of its move; hop judges every loop
  --out DIR --fps N   where the contact sheet and the GIF go (default .); the rate the game plays them, frames a
                      second, a decimal allowed (default 30: used by the GIF, choppy and snap)
  --name NAME         the stem of the written files (default anim)
Exit code: 0 no fault, 1 one fault or more, 2 a usage error (a bad option, a missing file, a strip that does not cut).
Frame numbers in the output are 0-based: move[3] is the move's fourth frame; "frame k" in a jump or a snap is the
change from frame k to the next.
Faults (each a line "kind: ..."):
  size     frames differ in size            empty    a frame with nothing drawn
  apart    a piece apart from the figure    eye      the eye missing on a frame
  outline  coloured edge pixels with no ink round them (an open contour)
  ground   a walker's feet leave one ground line in a loop other than the move; a flier's shadow slides
  jump     a change between two frames over JUMP times the loop's mean, or one frame knocked sideways
  still    the move changes under STILL of the figure a frame
  shimmer  pixels flipping to another tone for one frame and back, often (texture crawling); a stroke's turning
           frames, tones too alike to tell apart (FAINT), and a tone stepping monotonically along a moving edge
           (a sub-pixel in-between) are not counted
  frozen   the head (round the eye) hardly moves against the body in the idle or the move: a mask on a living body
  stiff    a walker's body never rises or falls in the move (the top of its middle third holds to under STIFF px):
           legs stepping under a board
  choppy   a continuous loop updating fewer than CHOPPY_RATE times a second, or one update dropped (a hold twice the
           usual of 3+ frames): read as a dropped frame rate (--fps: the rate the game plays it at)
  uneven   the holds between a loop's moves jump in turn (1 frame, then 3, then 1): the motion stutters though
           the rate is the same (an idle's one long rest, and ease lengthening the holds at a turn, are on purpose)
  lurch    a held loop whose moves alternate big and small (a whole-body bob after a leg's small step, frames held
           between): a hitch each beat; with something moving on every frame the bob reads as a gait
  snap     an idle stops dead (a third of a second or more) and then changes a quarter of the figure in one step
  tick     a whole-pixel level is left and regained within a few frames: the eye's row in the idle, or a flier's
           whole-body height in its idle or move (a lift peaking just over half a pixel)
  hop      a grounded body (any idle but a flier's; every loop of a --legless body) lifts off its contact row
  vanish   a big piece switches off while the rest of the figure is nearly still, and stays gone (a far wing hidden
           at the turn of its stroke)
  shallow  a flier's idle moves only the upper half of the figure, where its move beats the whole wing
  reshape  the face, aligned on itself, changes its silhouette and ink lines between poses in the idle (a sheet
           redrawing the head in every cell)
Warnings (lines "warn: ...", not faults): the eye tick and reshape in loops other than the idle (an action may jump or
open its jaw on purpose; look at them).
Writes <out>/<name>_check.png (each distinct pose zoomed, at most 12 a loop plus any a fault names, labelled with the
frames it holds, "4-7", and under it the pixels changed from the one before, in red; the poses a fault names are
outlined in red) and <out>/<name>_check.gif
(the loops side by side, at --fps). Look at both: the numbers do not see likeness or taste.
--selftest draws a small walker and flier, checks they pass, then breaks them on purpose in every way above and
checks each break is caught. Run it after changing this file.

The thresholds of choppy, snap, tick, hop, vanish, shallow and reshape were fitted to a private calibration set (39
animated creatures, with 15 accept or reject judgements on them by one reviewer; not included), with the margins
stated in each function. No source gives a pixel threshold for judder: rerun the check on every animation you have
accepted whenever a threshold changes."""
import math
import os
import re
import statistics
import sys

import numpy as np
from PIL import Image, ImageDraw

JUMP, STILL, SHIMMER, FROZEN, FAINT, STIFF = 3.2, 0.015, 0.03, 0.12, 10, 0.5
MOVE_MIN, CADENCE_STEP, LURCH = 0.02, 0.08, 3.0          # uneven and lurch (unchanged)
CHOPPY_RATE, MOVE_EPS = 10.0, 0.002                      # choppy: updates a second; a move is over MOVE_EPS of A
SNAP_STEP, SNAP_STILL = 0.25, 0.02                       # snap: the step out of a dead stop; what counts as still
TICK_DUTY = 0.18                                         # tick: the shortest excursion against its share of the loop
HOP_LIFT, HOP_SHARE, HOP_STEP = 0.5, 0.6, 0.3            # hop: contact kept; rigid share of a big step; big step
VANISH_R, VANISH_MIN, VANISH_HOLD, VANISH_R4 = 2, 8, 3, 1.1
SHALLOW, SHALLOW_ROWS, SHALLOW_PX = 0.3, 0.8, 0.6
RESHAPE = 0.10


def hexrgb(v):
    return int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16)


def lum_hex(v):
    r, g, b = hexrgb(v)
    return 0.299 * r + 0.587 * g + 0.114 * b


class Spec:
    """What the check knows of a creature. Pixels are any hashable colour key; lum and rgb read one (default: hex)."""

    def __init__(self, ink=None, shadow=(), effects=(), eye=None, flier=False, idle="idle", move="move",
                 allow=None, glows_eye=(), lum=lum_hex, rgb=hexrgb, gait=True, fps=30, facing="right"):
        self.ink, self.shadow, self.effects = ink, set(shadow), set(effects)
        self.eye, self.flier, self.idle, self.move = eye, flier, idle, move
        self.allow, self.glows_eye, self.lum, self.rgb = allow or {}, set(glows_eye), lum, rgb
        self.gait = gait                                  # it walks on legs (a snake or a slug does not: no stiff;
        self.fps = fps                                    # hop then judges every loop); the rate the loops play at
        self.facing = facing                              # "right" or "left": where reshape's face window lies

    def is_ink(self, v):
        return v in self.ink if self.ink is not None else v is not None and self.lum(v) < 40


# ---- frame helpers ---------------------------------------------------------------------------------------------
def _pieces(f, skip):
    pts = {(x, y) for y, r in enumerate(f) for x, v in enumerate(r) if v is not None and v not in skip}
    sizes, seen = [], set()
    for q in pts:
        if q in seen:
            continue
        stack, n = [q], 0
        seen.add(q)
        while stack:
            x, y = stack.pop()
            n += 1
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    m = (x + a, y + b)
                    if m in pts and m not in seen:
                        seen.add(m)
                        stack.append(m)
        sizes.append(n)
    return sorted(sizes)


def _shifted(f, dy):
    h, w = len(f), len(f[0])
    return [f[y - dy] if 0 <= y - dy < h else [None] * w for y in range(h)]


def _diff(p, q):
    return sum(1 for y in range(len(p)) for x in range(len(p[0])) if p[y][x] != q[y][x])


def _change(p, q):
    """Pixels changed from p to q, p first moved a pixel up or down if that fits better (a bob is on purpose)."""
    return min(_diff(_shifted(p, dy), q) for dy in (-1, 0, 1))


def _aligned(frames, dys=None):
    """Each frame moved up or down (at most 2 px) to match the first best, so a bob does not read as flicker.
    dys, if a list, receives each frame's shift."""
    out = [frames[0]]
    if dys is not None:
        dys.append(0)
    for f in frames[1:]:
        dy = min((-2, -1, 0, 1, 2), key=lambda d: _diff(_shifted(f, d), frames[0]))
        out.append(_shifted(f, dy))
        if dys is not None:
            dys.append(dy)
    return out


def _codes(f):
    keys = {}
    return np.array([[0 if v is None else keys.setdefault(v, len(keys) + 1) for v in r] for r in f])


def _best_dx(a, b, reach=6):
    """The sideways shift (and up to 3 px up or down) bringing frame a nearest frame b: (dx, pixels still off)."""
    best, best_dx = None, 0
    for dx in range(-reach, reach + 1):
        for dy in range(-3, 4):
            m = int((np.roll(np.roll(a, dy, 0), dx, 1) != b).sum())
            if best is None or m < best or (m == best and abs(dx) < abs(best_dx)):
                best, best_dx = m, dx
    return best_dx, best


def _flips(seq, lum, skip=(), raw=None):
    """How often a pixel takes a tone for one frame and goes straight back (A, B, A), skip's frames left out.
    raw, if given, is the same pixel's tones at frame k's own place in the unaligned frames k-1, k, k+1 (one triple
    per k): where those step monotonically (B's lightness between its neighbours', and not equal to both), the A, B, A
    seen after aligning is a sub-pixel in-between on an edge that moved a whole pixel with the bob, not a flicker."""
    n = len(seq)

    def mono(t):
        if t is None or any(v is None for v in t) or t[0] == t[2]:
            return False
        a, b, c = (lum(v) for v in t)
        return min(a, c) <= b <= max(a, c)
    return sum(1 for k in range(n) if k not in skip and seq[k - 1] == seq[(k + 1) % n] != seq[k]
               and (seq[k] is None or seq[k - 1] is None or abs(lum(seq[k]) - lum(seq[k - 1])) >= FAINT)
               and not (raw is not None and mono(raw[k])))


def _near_turns(frames):
    """The frames at and beside a stroke's end (the frames either side much alike, as a wing at the bottom of its
    beat): a pixel the stroke passes there goes A, B, A on purpose. Turns on over a quarter of the loop are no
    stroke but a texture crawling: nothing is left out then."""
    n = len(frames)
    step = [_diff(frames[k], frames[k - 1]) for k in range(n)]
    turns = [k for k in range(n) if 0 < (d := min(step[k], step[(k + 1) % n]))
             and _diff(frames[k - 1], frames[(k + 1) % n]) <= d / 2]
    return set() if len(turns) > n / 4 else {(k + j) % n for k in turns for j in (-1, 0, 1)}


def _figure(f, spec):
    rows = list(f)
    while rows and all(v is None or v in spec.shadow for v in rows[-1]):
        rows.pop()
    return rows


# ---- array helpers for the motion checks (choppy, snap, tick, hop, vanish, shallow, reshape) ---------------------
def _arrays(frames, spec):
    """The creature alone (effects and shadow removed, A0) as int arrays sharing one key table: 0 is air.
    Returns (arrays, the set of ink codes)."""
    keys, ink = {}, set()
    skip = spec.effects | spec.shadow
    out = []
    for f in frames:
        a = np.zeros((len(f), len(f[0])), np.int32)
        for y, r in enumerate(f):
            for x, v in enumerate(r):
                if v is not None and v not in skip:
                    if v not in keys:
                        keys[v] = len(keys) + 1
                        if spec.is_ink(v):
                            ink.add(keys[v])
                    a[y, x] = keys[v]
        out.append(a)
    return out, ink


def _sh(a, dy, dx=0):
    """a moved dy rows down and dx columns right (negative: up, left), air filling in; nothing wraps round."""
    h, w = a.shape
    out = np.zeros_like(a)
    if abs(dy) >= h or abs(dx) >= w:
        return out
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def _nd(p, q):
    return int((p != q).sum())


def _chg(p, q):
    """_change on arrays: pixels changed from p to q, a 1-px bob forgiven."""
    return min(_nd(_sh(p, dy), q) for dy in (-1, 0, 1))


def _area(arrs):
    return sum(int((a > 0).sum()) for a in arrs) / len(arrs)


def _holds(flags):
    """Frames from one move to the next, cyclic (flags: does step k move)."""
    n, mv = len(flags), [k for k, f in enumerate(flags) if f]
    return [((mv[(i + 1) % len(mv)] - mv[i]) % n) or n for i in range(len(mv))]


def _blobs(m):
    """8-connected pieces of a boolean array, each as (ys, xs) index arrays."""
    pts = set(zip(*np.nonzero(m)))
    out = []
    while pts:
        stack = [pts.pop()]
        piece = list(stack)
        while stack:
            y, x = stack.pop()
            for b in (-1, 0, 1):
                for a in (-1, 0, 1):
                    q = (y + b, x + a)
                    if q in pts:
                        pts.remove(q)
                        stack.append(q)
                        piece.append(q)
        out.append((np.array([p[0] for p in piece]), np.array([p[1] for p in piece])))
    return out


def _dilate(m, r):
    out = np.zeros_like(m)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= _sh(m, dy, dx)
    return out


def _stabilised(arrs, ink):
    """Each frame moved by the whole rows that best match frame 0's colours exactly (ink excluded: an outline matches
    anywhere), so a whole-figure lift is taken out before reading what changed (vanish, shallow)."""
    ref = arrs[0]
    can = (ref > 0) & ~np.isin(ref, list(ink))
    out = []
    for a in arrs:
        dy = max(range(-8, 9), key=lambda d: (int(((_sh(a, d) == ref) & can).sum()), -abs(d)))
        out.append(_sh(a, dy))
    return out


# ---- the check -------------------------------------------------------------------------------------------------
def check(loops, spec, warns=None):
    """loops: {name: [frame, ...]}, a frame a list of rows of colour keys or None. Returns fault lines; warns, if a
    list, receives the warning lines (looked at, not counted as faults)."""
    faults = []
    allf = [(a, i, f) for a, v in loops.items() for i, f in enumerate(v)]
    sizes = {(len(f[0]), len(f)) for _, _, f in allf}
    if len(sizes) > 1:
        return [f"size: frames differ {sorted(sizes)}"]
    fx = spec.effects
    for a, i, f in allf:
        drawn = [(x, y) for y, r in enumerate(f) for x, v in enumerate(r) if v is not None]
        if not drawn:
            faults.append(f"empty: {a}[{i}]")
            continue
        stray = [s for s in _pieces(f, fx | spec.shadow)[:-1] if s > spec.allow.get(a, 0)]
        if stray:
            faults.append(f"apart: {a}[{i}] {len(stray)} piece(s) of {stray} px apart from the figure")
        if spec.eye and a not in spec.glows_eye and not any(v == spec.eye for r in f for v in r):
            faults.append(f"eye: {a}[{i}] has no eye ({spec.eye})")
        h, w = len(f), len(f[0])
        open_edge = sum(1 for x, y in drawn if not spec.is_ink(f[y][x]) and f[y][x] not in spec.shadow
                        and f[y][x] not in fx and any(not (0 <= x + dx < w and 0 <= y + dy < h)
                                                      or f[y + dy][x + dx] is None
                                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
        if open_edge > 2:
            faults.append(f"outline: {a}[{i}] {open_edge} coloured edge pixel(s) with no ink")
    if any(not any(v is not None for r in f for v in r) for _, _, f in allf):
        return faults
    for a, frames in loops.items():
        figs = [[[None if v in fx else v for v in r] for r in f] for f in frames]   # the creature alone
        if spec.flier:
            if len({tuple(i for i, v in enumerate(f[-1]) if v in spec.shadow) for f in frames}) > 1:
                faults.append(f"ground: {a} the shadow moves")
        elif a != spec.move:
            feet = {max(y for y, r in enumerate(f) for v in r if v is not None) for f in figs}
            if len(feet) > 1:
                faults.append(f"ground: {a} the feet leave the ground line (rows {sorted(feet)})")
        steps = [_change(figs[k], figs[(k + 1) % len(figs)]) for k in range(len(figs))]
        moving = [s for s in steps if s]
        mean = sum(moving) / len(moving) if moving else 0
        if moving and max(steps) > JUMP * mean:
            faults.append(f"jump: {a} a change of {max(steps)} px against a mean of {mean:.0f} "
                          f"(frame {steps.index(max(steps))})")
        arr = [_codes(f) for f in frames]                 # one frame knocked sideways out of step: it fits both
        n = len(arr)                                      # neighbours moved by one dx while they fit each other
        for k in range(n):
            p, c, q = arr[k - 1], arr[k], arr[(k + 1) % n]
            (dp, mp), (dq, mq), (pq, _) = _best_dx(c, p), _best_dx(c, q), _best_dx(p, q)
            twin = [d for d, m in ((dp, mp), (dq, mq)) if abs(d) >= 2 and m <= 0.03 * int((c != 0).sum())]
            if (dp == dq and abs(dp) >= 2 and abs(pq) <= 1) or twin:
                faults.append(f"jump: {a}[{k}] is knocked {abs((twin or [dp])[0])} px sideways out of step")
        body = sum(1 for r in _figure(frames[0], spec) for v in r if v is not None)
        if a == spec.move and body and mean / body < STILL:
            faults.append(f"still: {a} changes {mean / body:.1%} of the figure a frame")
        faults += _shimmer(a, frames, spec)
    warns = warns if warns is not None else []
    return (faults + frozen(loops, spec) + stiff(loops, spec) + cadence(loops, spec) + snap(loops, spec)
            + tick(loops, spec, warns) + hop(loops, spec) + vanish(loops, spec) + shallow(loops, spec)
            + reshape(loops, spec, warns))


def _raw_triples(frames, dys, x, y):
    """For the aligned pixel (x, y): per frame k, the tones at frame k's own source place (row y - dys[k]) in the
    unaligned frames k-1, k, k+1 (None off the frame). _flips reads them to tell a sub-pixel step from a flicker."""
    n, h = len(frames), len(frames[0])
    return [tuple(frames[j % n][y - dys[k]][x] for j in (k - 1, k, k + 1)) if 0 <= y - dys[k] < h else None
            for k in range(n)]


def _shimmer(a, frames, spec):
    """Texture crawl: pixels drawn in every (bob-aligned) frame that flip A, B, A on at least a sixth of the frames,
    over SHIMMER of those pixels. A flip at a stroke's turn, between tones too alike to see, or one that is a
    monotonic sub-pixel step in the unaligned frames (see _flips) is not counted."""
    dys = []
    al = _aligned(frames, dys)
    h, w = len(al[0]), len(al[0][0])
    held = [(x, y) for y in range(h) for x in range(w) if all(f[y][x] is not None for f in al)]
    if not held or len(al) <= 4:
        return []
    near = _near_turns(al)
    flick = sum(1 for x, y in held
                if _flips([f[y][x] for f in al], spec.lum, near, _raw_triples(frames, dys, x, y)) >= len(al) / 6)
    if flick / len(held) > SHIMMER:
        return [f"shimmer: {a} {flick} of its {len(held)} steady pixels flicker back and forth"]
    return []


def cadence(loops, spec):
    """How the motion is spread over the frames: choppy on the creature alone (effects and shadow removed, A0);
    uneven and lurch exactly as before (effects removed, a flier's shadow kept).

    choppy (A1). Perceived smoothness is set by the longest holds, not the mean (Klein et al. 2023): twos read smooth,
    threes start to read choppy, a 4-frame hold inside a cycle reads as a dropped rate. A move is a step changing over
    max(1, MOVE_EPS * A) px (A: the mean figure area); holds are the cyclic frames from one move to the next. A loop
    with fewer than 4 moves, or with a rest (a hold of n/3 or more), is a gesture: snap judges it. Otherwise
        rate = moves * fps / n          fault when rate < CHOPPY_RATE (10/s), however small the steps;
        dropped update                  fault when median(holds) >= 3 and some hold >= 2 * median(holds)
    (the second sees one lost update the mean rate hides: twelve poses on threes with one skipped, a 6-frame hold).

    uneven: the holds between moves (here a move is over MOVE_MIN of the figure: a blink or a glint is not) differ by
    2 frames or more and by twice (one long rest, at least twice the next longest, is an idle's pause and is left
    out). lurch: the median ratio of one move to the next over LURCH (a whole-body bob after a small leg step: a hitch
    on each beat). uneven and lurch only where the moves are big enough to see (over CADENCE_STEP of the figure), and
    on a cycle of moves (four or more; six for lurch): one gesture in an idle is drawn on purpose."""
    out = []
    for a, frames in loops.items():
        n = len(frames)
        if n < 4:
            continue
        figs, _ = _arrays(frames, spec)
        area = _area(figs)
        steps = [_nd(figs[k], figs[(k + 1) % n]) for k in range(n)]
        flags = [s > max(1.0, MOVE_EPS * area) for s in steps]
        if sum(flags) >= 4:
            hs = _holds(flags)
            if max(hs) < n / 3:
                rate, med = sum(flags) * spec.fps / n, statistics.median(hs)
                if rate < CHOPPY_RATE:
                    most = int(spec.fps // CHOPPY_RATE)           # the longest hold that keeps CHOPPY_RATE
                    how = (f"at {spec.fps:g} fps hold each pose {most} frame{'s' if most > 1 else ''} at most"
                           if most >= 1 else f"at {spec.fps:g} fps even a new pose every frame is too few: play it "
                           f"faster")
                    out.append(f"choppy: {a} updates {rate:.1f} times a second (holds {hs}): a few drawings each "
                               f"held long read as a dropped frame rate: a new pose at least every "
                               f"{1 / CHOPPY_RATE:g} s ({how}); spread the parts on one clock with staggered "
                               f"phases, or draw in-betweens")
                elif med >= 3 and max(hs) >= 2 * med:
                    out.append(f"choppy: {a} drops an update: a hold of {max(hs)} frames among holds of {med:g} "
                               f"(holds {hs}): two ticks running gave one pose; stagger the parts' phases so "
                               f"something changes on every tick")
        figs, _ = _arrays(frames, Spec(ink=spec.ink, effects=spec.effects, lum=spec.lum))   # as before: effects
        area = _area(figs)                                # alone removed (the shadow kept) for uneven and lurch
        steps = [_nd(figs[k], figs[(k + 1) % n]) for k in range(n)]
        moving = [s for s in steps if s > MOVE_MIN * area]
        if len(moving) < 3:
            continue
        big = sorted(moving)[len(moving) // 2] / max(1.0, area)
        if big <= CADENCE_STEP:
            continue
        held = steps.count(0) > 0
        holds = _holds([s > MOVE_MIN * area for s in steps])
        longest = sorted(holds)
        rest = len(longest) > 2 and longest[-1] >= 2 * longest[-2]   # an idle's one long pause: left out
        seq = [h for h in holds if not (rest and h == longest[-1])]
        abrupt = sum(1 for p, q in zip(seq, seq[1:] + seq[:1]) if max(p, q) >= 2 * min(p, q) and abs(p - q) >= 2)
        if len(seq) >= 4 and abrupt >= len(seq) / 2:      # a cycle (a gesture of two or three moves is not); a
            # sway's ease doubling its hold at each turn is half less: ease at a stroke's turn lengthens holds gradually
            out.append(f"uneven: {a} holds {holds} frames between its moves in turn: hold every pose alike")
        pairs = sorted(max(p, q) / max(1, min(p, q)) for p, q in zip(moving, moving[1:] + moving[:1]))
        if held and len(moving) >= 6 and pairs[len(pairs) // 2] > LURCH:   # a held cycle alternating big and small
            out.append(f"lurch: {a} its moves alternate big and small (x{pairs[len(pairs) // 2]:.1f}) between held "
                       f"frames: move something on every frame, or spread the big change (a bob) over the steps")
    return out


def snap(loops, spec):
    """A2, the idle only: a dead stop, then a big change. s[k] = _change(F[k], F[k+1]) / A (a 1-px bob forgiven).
    For each step with s[k] > SNAP_STILL, hold = 1 + the still run (s <= SNAP_STILL) ending just before it, cyclic.
    Fault when some step has hold >= fps/3 (a third of a second) and s[k] >= SNAP_STEP. Why: the moving hold
    (Williams): an idle never stops dead and then lurches; a rest may be long only when what ends it is small (a
    blink, a glint). Actions are left out: an anticipation held and then sprung is on purpose. Fitted margins: the
    faulty idle held 30 frames before a 73 % step; accepted idles held 26 frames before a 7 % step (a blink and glow),
    12 before 2 %, and 1-4 frames before anything bigger."""
    a = spec.idle
    if a not in loops or len(loops[a]) < 4:
        return []
    figs, _ = _arrays(loops[a], spec)
    n, area = len(figs), max(1.0, _area(figs))
    s = [_chg(figs[k], figs[(k + 1) % n]) / area for k in range(n)]
    worst = None
    for k in range(n):
        if s[k] <= SNAP_STILL:
            continue
        run = 0
        while run < n - 1 and s[(k - 1 - run) % n] <= SNAP_STILL:
            run += 1
        hold = run + 1
        if hold >= spec.fps / 3 and s[k] >= SNAP_STEP and (worst is None or hold * s[k] > worst[0]):
            worst = (hold * s[k], hold, s[k], k)
    if worst:
        score, hold, step, k = worst
        return [f"snap: {a} stands dead still {hold} frames, then changes {step:.0%} of the figure at once (frame "
                f"{k}, score {score:.1f}): keep something small moving through the rest (a breath, a blink, a "
                f"glint) and ease the big change in and out (holds 3, 2, 2, 3), each step under a quarter"]
    return []


def _eye_rows(frames, spec):
    """The eye's row per frame: the 8-connected piece of the eye colour (the biggest in frame 0, frontmost on a tie;
    then the piece nearest the last frame's eye), its mean row rounded half up. None if a frame has no eye."""
    out, last = [], None
    for f in frames:
        m = np.array([[v == spec.eye for v in r] for r in f])
        pcs = _blobs(m)
        if not pcs:
            return None
        cents = [(float(ys.mean()), float(xs.mean()), len(ys)) for ys, xs in pcs]
        if last is None:
            front = 1 if spec.facing != "left" else -1
            c = max(cents, key=lambda t: (t[2], front * t[1]))
        else:
            c = min(cents, key=lambda t: (t[0] - last[0]) ** 2 + (t[1] - last[1]) ** 2)
        last = c
        out.append(math.floor(c[0] + 0.5))
    return out


def _runs(levels):
    """Cyclic runs [level, length], starting at a change of level; [] when the level never changes."""
    n = len(levels)
    if len(set(levels)) == 1:
        return []
    s = next(k for k in range(n) if levels[k] != levels[k - 1])
    out = []
    for v in levels[s:] + levels[:s]:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return out


def _pulse(R):
    """Extremum runs (both neighbours on one side) dwelling too briefly: under 3 frames, or under 4 when a neighbour
    is itself an extremum (a two-level square wave). A run inside a cluster of 3+ consecutive short runs (3 frames or
    less each: a sniff, a buzz) is exempt."""
    N, bad = len(R), []
    if N < 2:
        return bad

    def ext(i):
        return N <= 2 or (R[(i - 1) % N][0] - R[i % N][0]) * (R[(i + 1) % N][0] - R[i % N][0]) > 0

    def short(i):
        return R[i % N][1] <= 3
    for i, (v, ln) in enumerate(R):
        if not ext(i):
            continue
        if N >= 3 and short(i) and ((short(i - 1) and short(i - 2)) or (short(i - 1) and short(i + 1))
                                    or (short(i + 1) and short(i + 2))):
            continue
        need = 4 if (ext(i - 1) or ext(i + 1)) else 3
        if ln < need:
            bad.append((v, ln))
    return bad


def _lift_track(figs):
    """A flier's whole-body height: per step, dy = +-1 when shifting the frame by it cuts the diff below 0.6 of the
    unshifted diff, summed. Returns (track, closes): a track that does not come back is not a lift cycle."""
    def dy_of(p, q):
        d0 = _nd(p, q)
        best = min(((d0, 0), (_nd(_sh(p, -1), q), -1), (_nd(_sh(p, 1), q), 1)), key=lambda t: (t[0], abs(t[1])))
        return best[1] if best[1] and best[0] < 0.6 * d0 else 0
    y, ys = 0, [0]
    for k in range(len(figs) - 1):
        y += dy_of(figs[k], figs[k + 1])
        ys.append(y)
    return ys, y + dy_of(figs[-1], figs[0]) == 0


def tick(loops, spec, warns):
    """A3: a whole-pixel level left and regained within a few frames reads as a tick, not a lift. After rounding, a
    1-px sine of peak A is up for (pi - 2 asin(0.5/A)) / 2pi of the beat: 0.16 at A = 0.58, so a lift peaking just
    over half a pixel (or a head turn moving the eye 0.5-0.9 px) shows its top for two frames.
    Eye anchor (the idle; a warning in other loops, where a jump or a strike may be quick on purpose): the eye's row
    per frame split into cyclic runs; an extremum run must last 3 frames, 4 in a two-level square wave (_pulse).
    Shift anchor (a flier's idle and move, eye or none): the whole-body height track (_lift_track); rest = the level
    held longest; each run at another level is an excursion; duty = the shortest excursion / (n / the number of
    excursions), i.e. its length against its fair share of the loop; fault under TICK_DUTY. Fitted margins: the
    faulty hovers 0.11 and 0.14, the lowest accepted 0.21."""
    out = []
    for a, frames in loops.items():
        n = len(frames)
        if n < 4:
            continue
        if spec.eye and a not in spec.glows_eye:
            ys = _eye_rows(frames, spec)
            R = _runs(ys) if ys else []
            bad = _pulse(R)
            if bad:
                v, ln = min(bad, key=lambda t: t[1])
                line = (f"tick: {a} the eye reaches row {v} for only {ln} frame(s) (eye runs "
                        f"{[tuple(r) for r in R]}): a lift peaking 0.5-0.9 px or a quick head turn; make each level "
                        f"dwell 4+ frames (lift under 0.5 or 1+ game px), or keep the head's turn under half a pixel")
                (out if a == spec.idle else warns).append(line if a == spec.idle else "warn: " + line)
        if spec.flier and a in (spec.idle, spec.move):
            figs, _ = _arrays(frames, spec)
            ys, closes = _lift_track(figs)
            R = _runs(ys) if closes else []
            if len(R) >= 2:
                rest = max({v for v, _ in R}, key=lambda v: sum(ln for w, ln in R if w == v))
                ex = [ln for v, ln in R if v != rest]
                duty = min(ex) / (n / len(ex))
                if duty < TICK_DUTY:
                    out.append(f"tick: {a} the body leaves its rest height for only {min(ex)} frame(s) a beat "
                               f"(duty {duty:.2f}, runs {[tuple(r) for r in R]}): a lift peaking just over half a "
                               f"pixel; use no lift (under 0.5 px) or a whole one (1+ px) held a third of the beat")
    return out


def hop(loops, spec):
    """A4: a grounded body never lifts off its contact. The lowest-row check (ground) misses a body whose belly row
    stays while everything above it rises. G = the loop's lowest drawn row; C_k = the columns whose lowest drawn
    cell lies on G; lift = min|C_k| / median|C_k|. For each step changing at least HOP_STEP of the figure,
    share = 1 - min over dy in +-1, +-2 of diff(shift(F_k, dy), F_k+1) / diff(F_k, F_k+1): how much of the step a
    rigid vertical shift explains. Fault when lift < HOP_LIFT or share >= HOP_SHARE.
    Scope: the idle of any non-flier, and every loop of a legless body (gait False). A legged walk rises on purpose
    (rigid shares 0.14-0.35), a legged action may jump, and a flier is off the ground anyway."""
    if spec.flier:
        return []
    out = []
    for a, frames in loops.items():
        if a != spec.idle and spec.gait:
            continue
        figs, _ = _arrays(frames, spec)
        n, area = len(figs), _area(figs)
        if n < 2 or not area:
            continue
        rows = [np.nonzero(f.any(1))[0] for f in figs]
        G = max(int(r.max()) for r in rows if len(r))
        C = []
        for f in figs:
            low = np.where(f.any(0), f.shape[0] - 1 - np.argmax((f > 0)[::-1], 0), -1)
            C.append(int((low == G).sum()))
        lift = min(C) / max(1.0, statistics.median(C))
        share = 0.0
        for k in range(n):
            p, q = figs[k], figs[(k + 1) % n]
            c = _nd(p, q)
            if c and c >= HOP_STEP * area:
                share = max(share, 1 - min(_nd(_sh(p, dy), q) for dy in (-2, -1, 1, 2)) / c)
        if lift < HOP_LIFT or share >= HOP_SHARE:
            why = (f"its contact on row {G} shrinks to {lift:.0%} of the usual" if lift < HOP_LIFT
                   else f"{share:.0%} of a big step is the whole body shifted up or down")
            out.append(f"hop: {a} the body lifts off the ground ({why}): keep the belly and feet on the ground row; "
                       f"move the parts above it (neck, head, arches), never the whole layer")
    return out


def vanish(loops, spec):
    """A5: a part never blinks out at a stroke's turning point (the far wing always shows a little). Frames are
    stabilised for whole-figure lift. For each transition i -> i+1, 'gone' blobs are 8-connected pieces of F_i lying
    over VANISH_R px from F_i+1, 'came' blobs of F_i+1 over VANISH_R px from F_i. An event is a blob of VANISH_MIN+ px
    whose place stays empty (under 1/3 of it within VANISH_R of the figure) for VANISH_HOLD+ frames, with under half
    its size arriving (or leaving) in the same transition. r4 = blob px / (the mean occupancy change of the
    transitions while the place is empty * the loop's median hold): a big piece going while everything else is slow
    is the turning-point signature; a fast stroke changes much around it. The median hold (moves counted as choppy
    counts them) makes r4 a change per update, not per frame: a sheet holding each drawing 3 frames has two still
    transitions to every moving one, and without it a wing coming up in one drawing step read as a vanish (an accepted
    12-drawing move on twos, r4 1.44 per frame, 0.72 per update). Holding every pose h frames leaves r4
    as it was. Fault when r4 >= VANISH_R4. Fitted margins: the faulty idles 1.22 and 1.50 (updating every frame), the
    highest accepted 0.92. A part covered by others when it vanishes is not seen: a rig should lint its hide rule
    instead."""
    out = []
    for a, frames in loops.items():
        n = len(frames)
        if n < 4:
            continue
        arrs, ink = _arrays(frames, spec)
        area = _area(arrs)                                # the loop's usual hold (moves as choppy counts them):
        flags = [_nd(arrs[k], arrs[(k + 1) % n]) > max(1.0, MOVE_EPS * area) for k in range(n)]
        hold_n = statistics.median(_holds(flags)) if any(flags) else 1   # a sheet on threes moves a third as
        ms = [s > 0 for s in _stabilised(arrs, ink)]      # much per frame as per update
        dil = [_dilate(m, VANISH_R) for m in ms]
        ch = [int((ms[i] ^ ms[(i + 1) % n]).sum()) for i in range(n)]
        best = None
        for i in range(n):
            gone = _blobs(ms[i] & ~dil[(i + 1) % n])
            came = _blobs(ms[(i + 1) % n] & ~dil[i])
            sg, sc = sum(len(b[0]) for b in gone), sum(len(b[0]) for b in came)
            for blob, kind in [(b, "gone") for b in gone] + [(b, "came") for b in came]:
                s = len(blob[0])
                if s < VANISH_MIN or (sc if kind == "gone" else sg) >= s / 2:
                    continue
                hold = 0
                for j in range(1, n):
                    k = (i + j) % n if kind == "gone" else (i + 1 - j) % n
                    if dil[k][blob].sum() / s < 1 / 3:
                        hold += 1
                    else:
                        break
                if hold < VANISH_HOLD:
                    continue
                idx = [(i + d) % n if kind == "gone" else (i - d) % n for d in range(1, hold + 1)]
                r4 = s / max(1.0, hold_n * sum(ch[j] for j in idx) / len(idx))
                if best is None or r4 > best[0]:
                    best = (r4, s, hold, i, kind)
        if best and best[0] >= VANISH_R4:
            r4, s, hold, i, kind = best
            out.append(f"vanish: {a} a {s}-px piece {'switches off' if kind == 'gone' else 'switches on'} at "
                       f"frame {i + 1} and its place stays empty {hold} frames while the rest barely moves (r4 "
                       f"{r4:.2f}): a far wing hidden at the turn of its stroke; let it show (25-30 % of it) or "
                       f"hide it only while it crosses edge-on")
    return out


def _lowfrac(frames, spec):
    """Stabilised for lift; per cell the transitions whose colour changes. Returns (share of the changes lying below
    the middle row of the figure's union, share of the union's rows that ever change, share of its cells that ever
    change, total changes)."""
    arrs, ink = _arrays(frames, spec)
    st = _stabilised(arrs, ink)
    n = len(st)
    cnt = sum((st[i] != st[(i + 1) % n]).astype(int) for i in range(n))
    fig = np.any([s > 0 for s in st], 0)
    ys = np.nonzero(fig.any(1))[0]
    if not len(ys):
        return 0.0, 0.0, 0.0, 0
    y0, y1 = int(ys.min()), int(ys.max())
    tot = int(cnt.sum())
    low = int(cnt[int(math.floor((y0 + y1) / 2)) + 1:].sum())
    rows = int((cnt.any(1)[y0:y1 + 1]).sum()) / (y1 - y0 + 1)
    px = int(((cnt > 0) & fig).sum()) / max(1, int(fig.sum()))
    return low / max(1, tot), rows, px, tot


def shallow(loops, spec):
    """A6, a flier: an idle beats more slowly than the move, not with a different part of the wing. A squeeze about
    the wing's own lower edge moves only its top: the lower half of the bird is dead. lowfrac = the share of all
    (lift-stabilised) cell changes lying below the middle row of the figure's union; fault when
    lowfrac(idle) / lowfrac(move) < SHALLOW. With no move loop: the rows that ever change must cover SHALLOW_ROWS of
    the figure's rows and the changed cells SHALLOW_PX of its union. Fitted margins: the faulty idle 0.04, the lowest
    accepted 0.37; an absolute bar fails a beetle whose idle and move both keep low (0.07). Walkers are left out: a
    standing idle rightly keeps its legs still while its walk moves them."""
    if not spec.flier or spec.idle not in loops or len(loops[spec.idle]) < 4:
        return []
    li, rows, px, tot = _lowfrac(loops[spec.idle], spec)
    if not tot:
        return []
    a = spec.idle
    if spec.move in loops and len(loops[spec.move]) >= 4:
        lm = _lowfrac(loops[spec.move], spec)[0]
        if lm > 0 and li / lm < SHALLOW:
            return [f"shallow: {a} moves only the upper part ({li:.0%} of its changes in the lower half, against "
                    f"{lm:.0%} in the {spec.move}; ratio {li / lm:.2f}): beat the same wing less often, not less "
                    f"far: it must cross the shoulder line (edge-on, then under the belly)"]
    elif rows < SHALLOW_ROWS or px < SHALLOW_PX:
        return [f"shallow: {a} moves only part of the figure ({rows:.0%} of its rows, {px:.0%} of its pixels "
                f"ever change): beat the whole wing, crossing the shoulder line"]
    return []


def _distinct(frames):
    out = [frames[0]]
    for f in frames[1:]:
        if f != out[-1]:
            out.append(f)
    if len(out) > 1 and out[-1] == out[0]:
        out.pop()
    return out


def reshape(loops, spec, warns):
    """A7: the face is rigid. Aligned on itself, the head keeps its silhouette and ink lines (mouth line, jaw) unless
    a face move is drawn on purpose. AI sheets fail this first, redrawing the head in every cell.
    1. The eye: spec.eye's centroid in the first pose, or else the frontmost ink pixel in the front third with colour
       on 3 of its 4 sides. 2. The face window: rows eye +- r, columns from 1 px behind the eye forward (mirrored for
       facing left), r = max(3, round(0.12 * figure width)). 3. Distinct poses only; every pixel classed air, ink or
       colour. 4. For each pose change p -> q, q's window slid by dx, dy in [-3, 3] ([-7, 7] outside the idle, where a
       hop may carry the head far): the fewest class mismatches / p's drawn pixels in the window. 5. Fault in the
       idle when the mean over the pose changes > RESHAPE; a warning in other loops (an action may open its jaw).
    The mean, not the max: one accepted change of 0.41 (wisps passing the face) sits among zeros. A rigid head that
    bobs, slides or turns 1.5 degrees keeps its class map after the best shift. Fitted margins: the faulty idles 0.16
    and 0.13, the highest accepted 0.065."""
    out = []
    for a, frames in loops.items():
        poses = _distinct(frames)
        if len(poses) < 2:
            continue
        fx = spec.effects | spec.shadow
        cls = [np.array([[0 if v is None or v in fx else 1 if spec.is_ink(v) else 2 for v in r] for r in f])
               for f in poses]
        c0, f0 = cls[0], poses[0]
        xs = np.nonzero(c0.any(0))[0]
        if not len(xs):
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        left = spec.facing == "left"
        eye = None
        pts = [(x, y) for y, r in enumerate(f0) for x, v in enumerate(r) if spec.eye and v == spec.eye]
        if pts:
            eye = (round(sum(p[0] for p in pts) / len(pts)), round(sum(p[1] for p in pts) / len(pts)))
        else:
            h, w = c0.shape
            span = range(max(1, x0), min(w - 1, x0 + (x1 - x0) // 3 + 1)) if left else \
                range(max(1, x0 + 2 * (x1 - x0) // 3), min(w - 1, x1 + 1))
            for y in range(1, h - 1):
                for x in span:
                    if c0[y, x] == 1 and sum(c0[y + b, x + c] == 2 for c, b in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3:
                        if eye is None or (x < eye[0] if left else x > eye[0]):
                            eye = (x, y)
        if eye is None:
            continue
        ex, ey = eye
        r = max(3, round(0.12 * (x1 - x0)))
        cx0, cx1 = (ex - r, ex + 1) if left else (ex - 1, ex + r)

        R = 3 if a == spec.idle else 7
        M = r + R + 2                                     # a margin of -1 (outside the frame) round each pose
        pads = []
        for c in cls:
            P = np.full((c.shape[0] + 2 * M, c.shape[1] + 2 * M), -1)
            P[M:M + c.shape[0], M:M + c.shape[1]] = c
            pads.append(P)

        def win(P, dx, dy):
            return P[ey - r + dy + M:ey + r + dy + M + 1, cx0 + dx + M:cx1 + dx + M + 1]
        res = []
        for k in range(len(cls)):
            W0 = win(pads[k - 1], 0, 0)
            drawn = int((W0 > 0).sum())
            if not drawn:
                continue
            best = min(int(((W0 != (W1 := win(pads[k], dx, dy))) & (W0 >= 0) & (W1 >= 0)).sum())
                       for dx in range(-R, R + 1) for dy in range(-R, R + 1))
            res.append(best / drawn)
        if not res:
            continue
        mean = sum(res) / len(res)
        if mean > RESHAPE:
            line = (f"reshape: {a} the face changes shape between poses (mean {mean:.3f} of its pixels change class "
                    f"after the best alignment; worst {max(res):.2f}): draw the head once and move it whole (paste "
                    f"one approved head, placed by the eye), or read every drawing on one grid")
            (out if a == spec.idle else warns).append(line if a == spec.idle else "warn: " + line)
    return out


def stiff(loops, spec):
    """A walker's move: the mean top row of the middle third of the figure, frame by frame. Under STIFF px of rise
    and fall over the loop, the body is a board the legs step under (a gait lifts the body on every step)."""
    if spec.flier or not spec.gait or spec.move not in loops:
        return []
    tops = []
    for f in loops[spec.move]:
        fig = [[None if v in spec.effects or v in spec.shadow else v for v in r] for r in f]
        xs = [x for r in fig for x, v in enumerate(r) if v is not None]
        x0, x1 = min(xs), max(xs)
        cols = range(x0 + (x1 - x0) // 3, x0 + 2 * (x1 - x0) // 3 + 1)
        t = [next((y for y in range(len(fig)) if fig[y][x] is not None), None) for x in cols]
        t = [v for v in t if v is not None]
        tops.append(sum(t) / len(t))
    if max(tops) - min(tops) < STIFF:
        return [f"stiff: {spec.move} the body never rises or falls ({max(tops) - min(tops):.1f} px): lift it on "
                f"each step"]
    return []


def frozen(loops, spec):
    """The head, a box round the eye an eighth of the figure across, in the idle and the move with the bob aligned
    away: under FROZEN of its pixels ever change, it is a mask on a living body."""
    eye = spec.eye
    f0 = next((f for v in loops.values() for f in v if any(eye in r for r in f)), None) if eye else None
    if f0 is None:
        return []
    pts = [(x, y) for y, r in enumerate(f0) for x, v in enumerate(r) if v == eye]
    ex, ey = sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)
    xs = [x for r in f0 for x, v in enumerate(r) if v is not None and v not in spec.shadow]
    hr = max(3, round(0.12 * (max(xs) - min(xs))))
    out = []
    for a in (spec.idle, spec.move):
        if a not in loops:
            continue
        fr = _aligned(loops[a])
        h, w = len(fr[0]), len(fr[0][0])
        box = [(x, y) for y in range(max(0, int(ey - hr)), min(h, int(ey + hr) + 1))
               for x in range(max(0, int(ex - hr)), min(w, int(ex + hr) + 1))]
        drawn = [(x, y) for x, y in box if any(f[y][x] is not None for f in fr)]
        moved = sum(1 for x, y in drawn if len({f[y][x] for f in fr}) > 1)
        if drawn and moved / len(drawn) < FROZEN:
            out.append(f"frozen: {a} the head hardly moves ({moved} of its {len(drawn)} pixels ever change)")
    return out


# ---- pictures --------------------------------------------------------------------------------------------------
def _img(f, rgb, Z, bg=(74, 66, 84)):
    im = Image.new("RGB", (len(f[0]), len(f)), bg)
    for y, r in enumerate(f):
        for x, v in enumerate(r):
            if v is not None:
                im.putpixel((x, y), rgb(v))
    return im.resize((im.width * Z, im.height * Z), Image.NEAREST)


def fault_frames(lines, loops):
    """{loop: {frame indices}} named in fault lines: "loop[k]" and "loop ... (frame k)". Frame indices are 0-based;
    a jump's or a snap's "frame k" is the change from frame k to the next, so both frames are named."""
    out = {}
    for line in lines:
        m = re.match(r"\s*\w+: (\S+?)(?:\[(\d+)\])?\s", line + " ")
        if not m or m.group(1) not in loops:
            continue
        ks = out.setdefault(m.group(1), set())
        if m.group(2):
            ks.add(int(m.group(2)))
        n = len(loops[m.group(1)])
        for k in map(int, re.findall(r"\bframe (\d+)", line)):
            ks.add(k)
            if line.lstrip().startswith(("jump:", "snap:")):      # a step: the frame after it too
                ks.add((k + 1) % n if n else k + 1)
    return out


def sheet(loops, path, rgb=hexrgb, Z=6, faults=None):
    """Every loop's distinct poses (at most 12, spread over the loop, plus any a fault names), each labelled with the
    frames it holds (0-based: "4-7" is one pose held over frames 4 to 7), and under each the pixels changed from the
    pose just before it (shown or not), in red.
    faults: fault lines (check's result); the tiles of the frames they name are outlined in red."""
    marked = fault_frames(faults or [], loops)
    rows = []
    for a, frames in loops.items():
        keys = []                                         # [first frame, last frame, the pose]
        for k, f in enumerate(frames):
            if keys and f == keys[-1][2]:
                keys[-1][1] = k
            else:
                keys.append([k, k, f])
        hit = [any(k0 <= m <= k1 for m in marked.get(a, ())) for k0, k1, _ in keys]
        if len(keys) > 12:
            pick = {round(i * (len(keys) - 1) / 11) for i in range(12)} | {i for i, h in enumerate(hit) if h}
            keep = sorted(pick)
        else:
            keep = list(range(len(keys)))
        tiles = []
        for i in keep:
            k0, k1, f = keys[i]
            before = keys[i - 1][2]                         # the pose just before it, shown or not
            diff = Image.new("RGB", (len(f[0]), len(f)), (30, 26, 34))
            for y, r in enumerate(f):
                for x, v in enumerate(r):
                    if v != before[y][x]:
                        diff.putpixel((x, y), (230, 60, 60))
                    elif v is not None:
                        diff.putpixel((x, y), (90, 84, 100))
            tiles.append((_img(f, rgb, Z), diff.resize((diff.width * Z, diff.height * Z), Image.NEAREST),
                          f"{k0}" if k0 == k1 else f"{k0}-{k1}", hit[i]))
        rows.append((a, tiles))
    gap, head = 8, 28
    W = max(sum(t.width + gap for t, *_ in tiles) for _, tiles in rows) + gap
    out = Image.new("RGB", (W, sum(2 * t[0][0].height + head + 10 for _, t in rows)), (16, 13, 20))
    d, y = ImageDraw.Draw(out), 0
    for a, tiles in rows:
        d.text((4, y + 2), a, fill=(240, 230, 200))
        x = gap // 2
        for top, diff, label, bad in tiles:
            d.text((x, y + 15), label, fill=(255, 120, 120) if bad else (170, 160, 150))
            out.paste(top, (x, y + head))
            out.paste(diff, (x, y + head + 2 + top.height))
            if bad:
                d.rectangle((x - 3, y + head - 3, x + top.width + 2, y + head + 4 + 2 * top.height),
                            outline=(255, 70, 70), width=2)
            x += top.width + gap
        y += 2 * tiles[0][0].height + head + 10
    out.save(path)


def gif(loops, path, rgb=hexrgb, fps=30, Z=5):
    names = list(loops)
    W, H = len(loops[names[0]][0][0]), len(loops[names[0]][0])
    n = max(len(v) for v in loops.values()) * 2
    frames = []
    for t in range(n):
        im = Image.new("RGB", (len(names) * (W + 6), H + 4), (74, 66, 84))
        for i, a in enumerate(names):
            im.paste(_img(loops[a][t % len(loops[a])], rgb, 1), (i * (W + 6) + 3, 2))
        frames.append(im.resize((im.width * Z, im.height * Z), Image.NEAREST))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=round(1000 / fps), loop=0)


def tracks(loops, spec):
    """What to read before the GIF (the workflow's look at the motion): per loop, the eye's row runs (level, frames)
    and the per-step change list (pixels changed from frame k to k+1, a 1-px bob forgiven, as a share of the
    figure). A 2-3-frame excursion of the eye, or a long run of zeros followed by a big step, shows here first."""
    lines = []
    for a, frames in loops.items():
        figs, _ = _arrays(frames, spec)
        n, area = len(figs), max(1.0, _area(figs))
        steps = [_chg(figs[k], figs[(k + 1) % n]) / area for k in range(n)]
        lines.append(f"{a}: steps " + " ".join(f"{s * 100:.0f}" for s in steps) + " (% of the figure)")
        if spec.eye and a not in spec.glows_eye:
            ys = _eye_rows(frames, spec)
            if ys:
                lines.append(f"{a}: eye rows {[tuple(r) for r in _runs(ys)] or [(ys[0], n)]}")
    return lines


# ---- loading ---------------------------------------------------------------------------------------------------
def _grid(im):
    im = im.convert("RGBA")
    return [["#%02x%02x%02x" % im.getpixel((x, y))[:3] if im.getpixel((x, y))[3] >= 128 else None
             for x in range(im.width)] for y in range(im.height)]


def hexcol(v):
    """A colour option normalised to the loaded pixels' key: '#rrggbb', lower case ('FFCC33' and '#ffcc33' alike).
    ValueError when it is not six hex digits."""
    t = v.strip().lower()
    t = t if t.startswith("#") else "#" + t
    if len(t) != 7 or any(c not in "0123456789abcdef" for c in t[1:]):
        raise ValueError(f"not a colour (#rrggbb): {v!r}")
    return t


def load(src, frame=None, frames=None, fps=None):
    """Frames from a strip PNG, a folder of PNGs, or a GIF. A strip is cut by frame (one frame's width) or frames (how
    many it holds); with neither its frames are square (as wide as the strip is tall). ValueError when the strip's
    width is not a whole number of frames: a wrong cut would be checked as a broken animation. A folder is read in
    file-name order (zero-pad the numbers: f00.png, f01.png, ...). A GIF: with fps, each of its images is repeated
    for its own duration, max(1, round(duration_ms * fps / 1000)) frames, since exporters store a held pose as one
    image with a longer duration; without fps, one frame per image (its durations ignored)."""
    if os.path.isdir(src):
        return [_grid(Image.open(os.path.join(src, n))) for n in sorted(os.listdir(src)) if n.lower().endswith(".png")]
    im = Image.open(src)
    if getattr(im, "n_frames", 1) > 1:
        out = []
        for k in range(im.n_frames):
            im.seek(k)
            g = _grid(im.copy())
            ms = im.info.get("duration") or 0
            out += [g] * (max(1, round(ms * fps / 1000)) if fps and ms else 1)
        return out
    if frames:
        if im.width % frames:
            raise ValueError(f"{src}: {im.width} px wide does not split into {frames} frames")
        fw = im.width // frames
    else:
        fw = frame or im.height
        if fw <= 0 or im.width % fw:
            raise ValueError(f"{src}: {im.width} px wide is not a whole number of {fw}-px frames"
                             + ("" if frame else " (square frames assumed): pass --frame W or --frames N"))
    return [_grid(im.crop((k * fw, 0, (k + 1) * fw, im.height))) for k in range(im.width // fw)]


def _wide_strip(src):
    """A single-image file wider than it is tall: a strip load cuts into frames."""
    if not os.path.isfile(src):
        return False
    with Image.open(src) as im:
        return getattr(im, "n_frames", 1) == 1 and im.width > im.height


VALUED = {"--loop", "--frame", "--frames", "--eye", "--facing", "--ink", "--shadow", "--effects", "--allow",
          "--glows-eye", "--idle", "--move", "--out", "--fps", "--name"}
FLAGS = {"--flier", "--legless", "--selftest", "--help", "-h"}


def _args(argv):
    """{option: [values]} for the valued options, {flag: [True]} for the flags. ValueError on an unknown option or a
    missing value."""
    got, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a in VALUED:
            if i + 1 >= len(argv):
                raise ValueError(f"{a} needs a value")
            got.setdefault(a, []).append(argv[i + 1])
            i += 2
        elif a in FLAGS:
            got.setdefault(a, []).append(True)
            i += 1
        else:
            raise ValueError(f"unknown argument {a!r}")
    return got


def main(argv):
    """The command line (see the module's help). Returns the exit code: 0 no fault, 1 faults, 2 a usage error."""
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    try:
        got = _args(argv)

        def opt(name, default=None, many=False):
            vals = got.get(name, [])
            return vals if many else (vals[-1] if vals else default)

        def cols(s):
            return {hexcol(c) for c in s.split(",") if c.strip()} if s else set()

        def count(name):
            v = opt(name)
            if v is None:
                return None
            if not v.isdigit() or int(v) <= 0:
                raise ValueError(f"{name} must be a whole number over 0, not {v!r}")
            return int(v)
        frame, frames = count("--frame"), count("--frames")
        if frame and frames:
            raise ValueError("give --frame or --frames, not both")
        loops = {}
        for spec_ in opt("--loop", many=True):
            if "=" not in spec_:
                raise ValueError(f"--loop takes NAME=PATH, not {spec_!r}")
            name, src = spec_.split("=", 1)
            if not os.path.exists(src):
                raise ValueError(f"no such file or folder: {src}")
            loops[name] = (name, src)
        if not loops:
            print(__doc__)
            return 2
        facing = opt("--facing", "right")
        if facing not in ("right", "left"):
            raise ValueError("--facing must be right or left")
        allow = {}
        for a in opt("--allow", many=True):
            k, _, v = a.partition("=")
            if not v.isdigit():
                raise ValueError(f"--allow takes LOOP=N, not {a!r}")
            allow[k] = int(v)
        try:
            fps = float(opt("--fps", 30))
        except ValueError:
            raise ValueError(f"--fps must be a number, not {opt('--fps')!r}") from None
        if not fps > 0:
            raise ValueError("--fps must be over 0")
        loops = {name: load(src, frame, frames, fps) for name, (_, src) in loops.items()}
        eye = opt("--eye")
        spec = Spec(ink=cols(opt("--ink")) or None, shadow=cols(opt("--shadow")), effects=cols(opt("--effects")),
                    eye=hexcol(eye) if eye else None, flier="--flier" in got, idle=opt("--idle", "idle"),
                    move=opt("--move", "move"), allow=allow, glows_eye=opt("--glows-eye", many=True),
                    gait="--legless" not in got, fps=fps, facing=facing)
    except ValueError as e:
        print(f"error: {e}  (--help lists the options)", file=sys.stderr)
        return 2
    if not frame and not frames and any(_wide_strip(s.split("=", 1)[1]) for s in opt("--loop", many=True)):
        print("note: strips cut into square frames (no --frame or --frames given)")
    warns = []
    faults = check(loops, spec, warns)
    out = opt("--out", ".")
    os.makedirs(out, exist_ok=True)
    name = opt("--name", "anim")
    sheet(loops, os.path.join(out, f"{name}_check.png"), faults=faults)
    gif(loops, os.path.join(out, f"{name}_check.gif"), fps=fps)
    print(f"{name}: {len(faults)} fault(s)")
    for f in faults + warns:
        print("  " + f)
    for line in tracks(loops, spec):                     # read these before the GIF (the eye's rows, the steps)
        print("  " + line)
    print("sheets:", os.path.abspath(out))
    return 1 if faults else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            import pixel_anim_selftest
        except ImportError:
            print("error: --selftest needs pixel_anim_selftest.py beside this file", file=sys.stderr)
            sys.exit(2)
        sys.exit(0 if pixel_anim_selftest.run("--verbose" in sys.argv) else 1)
    sys.exit(main(sys.argv[1:]))
