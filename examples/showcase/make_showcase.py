"""Build the README's three pictures from the showcase creatures, with the repo's own tools.

    python examples/showcase/make_showcase.py            # writes docs/img/hero.gif, check.png, parts.png
    python examples/showcase/make_showcase.py --out DIR  # writes them to DIR instead

  hero.gif    the beast, the bird and the lizard side by side, each over its own stretch of road: their idles, then
              their moves (the road under each scrolling at that creature's ROAD_SPEED, which a planted foot keeps
              pace with), then their attacks, each running on into its idle; the row at the top names the
              loop playing. 30 fps (every pose held 2 frames), scaled 2x.
  check.png   pixel_anim_check run on the beast's walk twice: once with the eye lost on one pose (painted over,
              as when a head moves without its eye), once as it is. The lines shown are the check's own.
  parts.png   body_parts.py run on the beast's drawing (beast/beast_art_8x.png) with the bones in beast/marks.json;
              the parts it cut, tinted and named.

It first checks every loop of every creature with pixel_anim_check, with the options each animate.py's docstring
gives (the part strips, the palette and the drawing included), and stops unless each has 0 faults. It reads the
strips as they are on disk (run a creature's animate.py first to rebuild them and its check/ files). Needs Python
3.8+, numpy and Pillow; every word in the pictures is pixfont.py, the pixel font beside this script, so they come out
the same on every machine. check.png and parts.png are drawn by showcase_stills.py."""
import argparse
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "skills", "pixel-anim-check"))
sys.path.insert(0, os.path.join(ROOT, "skills", "pixel-animate"))
import pixel_anim_check as pac                            # noqa: E402
import pixfont                                            # noqa: E402

LOOPS = ("idle", "move", "attack")
# what pixel_anim_check is told of each creature: the same options as the check command in each animate.py's
# docstring. Paths are inside the creature's folder; every loop also has its part strip, check/<key>_<loop>_parts.png.
CREATURES = {
    "beast": dict(frame=93, eye="#f2aa3c", ink=("#120f19", "#191a2e", "#242844", "#323a5c", "#404e78", "#566594"),
                  effects=("#fff9e6", "#ffd25e", "#c3cdf0", "#7d89b8"), action="strike:right", speed=1.0,
                  squash=("#8c8c8c", "#208040", "#909020"), palette="check/beast_palette.png",
                  ref="check/beast_art.png"),
    "bird": dict(frame=86, eye="#22110f", ink=("#0e0a16", "#1f5d68", "#5a1f2c"), flier=True,
                 effects=("#e2f8ff", "#7fb6c8", "#fff0a8"), action="strike:right", speed=1.0,
                 squash=("#3f7fd0", "#24497a", "#c8a040", "#9a6b2f", "#40c0a0", "#d88a3a"),
                 palette="check/bird_palette.png",
                 ref="check/bird_ref.png"),
    "lizard": dict(frame=113, eye="#ffaf2e", ink=("#140f1e", "#2f5634"),
                   effects=("#5e1830", "#8e2347", "#d84a68", "#ff8f97", "#fff4e8", "#ffc0b0"),
                   action="strike:right", speed=0.5, squash=("#208040", "#909020"), palette="check/lizard_art.png",
                   ref="check/lizard_art.png"),
}


# ---- reading the creatures ----------------------------------------------------------------------------------------
def path(key, name):
    return os.path.join(HERE, key, name)


def loops(key):
    return {a: pac.load(path(key, f"{key}_{a}.png"), frame=CREATURES[key]["frame"]) for a in LOOPS}


def spec(key):
    """The check's Spec for a creature, as its command line builds it."""
    c = CREATURES[key]
    need = [c["palette"], c["ref"]] + [f"check/{key}_{a}_parts.png" for a in LOOPS]
    missing = [n for n in need if not os.path.isfile(path(key, n))]
    if missing:
        sys.exit(f"{key}: no {', '.join(missing)} (run {key}/animate.py first)")
    pal = pac.load(path(key, c["palette"]), frames=1)[0]
    return pac.Spec(eye=c["eye"], ink=set(c["ink"]), flier=c.get("flier", False), effects=c["effects"],
                    actions={"attack": c["action"]}, speed=c["speed"],
                    parts={a: pac.load(path(key, f"check/{key}_{a}_parts.png"), frame=c["frame"]) for a in LOOPS},
                    squash=c["squash"], palette={v for r in pal for v in r if v is not None},
                    ref=pac.load(path(key, c["ref"]), frames=1)[0])


def rgba(frame):
    """A frame of hex keys (or None) as an RGBA array."""
    out = np.zeros((len(frame), len(frame[0]), 4), np.uint8)
    for y, r in enumerate(frame):
        for x, v in enumerate(r):
            if v is not None:
                out[y, x] = pac.hexrgb(v) + (255,)
    return out


def paste(canvas, art, x, y):
    """Lay an RGBA array on an RGB array (opaque pixels only) with its top-left at (x, y)."""
    h, w = art.shape[:2]
    on = art[..., 3] > 0
    canvas[y:y + h, x:x + w][on] = art[..., :3][on]


def up(arr, s):
    return np.repeat(np.repeat(arr, s, 0), s, 1)


# ---- hero.gif -----------------------------------------------------------------------------------------------------
SEGMENTS = (("idle", 144), ("move", 64), ("attack", 66))  # frames each: 4.8 s, 2.1 s, 2.2 s
PERIOD = 32                                               # the road's pattern repeats every 32 px, so the scroll a
                                                          # move adds (64 or 32 px) lands back where it began
OUTSIDE = (17, 15, 24)
SKY = [(30, 27, 46), (35, 31, 54), (41, 36, 62), (48, 42, 71)]   # dusk in flat bands, a dithered row between
STAR = (86, 78, 116)
ROAD = dict(edge=(150, 124, 104), notch=(104, 84, 78), near=(112, 90, 82), far=(86, 68, 66), deep=(70, 55, 56),
            pebble=(168, 142, 120), pit=(80, 62, 60))
LIT, DIM = (238, 220, 176), (84, 76, 106)


def schedule(n):
    """(loop, frame) at each frame of the GIF for a creature whose loops have n[loop] frames. Each segment starts
    its loop on frame 0, but for the idle: the attack runs on into the idle, and the idle segment goes on from there
    when the GIF wraps, so nothing jumps at the seam."""
    lens = dict(SEGMENTS)
    att, ni = n["attack"], n["idle"]
    o = (lens["attack"] - att) % ni
    out = [("idle", (o + t) % ni) for t in range(lens["idle"])]
    out += [("move", t % n["move"]) for t in range(lens["move"])]
    out += [("attack", t) if t < att else ("idle", (t - att) % ni) for t in range(lens["attack"])]
    return out


def road(w, rows, rng):
    """A stretch of road `rows` tall, PERIOD-periodic across, wide enough to scroll w px over: its lit edge with a
    few worn notches, the near ground with pebbles, the far ground darker."""
    tile = np.zeros((rows, PERIOD, 3), np.uint8)
    tile[0] = ROAD["edge"]
    tile[1:3] = ROAD["near"]
    tile[3:5] = ROAD["far"]
    tile[5:] = ROAD["deep"]
    tile[2, 1::2] = ROAD["far"]
    tile[4, ::2] = ROAD["deep"]
    for x in (5, 6, 19):
        tile[0, x] = ROAD["notch"]
    for x0 in (2, 11, 24):                                # three pebbles a period, lit on top, a shadow beside
        x, y = x0 + int(rng.integers(0, 4)), int(rng.integers(1, 4))
        tile[y, x:x + 2] = ROAD["pebble"]
        tile[y + 1, x + 1:x + 3] = ROAD["pit"]
    reps = (w + PERIOD) // PERIOD + 1
    return np.tile(tile, (1, reps, 1))


def hero(out_path, order=("beast", "bird", "lizard"), S=2):
    """The three creatures, each in its own lane of sky and road, through SEGMENTS; the 1x scene scaled S times."""
    L = {k: {a: [rgba(f) for f in v] for a, v in loops(k).items()} for k in order}
    boxes = {}
    for k in order:
        alpha = np.any([f[..., 3] > 0 for a in L[k] for f in L[k][a]], 0)
        ys, xs = np.nonzero(alpha)
        boxes[k] = (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1)
    margin, gap, padx, label_h, below = 6, 5, 6, 19, 8
    lift = {k: 3 if CREATURES[k].get("flier") else 1 for k in order}   # rows between its lowest pixel and the road
    sky_h = max(b[3] - b[2] + lift[k] for k, b in boxes.items()) + 4
    G = label_h + sky_h                                   # the road's lit edge: a walker's paws stand on the row above
    H1 = G + below + margin - 2
    lanes, x = {}, margin
    for k in order:
        w = boxes[k][1] - boxes[k][0] + 2 * padx
        lanes[k] = (x, w)
        x += w + gap
    W1 = x - gap + margin
    rng = np.random.default_rng(11)
    scene = np.zeros((H1, W1, 3), np.uint8)
    scene[:] = OUTSIDE
    strips, places = {}, {}
    for k in order:
        x0, w = lanes[k]
        lane = scene[label_h:G + below, x0:x0 + w]
        cuts = [int(sky_h * f) for f in (0.3, 0.55, 0.8)]
        for y in range(sky_h):
            band = sum(y >= c for c in cuts)
            lane[y] = SKY[band]
            if y + 1 in cuts:
                lane[y, y % 2::2] = SKY[band + 1]
        for _ in range(w // 12):                          # a few dim stars
            lane[rng.integers(2, int(sky_h * 0.5)), rng.integers(2, w - 2)] = STAR
        strips[k] = road(w, below, rng)
        for cy, cx in ((0, 0), (0, w - 1), (lane.shape[0] - 1, 0), (lane.shape[0] - 1, w - 1)):
            lane[cy, cx] = OUTSIDE                        # the lane's corners cut
        bx0, _, _, by1 = boxes[k]
        places[k] = (x0 + padx - bx0, G - lift[k] - (by1 - 1))
    plans = {k: schedule({a: len(L[k][a]) for a in LOOPS}) for k in order}
    timeline = [a for a, n in SEGMENTS for _ in range(n)]
    move0 = SEGMENTS[0][1]
    labels = {}
    words = "  ".join(LOOPS)
    for a in LOOPS:                                       # "idle  move  attack", the loop playing lit
        im = Image.new("RGB", (pixfont.width(words), 9), OUTSIDE)
        x = 0
        for word in LOOPS:
            pixfont.draw(im, x, 0, word, LIT if word == a else DIM)
            x += (len(word) + 2) * pixfont.CELL_W
        labels[a] = np.asarray(im)
    frames = []
    for t, seg in enumerate(timeline):
        f = scene.copy()
        f[5:14, margin + 1:margin + 1 + labels[seg].shape[1]] = labels[seg]
        for k in order:
            x0, w = lanes[k]
            off = int(np.floor(max(0, min(t - move0, SEGMENTS[1][1])) * CREATURES[k]["speed"])) % PERIOD
            band = strips[k][:, off:off + w].copy()       # the road scrolls back under a walker going right
            band[0, 0] = band[-1, 0] = band[0, -1] = band[-1, -1] = OUTSIDE
            f[G:G + below, x0:x0 + w] = band
            a, i = plans[k][t]
            paste(f, L[k][a][i], *places[k])
        frames.append(f)
    return write_gif(out_path, frames, S)


def write_gif(out_path, frames, S):
    """One palette for the whole GIF; a frame equal to the one before is merged into it, with their whole time, each
    image's start and end put on the 10 ms grid a GIF stores (frames at 30 fps: 30, 40, 30 ms)."""
    colours = sorted({tuple(c) for f in frames for c in f.reshape(-1, 3)})
    if len(colours) > 256:
        sys.exit(f"hero: {len(colours)} colours, over the GIF's 256")
    lut = {c: i for i, c in enumerate(colours)}
    pal = [v for c in colours for v in c]
    out, starts = [], []
    for i, f in enumerate(frames):
        if not out or not np.array_equal(f, frames[i - 1]):
            out.append(f)
            starts.append(i)
    edges = [int(round(k * 100 / 30)) * 10 for k in starts + [len(frames)]]
    durations = [b - a for a, b in zip(edges, edges[1:])]
    ims = []
    for f in out:
        idx = np.array([lut[tuple(c)] for c in f.reshape(-1, 3)], np.uint8).reshape(f.shape[:2])
        im = Image.fromarray(up(idx, S), "P")
        im.putpalette(pal)
        ims.append(im)
    ims[0].save(out_path, save_all=True, append_images=ims[1:], duration=durations, loop=0, optimize=False,
                disposal=1)
    return ims[0].size, len(ims), sum(durations)


# ---- writing ------------------------------------------------------------------------------------------------------
def unchanged(new, old):
    """The picture on disk holds the same pixels (every GIF frame and its time too) as the one just built: then it
    is left alone, so another zlib or Pillow build does not churn the tracked files."""
    if not os.path.exists(old):
        return False
    a, b = Image.open(new), Image.open(old)
    if a.size != b.size or getattr(a, "n_frames", 1) != getattr(b, "n_frames", 1):
        return False
    for k in range(getattr(a, "n_frames", 1)):
        a.seek(k)
        b.seek(k)
        if a.info.get("duration") != b.info.get("duration") or \
                not np.array_equal(np.asarray(a.convert("RGBA")), np.asarray(b.convert("RGBA"))):
            return False
    return True


def main(argv):
    ap = argparse.ArgumentParser(prog="make_showcase.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "img"), metavar="DIR",
                    help="where the pictures go (default: docs/img)")
    out = os.path.abspath(ap.parse_args(argv).out)
    os.makedirs(out, exist_ok=True)
    import showcase_stills                                # after the paths above are set
    for key in CREATURES:                                 # the pictures show clean animations, or none at all
        warns = []
        faults = pac.check(loops(key), spec(key), warns)
        if faults:
            sys.exit(f"{key}: {len(faults)} fault(s), first: {faults[0]}  (fix the creature before the pictures)")
        print(f"{key}: 0 fault(s), {len(warns)} warning(s)")
    for name, build in (("hero.gif", hero), ("check.png", showcase_stills.check_png),
                        ("parts.png", showcase_stills.parts_png)):
        target = os.path.join(out, name)
        tmp = target + ".new" + os.path.splitext(name)[1]
        size = build(tmp)[0]
        if unchanged(tmp, target):
            os.remove(tmp)
            print(f"same    {name}")
        else:
            os.replace(tmp, target)
            print(f"wrote   {name} ({size[0]}x{size[1]}, {os.path.getsize(target) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
