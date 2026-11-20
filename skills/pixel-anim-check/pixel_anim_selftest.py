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

from PIL import Image

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


def walker_frame(t, kind, bob=True, rise=None, lead=False, cut=False):
    """A four-legged walker 34x22 standing on row 20: legs swing in the move (the forward foot lifted) and the body
    rises a pixel as they pass under it, the head nods and the tail wags in both loops.
    For the cases: rise forces the body's rise (0 or 1, the legs stretching under it); lead paints the fur/belly
    line's row 11 a mid tone (MID), the sub-pixel in-between of a 1-px rise or fall; cut takes the head's front
    column and lowest row off (a snout cut flat, as a redrawn sheet cell may)."""
    g = [[None] * 34 for _ in range(22)]
    s = math.sin(2 * math.pi * t)
    up = 1 if bob and kind == "move" and abs(s) < 0.5 else 0
    if rise is not None:
        up = rise
    for i, hx in enumerate((10, 13, 18, 21)):            # back pair, front pair; diagonal pairs in step
        sw = (s if i in (0, 3) else -s) if kind == "move" else 0.0
        lift = 1 if kind == "move" and sw > 0.3 else 0
        _line(g, hx, 14 - up, hx + round(2 * sw), 19 - lift, "#a8744e", 2)
    _disc(g, 15.5, 11.5 - up, 8, 3.6, FUR, BELLY)
    if lead:
        for x in range(34):
            if g[11][x] in (FUR, BELLY):
                g[11][x] = MID
    wag = round(2 * math.sin(2 * math.pi * t + 1.0))
    _line(g, 7, 10 - up, 3, 6 + wag - up, FUR, 2)
    nod = round(math.sin(2 * math.pi * t * (2 if kind == "move" else 1)))
    head = [(x, y) for y in range(22) for x in range(34) if ((x - 25.5) / 3.6) ** 2 + ((y - 7.5 - nod + up) / 3.2) ** 2 <= 1]
    _disc(g, 25.5, 7.5 + nod - up, 3.6, 3.2, FUR)
    if cut:
        fx, fy = max(x for x, _ in head), max(y for _, y in head)
        for x, y in head:
            if (x == fx or y == fy) and g[y][x] == FUR:
                g[y][x] = None
    g[7 + nod - up][27] = EYE
    return _outline(g)


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
        L["move"] = [pac._shifted(walker_frame(p / 32, "move", bob=False), -1 if (p // 2) % 2 else 0)
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

    for kind, who, fn in cases:
        L = copy.deepcopy(walker if who == "walker" else flier)
        fn(L)
        f = pac.check(L, ws if who == "walker" else fs)
        hit = [x for x in f if x.startswith(kind + ":")]
        print(f"{kind:8s} on {who:7s} {'caught' if hit else 'MISSED'}" + (f"  (also: {f[0]})" if f and not hit else ""))
        ok &= bool(hit)
    ok &= cli(walker)
    print("selftest:", "all hold" if ok else "FAILED")
    return ok


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
        ims[0].save(gpath, save_all=True, append_images=ims[1:], duration=33, loop=0, disposal=2)
        with Image.open(gpath) as g:
            images = g.n_frames
        got = pac.load(gpath, fps=30)
        case("a GIF's merged holds are expanded by duration", images < len(held) and got == held,
             (images, len(got), len(held)))
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
    return ok


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--sheets") + 1] if "--sheets" in sys.argv else None
    if out:                                               # the test creatures drawn, to look at them
        w, f = creatures()
        pac.gif(w, os.path.join(out, "walker.gif"))
        pac.gif(f, os.path.join(out, "flier.gif"))
    sys.exit(0 if run("--verbose" in sys.argv) else 1)
