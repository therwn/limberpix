"""The check checked: draws a small walker and a small flier that animate well, checks they pass with no false alarm,
then breaks them on purpose in every way pixel_anim_check knows and checks each break is caught by its own fault.
A new check comes with its own case here.

    python pixel_anim_selftest.py [--verbose] [--sheets DIR]   # --verbose: the numbers behind the clean cases;
                                                               # --sheets: the test creatures as GIFs in DIR"""
import contextlib
import copy
import io
import math
import os
import random
import sys
import tempfile

from PIL import Image, ImageSequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_anim_check as pac                           # noqa: E402

INK, FUR, BELLY, EYE, SHADOW = "#1a1216", "#c8946a", "#e3c09a", "#ffcc33", "#2b2430"
MID = "#d6aa82"                                           # between FUR and BELLY: a sub-pixel in-between tone


def _outline(g):
    h, w = len(g), len(g[0])
    add = [(x, y) for y in range(h) for x in range(w) if g[y][x] is None and any(
        0 <= x + a < w and 0 <= y + b < h and g[y + b][x + a] not in (None, INK)
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in add:
        g[y][x] = INK
    return g


def _disc(g, cx, cy, rx, ry, col, lower=None):
    for y in range(len(g)):
        for x in range(len(g[0])):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                g[y][x] = lower if lower and y > cy else col


def _line(g, x0, y0, x1, y1, col, width=1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
        for d in range(width):
            if 0 <= y < len(g) and 0 <= x + d < len(g[0]):
                g[y][x + d] = col


LEG_L, BODY_L, TAIL_L, HEAD_L = "#800000", "#008000", "#000080", "#808000"   # the part strip's flat colours


def _half(v):
    return math.floor(v + 0.5)


def walker_frame(t, kind, bob=True, rise=None, lead=False, cut=False, nudge=0, nods=True, bobs=2, lunge=None,
                 labels=False, band=0):
    """A four-legged walker 34x22 standing on row 20: in the move it walks in place (a planted foot goes back at an
    even pace, a lifted one swings forward), the body rising a pixel as the legs pass under it; the head nods and
    the tail wags in both loops.
    For the cases: rise forces the body's rise (0 or 1, the legs stretching under it); lead paints the fur/belly
    line's row 11 a mid tone (MID), the sub-pixel in-between of a 1-px rise or fall; cut takes the head's front
    column and lowest row off (a snout cut flat, as a redrawn sheet cell may); nudge moves the back planted foot
    that many px forward; nods False holds the head on the body; bobs 1 lifts the body once a loop, not twice;
    lunge (dx, dy) carries the head that far on a neck (a bite); labels draws the part strip instead (each part one
    flat colour, no outline); band raises the body's rear half (columns left of 16) that many px on its own, a torso
    cut into two bands."""
    g = [[None] * 34 for _ in range(22)]
    s = math.sin(2 * math.pi * t)
    up = 1 if bob and kind == "move" and (abs(s) < 0.5 if bobs == 2 else s > 0) else 0
    if rise is not None:
        up = rise
    fur, belly = (BODY_L, BODY_L) if labels else (FUR, BELLY)
    for i, hx in enumerate((10, 13, 18, 21)):            # back pair, front pair; diagonal pairs in step
        dx = lift = 0
        if kind == "move":
            u = (t + (0.25 if i in (0, 3) else 0.75)) % 1
            dx, lift = (2 - 8 * u, 0) if u < 0.5 else (-2 + 8 * (u - 0.5), 1)   # planted: back; lifted: forward
            dx = _half(dx) + (nudge if i == 0 and not lift else 0)
        _line(g, hx, 14 - up, hx + dx, 19 - lift, LEG_L if labels else "#a8744e", 2)
    _disc(g, 15.5, 11.5 - up, 8, 3.6, fur, belly)
    if band:                                              # the rear half drawn again band px higher, rigidly
        for y in range(22):
            for x in range(16):
                if g[y][x] in (fur, belly):
                    g[y][x] = None
        for y in range(22):
            for x in range(16):
                if ((x - 15.5) / 8) ** 2 + ((y + band - 11.5 + up) / 3.6) ** 2 <= 1:
                    g[y][x] = belly if y + band > 11.5 - up else fur
    if lead and not labels:
        for x in range(34):
            if g[11][x] in (FUR, BELLY):
                g[11][x] = MID
    wag = round(2 * math.sin(2 * math.pi * t + 1.0))
    _line(g, 7, 10 - up, 3, 6 + wag - up, TAIL_L if labels else FUR, 2)
    nod = round(math.sin(2 * math.pi * t * (2 if kind == "move" else 1))) if nods else 0
    lx, ly = lunge or (0, 0)
    hc = HEAD_L if labels else FUR
    if lunge:
        for j in range(3):
            _line(g, 21, 9 + j - up, 25 + lx, 7 + j + ly + nod - up, hc)
    hy = 7.5 + nod - up + ly
    head = [(x, y) for y in range(22) for x in range(34) if ((x - 25.5 - lx) / 3.6) ** 2 + ((y - hy) / 3.2) ** 2 <= 1]
    _disc(g, 25.5 + lx, hy, 3.6, 3.2, hc)
    if cut:
        fx, fy = max(x for x, _ in head), max(y for _, y in head)
        for x, y in head:
            if (x == fx or y == fy) and g[y][x] == FUR:
                g[y][x] = None
    g[7 + nod - up + ly][27 + lx] = HEAD_L if labels else EYE
    return g if labels else _outline(g)


def flier_frame(t, kind, shallow=False, hidden=False):
    """A flier 30x24 over its shadow (the bottom row): its wing foreshortened through the beat, the body lifted on
    the downstroke, the head nodding against it.
    For the cases: shallow squeezes the wing only between s 0.4 and 1 about its own lower edge, so its tip never
    passes the shoulder row, and holds the head (the lower half of the bird stays dead, as in a top-only beat whose
    head sits high); hidden draws only the wing's pixels over the body (the rest gone behind it)."""
    g = [[None] * 30 for _ in range(24)]
    s = math.cos(2 * math.pi * t) * (0.6 if kind == "idle" else 1.0)
    if shallow:
        s = 0.7 + 0.3 * math.cos(2 * math.pi * t)
    lift = round(max(0.0, math.sin(2 * math.pi * t)))
    cy = 10 - lift
    _disc(g, 14, cy, 5.5, 3, FUR, BELLY)
    nod = 0 if shallow else round(0.8 * math.sin(2 * math.pi * t + 2.0))
    _disc(g, 20.5, cy - 2 + nod, 2.6, 2.4, FUR)
    g[cy - 2 + nod][21] = EYE
    tip = cy - round(7 * s)
    for x in range(6, 17):                                # the wing: a fan from the shoulder (x 16) to the tip (x 6)
        u = (16 - x) / 10
        top, bot = cy - 1 + round((tip - cy) * u), cy - 1 + round((tip - cy) * u * 0.4)
        if shallow:                                       # squeezed about its own lower edge: that edge stays put
            bot = cy - 1
        for y in range(min(top, bot), max(top, bot) + 1):
            if not hidden or ((x - 14) / 5.5) ** 2 + ((y - cy) / 3) ** 2 <= 1:
                g[y][x] = "#8f6a52"
    g = _outline(g)
    for x in range(10, 20):
        g[23][x] = SHADOW
    return g


def creatures():
    walker = {"idle": [walker_frame(k / 24, "idle") for k in range(24)],
              "move": [walker_frame(k / 16, "move") for k in range(16)]}
    flier = {"idle": [flier_frame(k / 24, "idle") for k in range(24)],
             "move": [flier_frame(k / 16, "move") for k in range(16)]}
    return walker, flier


def run(verbose=False):
    """Every case, one line each; False when any fails. verbose adds the numbers behind the special clean cases."""
    walker, flier = creatures()
    ws = pac.Spec(eye=EYE)
    fs = pac.Spec(eye=EYE, flier=True, shadow={SHADOW})
    ok = True
    for name, loops, spec in (("walker", walker, ws), ("flier", flier, fs)):
        f = pac.check(loops, spec)
        print(f"clean {name:7s} passes{'' if not f else ': NO, FALSE ALARM: ' + '; '.join(f[:3])}")
        ok &= not f
    cases = []

    def speck(L):
        for y in (1, 2):
            for x in (1, 2):
                L["move"][5][y][x] = INK
    cases.append(("apart", "walker", speck))

    def no_eye(L):
        f = L["move"][3]
        for r in f:
            for i, v in enumerate(r):
                if v == EYE:
                    r[i] = FUR
    cases.append(("eye", "walker", no_eye))

    def open_line(L):
        f = L["idle"][2]
        edge = [(x, y) for y, r in enumerate(f) for x, v in enumerate(r) if v == INK and any(
            0 <= x + a < len(r) and f[y][x + a] not in (None, INK) for a in (1, -1))]
        for x, y in edge[:8]:
            f[y][x] = None
    cases.append(("outline", "walker", open_line))

    def hop(L):
        L["idle"][10] = pac._shifted(L["idle"][10], -2)
    cases.append(("ground", "walker", hop))

    def slide(L):
        f = L["idle"][7]
        f[-1] = [None] * 3 + f[-1][:-3]
    cases.append(("ground", "flier", slide))

    def padded_slide(L):
        slide(L)
        for frames in L.values():
            for f in frames:
                f.append([None] * len(f[-1]))
    cases.append(("ground", "flier", padded_slide))

    def pop(L):
        L["move"][8] = [[None] * 4 + r[:-4] for r in L["move"][8]]
    cases.append(("jump", "walker", pop))

    def frozen_move(L):
        L["move"] = [copy.deepcopy(L["move"][0]) for _ in range(16)]
        f = L["move"][8]
        x, y = next((x, y) for y, r in enumerate(f) for x, v in enumerate(r) if v == FUR)
        f[y][x] = BELLY
    cases.append(("still", "walker", frozen_move))

    def crawl(L):                                         # texture redrawn every frame, every other frame alike
        rnd = random.Random(7)
        A = L["idle"]
        held = [(x, y) for y in range(len(A[0])) for x in range(len(A[0][0])) if all(f[y][x] not in (None, INK) for f in A)]
        for x, y in rnd.sample(held, max(1, len(held) // 6)):
            for k, f in enumerate(A):
                f[y][x] = "#f0d8b0" if (k + x) % 2 else "#6a4a3a"
    cases.append(("shimmer", "walker", crawl))

    def speckle(L):                                       # texture redrawn at random
        rnd = random.Random(11)
        A = L["idle"]
        steady = [(x, y) for y in range(len(A[0])) for x in range(len(A[0][0]))
                  if A[0][y][x] not in (None, INK) and all(f[y][x] == A[0][y][x] for f in A)]
        for x, y in rnd.sample(steady, max(1, len(steady) // 6)):
            for f in A:
                if rnd.random() < 0.5:
                    f[y][x] = rnd.choice(("#f0d8b0", "#6a4a3a", "#9a7a9a"))
    cases.append(("shimmer", "walker", speckle))

    def beat_crawl(L):                                    # a crawl on a beating wing's loop: its turns left out of
        A = L["move"]                                     # the count must not hide it
        held = [(x, y) for y in range(len(A[0])) for x in range(len(A[0][0]))
                if all(f[y][x] not in (None, INK, SHADOW) for f in A)]
        for k, f in enumerate(A):
            for x, y in held[::2]:
                f[y][x] = "#f0d8b0" if (k + x) % 2 else "#6a4a3a"
    cases.append(("shimmer", "flier", beat_crawl))

    def mask(L):                                          # the head held as on the first frame
        for a in ("idle", "move"):
            f0 = L[a][0]
            ey, ex = next((y, r.index(EYE)) for y, r in enumerate(f0) if EYE in r)
            for f in L[a][1:]:
                for y in range(max(0, ey - 5), min(len(f), ey + 6)):
                    for x in range(max(0, ex - 5), min(len(f[0]), ex + 6)):
                        f[y][x] = f0[y][x]
    cases.append(("frozen", "walker", mask))

    def board(L):                                         # legs stepping under a body that never rises
        L["move"] = [walker_frame(k / 16, "move", bob=False) for k in range(16)]
    cases.append(("stiff", "walker", board))

    def few_drawings(L):                                  # four drawings, each held six frames
        L["move"] = [walker_frame((k // 6 * 6) / 24, "move") for k in range(24)]
    cases.append(("choppy", "walker", few_drawings))

    def stepped(L):                                       # the idle stepped one pose every 6 frames: small steps,
        L["idle"] = [walker_frame((k // 6 * 6) / 24, "idle") for k in range(24)]   # 5 updates a second
    cases.append(("choppy", "walker", stepped))

    def dropped(L):                                       # 12 poses on threes, one skipped: one hold of 6 frames
        poses = [walker_frame(p / 12, "idle") for p in range(12)]
        poses[7] = poses[6]
        L["idle"] = [f for f in poses for _ in range(3)]
    cases.append(("choppy", "walker", dropped))

    def dead_stop(L):                                     # 28 frames dead still, then 4 walk drawings on twos
        L["idle"] = [walker_frame(0, "idle") for _ in range(28)] + [walker_frame((p + 0.5) / 4, "move")
                                                                     for p in range(4) for _ in range(2)]
    cases.append(("snap", "walker", dead_stop))

    def blip(L):                                          # the whole flier up 1 px for 2 frames, twice a loop
        for k in (5, 6, 17, 18):
            f = L["idle"][k]
            L["idle"][k] = pac._shifted(f[:-1], -1) + [f[-1]]   # the shadow row stays
    cases.append(("tick", "flier", blip))

    def lift_off(L):                                      # every row above the lowest raised 1 px on 2 frames: the
        for k in (6, 7):                                  # feet's bottom row stays, so ground does not see it
            f = L["idle"][k]
            low = max(y for y, r in enumerate(f) if any(v is not None for v in r))
            L["idle"][k] = pac._shifted(f[:low], -1) + f[low:]
    cases.append(("hop", "walker", lift_off))

    def far_wing_off(L):                                  # the wing held at the bottom of its stroke 6 frames and
        L["move"][7] = flier_frame(0.5, "move")           # switched off behind the body for the middle 4
        L["move"][12] = flier_frame(0.5, "move")
        for k in range(8, 12):
            L["move"][k] = flier_frame(0.5, "move", hidden=True)
    cases.append(("vanish", "flier", far_wing_off))

    def far_wing_off_twos(L):                             # the same, every frame held twice (a sheet on twos):
        far_wing_off(L)                                   # r4 is read per update, so holding changes nothing
        L["move"] = [f for f in L["move"] for _ in range(2)]
    cases.append(("vanish", "flier", far_wing_off_twos))

    def top_only(L):                                      # the idle squeezes the wing from its top only
        L["idle"] = [flier_frame(k / 24, "idle", shallow=True) for k in range(24)]
    cases.append(("shallow", "flier", top_only))

    def redrawn_snout(L):                                 # every other distinct pose of the idle with its snout cut
        A, pose, last = L["idle"], 0, None
        for k in range(len(A)):
            if last is not None and A[k] != last:
                pose += 1
            last = A[k]
            if pose % 2:
                A[k] = walker_frame(k / 24, "idle", cut=True)
    cases.append(("reshape", "walker", redrawn_snout))

    def stutter(L):                                       # the same eight poses, held 1 and 3 frames in turn
        poses = [walker_frame(p / 8, "move") for p in range(8)]
        L["move"] = [f for p, f in enumerate(poses) for _ in range(1 if p % 2 else 3)]
    cases.append(("uneven", "walker", stutter))

    def hitch(L):                                         # a leg's small step, then the whole body jumping a pixel
        L["move"] = [pac._shifted(walker_frame(p / 16, "move", bob=False), -1 if (p // 2) % 2 else 0)
                     for p in range(8) for _ in range(2)]
    cases.append(("lurch", "walker", hitch))

    def narrow(L):
        L["idle"][4] = [r[:-1] for r in L["idle"][4]]
    cases.append(("size", "walker", narrow))

    # a sub-pixel 1-px breath must pass: the body rises a pixel for half the loop, the fur/belly line taking a mid
    # tone on the frame before each whole step. After the bob is aligned away that tone reads A, B, A; it steps
    # monotonically in the frames themselves, so shimmer must not count it (and nothing else may fire).
    breath = copy.deepcopy(walker)
    breath["idle"] = [walker_frame(k / 24, "idle", rise=int(12 <= k < 24), lead=k in (11, 23)) for k in range(24)]
    f = pac.check(breath, ws)
    al_dys = []
    al = pac._aligned(breath["idle"], al_dys)
    lead = [(x, y) for y in (11, 12) for x in range(34)
            if any(g[y][x] == MID for g in al) and all(g[y][x] is not None for g in al)]
    naive = sum(pac._flips([g[y][x] for g in al], pac.lum_hex) for x, y in lead)
    left = sum(pac._flips([g[y][x] for g in al], pac.lum_hex, raw=pac._raw_triples(breath["idle"], al_dys, x, y))
               for x, y in lead)
    print(f"clean breathing walker (a sub-pixel tone leads each step) passes"
          f"{'' if not f else ': NO, FALSE ALARM: ' + '; '.join(f[:3])}"
          + (f"  (tone flips after aligning: {naive}; counted as shimmer: {left})" if verbose else ""))
    ok &= not f and naive > 0 and left == 0

    # a few drawings held long must not read as a vanish: the clean flier's beat as 4 drawings held 3 frames each
    # (and 8 held 4). Read per frame, the wing coming up in one drawing step against the held frames' zeros looked
    # like a piece switching on while nothing moved (an accepted 12-drawing sheet on twos did).
    held = [x for draws, hold in ((4, 3), (8, 4))
            for x in pac.vanish({"move": [flier_frame((k // hold) / draws, "move") for k in range(draws * hold)]}, fs)]
    print(f"clean flier held on 3s and 4s passes{'' if not held else ': NO, FALSE ALARM: ' + held[0]}")
    ok &= not held

    ok &= later_quiet(walker, flier)
    ok &= crawler_quiet()
    cases += later_cases()
    for kind, who, fn in cases:
        L = copy.deepcopy(walker if who == "walker" else flier)
        extra = fn(L) or {}                               # a case may declare more of the spec (an action, parts)
        spec = pac.Spec(**dict(dict(eye=EYE) if who == "walker" else dict(eye=EYE, flier=True, shadow={SHADOW}),
                               **extra))
        warns = []
        f = pac.check(L, spec, warns)
        hit = [x for x in f if x.startswith(kind + ":")]
        soft = [x for x in warns if x.startswith(f"warn: {kind}:")]
        how = "caught" if hit else "warned" if soft else "MISSED"
        print(f"{kind:8s} on {who:7s} {how}" + (f"  (also: {(f + warns)[0][:110]})" if (f + warns) and how == "MISSED"
                                               else ""))
        ok &= bool(hit or soft)
    ok &= cli(walker)
    print("selftest:", "all hold" if ok else "FAILED")
    return ok


# ---- the later checks: helpers, the clean cases that must stay quiet, the broken ones that must be caught --------
LATER = {"jump", "skate", "gait", "boil", "strike", "counter", "recover", "stage", "piston", "gravity", "squash",
         "lag", "volume", "blend", "orphans", "speck", "doubles", "drift", "swap", "mark", "palette", "choppy",
         "uneven", "split", "hitch"}
GEM, PATCH, DARK = "#5ad1e0", "#3a6ea5", "#2a1a20"


def _on(frames, hold):
    return [copy.deepcopy(f) for f in frames for _ in range(hold)]


def _sx(f, d):
    """A frame moved d px sideways (right when positive), air filling in."""
    return [([None] * d + r[:-d]) if d > 0 else (r[-d:] + [None] * -d) if d < 0 else list(r) for r in f]


def _squat(f, rows):
    """The idle squatted: leg rows 17.. taken out (the legs shortened), the figure above sinking onto them."""
    return [[None] * len(f[0]) for _ in range(rows)] + [list(r) for r in f[:17]] + [list(r) for r in f[17 + rows:]]


def bite(poses):
    """A strike on the walker: (head dx, head dy, hold) per pose, the head carried on its neck, the rest still."""
    return [walker_frame(0, "idle", lunge=(dx, dy)) for dx, dy, h in poses for _ in range(h)]


def leap(poses, tailless=()):
    """A jump on the walker: (lift px, squat rows, hold) per pose; the poses in tailless lose the tail (narrower)."""
    out = []
    for i, (lift, rows, h) in enumerate(poses):
        f = _squat(walker_frame(0, "idle"), rows) if rows else walker_frame(0, "idle")
        if i in tailless:
            f = [[None if x <= 6 else v for x, v in enumerate(r)] for r in f]
        out += [pac._shifted(f, -lift) if lift else f] * h
    return [copy.deepcopy(f) for f in out]


GOOD_BITE = [(0, 0, 3), (-1, -1, 3), (-1, -2, 3), (-1, -3, 9), (3, 1, 3), (2, 1, 3), (2, 0, 3), (1, 0, 3)]
GOOD_LEAP = [(0, 0, 2), (0, 2, 6), (2, 0, 2), (3, 0, 2), (4, 0, 2), (3, 0, 2), (2, 0, 2), (0, 2, 2), (0, 1, 2)]


def _with_gem(frames, dx=0):
    """Each frame with a 1-px gem on the body (the top fur pixel of column 14, one row down), riding the body."""
    out = copy.deepcopy(frames)
    for f in out:
        y = next(y for y in range(len(f)) if f[y][14] == FUR)
        f[y + 1][14 + dx] = GEM
    return out


def _with_patch(frames):
    """Each frame with a 3x3 patch of its own colour on the body (a shield, a mark), riding the body."""
    out = copy.deepcopy(frames)
    for f in out:
        y = next(y for y in range(len(f)) if f[y][17] == FUR)
        for b in range(1, 4):
            for x in (16, 17, 18):
                f[y + b][x] = PATCH
    return out


def _labels(n, **kw):
    """The walker's move as a part strip (one flat colour a part), n frames."""
    return [walker_frame(k / n, "move", labels=True, **kw) for k in range(n)]


def later_quiet(walker, flier):
    """The clean cases the later checks must leave alone (no fault, no warning of theirs)."""
    ok = True
    ws, fs = dict(eye=EYE), dict(eye=EYE, flier=True, shadow={SHADOW})
    pal = {v for a in walker for f in walker[a] for r in f for v in r if v is not None}
    sway = [_sx(walker_frame(p / 12, "idle"), round(2 * math.sin(2 * math.pi * p / 12))) for p in range(12)]
    quiet = [
        ("walker on twos", dict(walker, move=_on(walker["move"], 2)), ws),
        ("walker on threes", dict(walker, move=_on(walker["move"], 3)), ws),
        ("walker idle swaying 2 px over 12 poses on twos", dict(walker, idle=_on(sway, 2)), ws),
        ("walker biting (a strike on threes, one 9-frame key)", dict(walker, bite=bite(GOOD_BITE)),
         dict(ws, actions={"bite": "strike:right"})),
        ("walker leaping (a jump, one 6-frame key)", dict(walker, leap=leap(GOOD_LEAP)),
         dict(ws, actions={"leap": "jump"})),
        ("walker with its part strip", walker, dict(ws, parts={"move": _labels(16), "idle": [
            walker_frame(k / 24, "idle", labels=True) for k in range(24)]}, squash={LEG_L})),
        ("walker against its palette and its drawing", walker,
         dict(ws, palette=pal, ref=walker_frame(0, "idle"))),
        ("walker with a gem (--mark)", {a: _with_gem(v) for a, v in walker.items()}, dict(ws, marks=[GEM])),
        ("walker with a patch, read as a sheet", {a: _with_patch(v) for a, v in walker.items()},
         dict(ws, sheets={"idle", "move"})),
        ("flier read as a sheet", flier, dict(fs, sheets={"idle", "move"})),
    ]
    for label, loops, kw in quiet:
        warns = []
        f = pac.check(loops, pac.Spec(**kw), warns)
        loud = [x for x in f] + [x for x in warns if x.split(":")[1].strip() in LATER]
        print(f"clean {label} passes" + ("" if not loud else ": NO, FALSE ALARM: " + "; ".join(x[:120] for x in loud[:3])))
        ok &= not loud
    return ok


def _crawler(contacts, top=2, w=30, h=11):
    """A plain body (rows top..6, columns 6-21) on 1-px legs that end on the ground row 10 at the given columns:
    the shape of a many-legged crawler's frame, for the skate and gait readings alone."""
    f = [[None] * w for _ in range(h)]
    for y in range(top, 7):
        for x in range(6, 22):
            f[y][x] = FUR
    for x in contacts:
        for y in range(7, h):
            f[y][x] = INK
    return f


def crawler_quiet():
    """Good loop shapes of accepted creatures the skate and gait warnings must leave alone (checked on their own:
    the crawler is only a body on legs). Feet merged on the ground row that split apart, one going back 2 px and
    one forward 1 (a many-legged sheet's legs), are not a foot sliding; a shell whose top shifts a pixel at uneven
    times has no wave count to judge."""
    ok = True
    spec = pac.Spec(eye=EYE)
    poses = [[13, 19], [11, 14, 19], [11, 14, 19], [12, 13, 19]]   # the far foot at 19 stays planted
    split = {"move": [_crawler(p) for p in poses for _ in range(2)]}
    warns = []
    pac.skate(split, spec, warns)
    print("clean crawler, two merged feet splitting apart, passes" +
          ("" if not warns else ": NO, FALSE ALARM: " + warns[0][:120]))
    ok &= not warns
    pops = [0, 0, -1, 0, 0, -1, 0, 0, 0, -1, 0, 0]          # three 1-px pops, 3, 4 and 5 poses apart
    shell = {"move": [_crawler([8, 12, 16, 20], top=2 + d) for d in pops for _ in range(2)]}
    warns = []
    pac.gait(shell, spec, warns)
    print("clean crawler, its shell popping at uneven times, passes" +
          ("" if not warns else ": NO, FALSE ALARM: " + warns[0][:120]))
    ok &= not warns
    edge = [_crawler([8, 12, 16, 20]) for _ in range(24)]   # an outline on the body's top, a fill below
    for f in edge:
        f[2][6:22] = [INK] * 16
    for k in (9, 10):                                     # the fill under the outline takes a tone between the
        edge[k][3][10] = "#6e5040"                        # two for 2 frames: the edge blending, not a speck
    warns = []
    pac.orphans({"idle": edge}, spec, warns)
    warns = [w for w in warns if w.startswith("warn: speck:")]
    print("clean crawler, a tone between its outline and fill for 2 frames, passes" +
          ("" if not warns else ": NO, FALSE ALARM: " + warns[0][:120]))
    ok &= not warns
    return ok


def later_cases():
    """(kind, who, fn): fn breaks the creature (and may return more Spec arguments); kind must be reported, as a
    fault or a warning."""
    cases = []

    def held_pop(L):                                      # on twos, both frames of one pose knocked 3 px sideways
        L["move"] = _on(L["move"], 2)
        for k in (12, 13):
            L["move"][k] = _sx(L["move"][k], 3)
    cases.append(("jump", "walker", held_pop))

    def held_pop3(L):                                     # on threes, all three frames of one pose knocked 2 px
        L["move"] = _on(L["move"], 3)
        for k in (18, 19, 20):
            L["move"][k] = _sx(L["move"][k], 2)
    cases.append(("jump", "walker", held_pop3))

    def foot_forward(L):                                  # one planted foot nudged a pixel forward on one frame
        L["move"][1] = walker_frame(1 / 16, "move", nudge=1)
    cases.append(("skate", "walker", foot_forward))

    def undeclared(L):                                    # the good bite, not declared an action: its key is a
        L["bite"] = bite(GOOD_BITE)                       # dropped rate
    cases.append(("choppy", "walker", undeclared))

    def strike_case(poses):
        def fn(L):
            L["bite"] = bite(poses)
            return {"actions": {"bite": "strike:right"}}
        return fn
    cases.append(("counter", "walker", strike_case(                  # it rises but never draws back
        [(0, 0, 3), (0, -1, 3), (0, -2, 3), (0, -3, 9), (3, 1, 3), (2, 1, 3), (2, 0, 3), (1, 0, 3)])))
    cases.append(("strike", "walker", strike_case(                   # the strike spread over even 1-px steps
        [(0, 0, 3), (-1, -1, 3), (-1, -2, 3), (-1, -3, 9), (0, -2, 3), (1, -1, 3), (2, 0, 3), (3, 1, 3),
         (2, 1, 3), (1, 0, 3)])))
    cases.append(("recover", "walker", strike_case(                  # straight back to rest from the contact
        [(0, 0, 3), (-1, -1, 3), (-1, -2, 3), (-1, -3, 9), (3, 1, 9)])))
    cases.append(("stage", "walker", strike_case(                    # a strike that barely changes the shape
        [(0, 0, 4), (-1, 0, 4), (-1, -1, 8), (1, 0, 4), (1, 1, 4), (0, 1, 4)])))
    cases.append(("piston", "walker", strike_case(                   # back and forth on one straight line
        [(0, 0, 3), (-1, 0, 3), (-2, 0, 3), (-3, 0, 9), (3, 0, 3), (2, 0, 3), (1, 0, 3)])))

    def leap_case(poses, tailless=()):
        def fn(L):
            L["leap"] = leap(poses, tailless)
            return {"actions": {"leap": "jump"}}
        return fn
    cases.append(("gravity", "walker", leap_case(                    # it falls at an even pace
        [(0, 0, 2), (0, 2, 6), (2, 0, 2), (3, 0, 2), (4, 0, 2), (3, 0, 2), (2, 0, 2), (1, 0, 2), (0, 2, 2),
         (0, 1, 2)])))
    cases.append(("squash", "walker", leap_case(GOOD_LEAP, tailless={7})))   # the landing squash narrows
    cases.append(("recover", "walker", leap_case(GOOD_LEAP[:8])))      # from the landing straight to rest

    def boiled(L):                                        # a sheet: each move pose held 3, then the same pose with a
        poses = [walker_frame(k / 16, "move") for k in range(16)]   # few outline pixels redrawn held 3 (5 real
        out = []                                          # poses a second read as 10)
        for i, f in enumerate(poses):
            nxt = poses[(i + 1) % 16]
            edge = [(x, y) for y, r in enumerate(f) for x, v in enumerate(r) if v == INK and nxt[y][x] == INK]
            b = copy.deepcopy(f)
            for x, y in edge[::max(1, len(edge) // 6)][:6]:
                b[y][x] = DARK
            out += _on([f], 3) + _on([b], 3)
        L["move"] = out
    cases.append(("boil", "walker", boiled))

    def one_bob(L):
        L["move"] = [walker_frame(k / 16, "move", bobs=1) for k in range(16)]
    cases.append(("gait", "walker", one_bob))

    def odd(L):                                           # 15 poses: one dropped from the 16
        L["move"] = L["move"][:15]
    cases.append(("gait", "walker", odd))

    def rigid_head(L):                                    # the head rides the body on its own frame: no lag
        L["move"] = [walker_frame(k / 16, "move", nods=False) for k in range(16)]
        return {"parts": {"move": _labels(16, nods=False)}, "squash": {LEG_L}}
    cases.append(("lag", "walker", rigid_head))

    def shrunk(L):                                        # the body part loses a row on one frame
        lab = _labels(16)
        y = max(y for y, r in enumerate(lab[5]) if BODY_L in r) - 1
        lab[5][y] = [None if v == BODY_L else v for v in lab[5][y]]
        return {"parts": {"move": lab}, "squash": {LEG_L}}
    cases.append(("volume", "walker", shrunk))

    def stray_colour(L):
        L["move"][5][10][15] = "#ff00ff"
        return {"palette": {v for a in L for f in L[a] for r in f for v in r if v not in (None, "#ff00ff")}}
    cases.append(("palette", "walker", stray_colour))

    def blended(L):                                       # a sheet: a mid tone on the fur/belly line in one frame
        L["idle"][5][11][15] = MID
        return {"sheets": {"idle"}}
    cases.append(("blend", "walker", blended))

    def speck(L):                                         # one body pixel blinks another colour on one frame
        L["idle"][9][10][15] = "#6a4a3a"
    cases.append(("speck", "walker", speck))

    def scattered(L):                                     # six lone pixels on one frame
        for x, y in ((10, 10), (13, 10), (16, 10), (19, 10), (12, 13), (17, 13)):
            L["idle"][5][y][x] = "#6a4a3a"
    cases.append(("orphans", "walker", scattered))

    def thick(L):                                         # the outline over the back doubled on one frame
        f = L["idle"][4]
        for x in range(9, 22):
            y = next(y for y in range(len(f)) if f[y][x] is not None)
            f[y - 1][x] = INK
    cases.append(("doubles", "walker", thick))

    def drifted(L):                                       # the approved drawing's snout is not the rest render's
        return {"ref": walker_frame(0, "idle", cut=True)}
    cases.append(("drift", "walker", drifted))

    def gem_lost(L):
        for a in L:
            L[a] = _with_gem(L[a])
        L["move"][5] = [[FUR if v == GEM else v for v in r] for r in L["move"][5]]
        return {"marks": [GEM]}
    cases.append(("mark", "walker", gem_lost))

    def gem_jump(L):
        for a in L:
            L[a] = _with_gem(L[a])
        L["move"][5] = _with_gem([walker_frame(5 / 16, "move")], dx=2)[0]   # the gem 2 px off for one frame
        return {"marks": [GEM]}
    cases.append(("mark", "walker", gem_jump))

    def banded(L):                                        # the torso's rear half raised a pixel on its own for
        L["idle"] = [walker_frame(k / 24, "idle", band=1 if 6 <= k < 18 else 0) for k in range(24)]   # 12 frames
    cases.append(("split", "walker", banded))

    def lone_head(L):                                     # the head held, then stepping a pixel down and back up,
        L["idle"] = [walker_frame(k / 24, "idle", nods=False, lunge=(0, 1 if 3 <= k < 15 else 0))   # each after a
                     for k in range(24)]                  # 12-frame hold, on frames where the tail holds too
        return {}
    cases.append(("hitch", "walker", lone_head))

    def shield_off(L):                                    # a sheet cell drops its patch
        L["move"] = _with_patch(L["move"])
        L["move"][7] = walker_frame(7 / 16, "move")
        return {"sheets": {"move"}}
    cases.append(("swap", "walker", shield_off))
    return cases


def _strip(frames, path):
    """Frames (rows of #rrggbb or None) saved side by side as one RGBA strip."""
    h, w = len(frames[0]), len(frames[0][0])
    im = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        for y, r in enumerate(f):
            for x, v in enumerate(r):
                if v is not None:
                    im.putpixel((k * w + x, y), pac.hexrgb(v) + (255,))
    im.save(path)


def cli(walker):
    """The command line: colour options in any case with or without '#', a decimal --fps, a strip whose frames are
    not square refused unless --frame or --frames cuts it, --help exiting 0 and a usage error exiting 2."""
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for a in ("idle", "move"):
            _strip(walker[a], os.path.join(tmp, a + ".png"))
        loops = ["--loop", "idle=" + os.path.join(tmp, "idle.png"), "--loop", "move=" + os.path.join(tmp, "move.png")]
        base = loops + ["--out", os.path.join(tmp, "out")]

        def run_main(args):
            buf, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                code = pac.main(args)
            return code, buf.getvalue() + err.getvalue()

        def case(name, cond, got):
            nonlocal ok
            print(f"cli      {name:48s} {'ok' if cond else 'WRONG'}" + ("" if cond else f"  ({got})"))
            ok &= bool(cond)
        code, text = run_main(base + ["--frame", "34", "--eye", "#ffcc33"])
        case("the clean walker passes from strips", code == 0, text)
        code, text = run_main(base + ["--frame", "34", "--eye", "FFCC33"])
        case("--eye FFCC33 is read as #ffcc33", code == 0 and "eye:" not in text, text)
        lower = run_main(base + ["--frame", "34", "--eye", "#ffcc33", "--ink", "#1a1216"])[0]
        upper = run_main(base + ["--frame", "34", "--eye", "#ffcc33", "--ink", " 1A1216 "])[0]
        case("--ink in upper case without # as in lower", lower == upper, (lower, upper))
        code, text = run_main(["--loop", "idle=" + os.path.join(tmp, "idle.png"), "--frames", "24", "--eye", "#ffcc33",
                               "--out", os.path.join(tmp, "out")])
        case("--frames 24 cuts the idle strip into 24", code == 0, text)
        code, text = run_main(base + ["--frame", "34", "--fps", "12.5", "--name", "slow"])
        case("--fps 12.5 runs", code in (0, 1) and os.path.exists(os.path.join(tmp, "out", "slow_check.gif")), text)
        code, text = run_main(base)
        case("a non-square strip with no --frame is refused", code == 2 and "--frame" in text, (code, text[-200:]))
        code, text = run_main(base + ["--frames", "7"])
        case("--frames that does not divide the strip refused", code == 2, (code, text[-200:]))
        code, text = run_main(base + ["--frame", "34", "--eye", "#ffcc3"])
        case("a malformed colour is a usage error", code == 2, (code, text[-200:]))
        code, text = run_main(base + ["--frame", "34", "--bogus"])
        case("an unknown option is a usage error", code == 2, (code, text[-200:]))
        case("--help exits 0", run_main(["--help"])[0] == 0 and run_main(["-h"])[0] == 0, "")
        case("no loop is a usage error", run_main([])[0] == 2, "")
        mixed = os.path.join(tmp, "mixed")
        os.mkdir(mixed)
        code, text = run_main(["--loop", "idle=" + mixed])
        case("an empty frame folder is a usage error", code == 2 and "no frames" in text, text)
        Image.new("RGB", (8, 8)).save(os.path.join(mixed, "00.png"))
        Image.new("RGB", (9, 8)).save(os.path.join(mixed, "01.png"))
        code, text = run_main(["--loop", "idle=" + mixed, "--out", os.path.join(tmp, "mixed-out")])
        case("unequal frame sizes are reported by the CLI",
             code == 1 and "size:" in text and "(8, 8)" in text and "(9, 8)" in text, text)
        pair = os.path.join(tmp, "pair.png")
        Image.new("RGB", (16, 8)).save(pair)
        code, text = run_main(["--loop", "idle=" + pair, "--parts", "idle=" + mixed])
        case("a size mismatch after the first part frame is refused", code == 2 and "--parts" in text, text)
        # a GIF whose held poses are merged into longer images: read at its own timing, every hold kept
        held = [f for f in walker["move"] for _ in range(2)]
        ims = []
        for f in held:
            im = Image.new("RGBA", (len(f[0]), len(f)), (0, 0, 0, 0))
            for y, r in enumerate(f):
                for x, v in enumerate(r):
                    if v is not None:
                        im.putpixel((x, y), pac.hexrgb(v) + (255,))
            ims.append(im)
        gpath = os.path.join(tmp, "held.gif")
        delays = [(30, 40, 30)[k % 3] for k in range(len(ims))]
        ims[0].save(gpath, save_all=True, append_images=ims[1:], duration=delays, loop=0, disposal=2)
        with Image.open(gpath) as g:
            images = g.n_frames
        got = pac.load(gpath, fps=30)
        case("a GIF's merged holds are expanded by duration", images < len(held) and got == held,
             (images, len(got), len(held)))
        timed = os.path.join(tmp, "timed.gif")
        poses = [Image.new("RGB", (8, 5), (20 * k, 0, 0)) for k in range(10)]
        poses[0].save(timed, save_all=True, append_images=poses[1:], duration=50)
        raw = pac.load(timed)
        ticks = pac.load(timed, fps=30)
        expected = [f for k, f in enumerate(raw) for _ in range(2 if k % 2 == 0 else 1)]
        case("500 ms of distinct GIF poses take 15 game frames", len(ticks) == 15 and ticks == expected, len(ticks))
        poses[0].save(timed, save_all=True, append_images=poses[1:], duration=10)
        case("sub-frame GIF poses fit the available ticks", len(pac.load(timed, fps=30)) == 3, "")
        poses[0].save(timed, duration=500)
        case("a one-image GIF keeps its canvas and duration", pac.load(timed, fps=30) == [raw[0]] * 15, "")
        for fps, total_ms in ((30, 670), (60, 330), (120, 170)):
            pac.gif({"idle": raw}, timed, fps=fps, Z=1)
            with Image.open(timed) as preview:
                delays = [f.info["duration"] for f in ImageSequence.Iterator(preview)]
            case(f"preview at {fps} fps keeps its total duration",
                 sum(delays) == total_ms and all(ms >= 10 for ms in delays), delays)
        pac.gif({"idle": raw[:3], "move": raw[:5]}, timed, fps=10, Z=1)
        with Image.open(timed) as preview:
            repeat = preview.info.get("loop")
            pairs = []
            for pose in ImageSequence.Iterator(preview):
                panel = pose.convert("RGB")
                pairs.append((panel.getpixel((3, 2))[0], panel.getpixel((17, 2))[0]))
        expected = [(20 * (k % 3), 20 * (k % 5)) for k in range(15)]
        case("3- and 5-frame loops wrap together", repeat == 0 and pairs == expected, (repeat, pairs))
        pac.gif({"idle": raw[:7], "move": raw[:9]}, timed, fps=10, Z=1)
        with Image.open(timed) as preview:
            case("long combined periods produce a bounded one-shot preview",
                 "loop" not in preview.info and preview.n_frames == 18, preview.info)
        _strip(bite(GOOD_BITE), os.path.join(tmp, "bite.png"))
        _strip([walker_frame(k / 16, "move", labels=True) for k in range(16)], os.path.join(tmp, "parts.png"))
        _strip([walker_frame(0, "idle")], os.path.join(tmp, "ref.png"))
        _strip(walker["idle"][:1] + walker["move"][:1], os.path.join(tmp, "pal.png"))
        later = base + ["--loop", "bite=" + os.path.join(tmp, "bite.png"), "--frame", "34", "--eye", "#ffcc33",
                        "--action", "bite:strike:right", "--speed", "0.4", "--parts",
                        "move=" + os.path.join(tmp, "parts.png"), "--squash", LEG_L, "--palette",
                        os.path.join(tmp, "pal.png"), "--ref", os.path.join(tmp, "ref.png"), "--sheet", "move",
                        "--glow", "#fff4c8"]
        code, text = run_main(later)
        case("the later options run clean (action, parts, palette, ref)", code == 0 and "warn:" not in text
             and "the road scrolls 0.4" in text and "strike at frame" in text, text[-400:])
        code, text = run_main(base + ["--frame", "34", "--action", "move:strike:sideways"])
        case("--action with a bad direction is a usage error", code == 2, (code, text[-200:]))
        code, text = run_main(base + ["--frame", "34", "--action", "bite:strike"])
        case("--action for a loop not given is a usage error", code == 2, (code, text[-200:]))
        code, text = run_main(base + ["--frame", "34", "--parts", "move=" + os.path.join(tmp, "ref.png")])
        case("--parts whose frames do not match the loop refused", code == 2, (code, text[-200:]))
        code, text = run_main(["--loop", "idle=" + os.path.join(tmp, "idle.png"), "--loop", "move=" + gpath,
                               "--frame", "34", "--eye", "#ffcc33", "--out", os.path.join(tmp, "out")])
        case("a GIF loop runs from the command line", code in (0, 1) and "error" not in text, text[-200:])
    slow = pac.cadence({"move": [f for f in walker["move"] for _ in range(2)]}, pac.Spec(eye=EYE, fps=12))
    case("choppy's advice follows --fps (12 fps: hold 1 frame)",
         any("hold each pose 1 frame at most" in x for x in slow), slow)
    marks = pac.fault_frames(["jump: move[8] is knocked 4 px sideways", "snap: idle stands dead still 30 frames, "
                              "then changes 40% of the figure at once (frame 3, score 1)", "still: move changes 1%"],
                             {"idle": [None] * 24, "move": [None] * 16})
    case("fault lines name their frames for the contact sheet", marks == {"move": {8}, "idle": {3, 4}}, marks)
    held = pac.fault_frames(["jump: move[6-7] (a held pose) is knocked 3 px sideways out of step",
                             "jump: idle[22-1] (a held pose) is knocked 2 px sideways out of step"],
                            {"idle": [None] * 24, "move": [None] * 16})
    case("a held pose's fault names every frame of it", held == {"move": {6, 7}, "idle": {22, 23, 0, 1}}, held)
    return ok


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--sheets") + 1] if "--sheets" in sys.argv else None
    if out:                                               # the test creatures drawn, to look at them
        w, f = creatures()
        pac.gif(w, os.path.join(out, "walker.gif"))
        pac.gif(f, os.path.join(out, "flier.gif"))
    sys.exit(0 if run("--verbose" in sys.argv) else 1)
