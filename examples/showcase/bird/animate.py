"""Animate the tuftwing (creature.py) by the pixel-animate method: pose the cut parts, bring every frame down on one
fixed grid, draw the outline last and put the eye back whole.

    python animate.py            # writes bird_idle.png (48 frames), bird_move.png (32 frames), bird_art_8x.png
    python animate.py --poses    # also prints each loop's pose per clock tick (the rig's numbers, before rendering)

Both loops play at 30 fps, every pose held 2 frames (one clock, `k // 2`), so the bird updates 15 times a second.

How a frame is made:
  1. The wing is one of its five drawn keys (creature.WINGS), picked by the stroke s and moved by whole pixels with
     the body: no resampling, so its feather lines stay as drawn. The far wing is the same key a tone darker.
  2. The parts that turn (the tail's root and its three fan feathers, the head, the crest) are sampled at REF x the
     game size through their pose (turns about their pivot in 1.5 degree steps, children through their parents)
     and brought down on the frame's own grid: a game pixel takes the colour most of its REF x REF samples hold.
     A part that only moves by whole pixels comes back exactly as drawn.
  3. Parts are laid down back to front (creature.GROUPS), each group inside its own one-pixel outline. Outline
     pixels on edges facing the light (air above or left, plumage below or right) take a lighter outline: a dark
     blue over blue, a rust over the breast and beak (the selective outline).
  4. The beak follows the head by whole pixels; the eye is laid down whole at the head's place; the ground shadow
     keeps its bottom row's columns and fades at its ends while the body is up.

The motion (pixel-animate section 3):
  wings    side-on, through the keys +1, +0.5, 0, -0.5, -1 and back: up, edge-on, then under the belly with the
           underside showing, a new drawing every tick (8 a beat). The far wing trails the near one by a tick. The
           move beats twice in 32 frames. The idle beats as deep (pixel-animate: slower, never shallower) but holds a
           glide between beats, wings raised, for 4 ticks: 2 beats in 48 frames, a calmer hover.
  lift     the body rises one whole pixel on the downstroke (the edge-on and down keys), never a fraction: a lift
           peaking 0.5-0.9 px reads as a tick. The head follows a tick late (a nod).
  tail     a chain: the root dips a tick after the body rises, the fan a tick after the root, further, and the fan's
           three feathers spread as it dips and close as it rises.
  head     the idle looks about: one slow tilt a loop, beak up then down, about the eye (so the eye stays on its
           row); the move nods with the beat. The crest follows the head a tick late and is thrown back as the
           body rises.

Check (from this folder):
  python ../../../skills/pixel-anim-check/pixel_anim_check.py --loop idle=bird_idle.png --loop move=bird_move.png \
         --frame 50 --eye "#120c1c" --ink "#1b1424,#2b4180,#8c3a2e" --flier --shadow "#3a3348,#544b63" \
         --out check --name bird
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature as C                                       # noqa: E402

REF = 8                                                    # reference px per game px
HOLD = 2                                                   # frames each pose is held (the loops play at 30 fps)
STEP = 1.5                                                 # degrees: every turn moves in these steps
CHARS = list(C.PALETTE)
IDX = {ch: i + 1 for i, ch in enumerate(CHARS)}            # 0 is empty

STROKE = [1.0, 0.5, 0.0, -0.5, -1.0, -0.5, 0.0, 0.5]       # the wing key on each tick of a beat
UP_TICKS = {2, 3, 4}                                       # the beat's ticks with the body up (the downstroke)
GLIDE_TAIL = [(-1.5, -3.0, 3.0), (-3.0, -6.0, 6.0), (-1.5, -4.5, 7.5), (0.0, -1.5, 4.5)]   # root, fan, spread
LOOPS = {
    # frames, wing beats a loop, ticks of glide (wings held raised) after each beat
    "idle": dict(n=48, beats=2, glide=4),
    "move": dict(n=32, beats=2, glide=0),
}


# ---- the parts as arrays -----------------------------------------------------------------------------------------
def _grid(layer, remap=None):
    g = np.zeros((C.H, C.W), np.int16)
    for (x, y), ch in C.pixels(layer).items():
        g[y, x] = IDX[(remap or {}).get(ch, ch)]
    return g


GRIDS = {name: _grid(layer) for name, layer in C.PARTS.items()}
WING_GRIDS = {s: _grid(layer) for s, layer in C.WINGS.items()}
FAR_GRIDS = {s: _grid(layer, C.FAR_TONES) for s, layer in C.WINGS.items()}


# ---- transforms (3x3 matrices on frame coordinates, y down) -----------------------------------------------------
def tr(dx, dy):
    return np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], float)


def rot(deg, p):
    t = np.radians(deg)
    c, s = np.cos(t), np.sin(t)
    r = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)
    return tr(*p) @ r @ tr(-p[0], -p[1])


_YS, _XS = np.mgrid[0:C.H * REF, 0:C.W * REF]
_XS = (_XS + 0.5) / REF
_YS = (_YS + 0.5) / REF


def sample(grid, T):
    """The part posed by T (local -> frame), brought down to game pixels: (mask, colour index)."""
    if np.allclose(T[:2, :2], np.eye(2)) and np.allclose(T[:2, 2], np.round(T[:2, 2])):
        return shift(grid, int(round(T[0, 2])), int(round(T[1, 2])))
    M = np.linalg.inv(T)
    lx = M[0, 0] * _XS + M[0, 1] * _YS + M[0, 2]
    ly = M[1, 0] * _XS + M[1, 1] * _YS + M[1, 2]
    ix, iy = np.floor(lx).astype(int), np.floor(ly).astype(int)
    ok = (ix >= 0) & (ix < C.W) & (iy >= 0) & (iy < C.H)
    big = np.zeros(ix.shape, np.int16)
    big[ok] = grid[iy[ok], ix[ok]]
    blocks = big.reshape(C.H, REF, C.W, REF).transpose(0, 2, 1, 3).reshape(C.H, C.W, REF * REF)
    counts = np.stack([(blocks == i).sum(2) for i in range(1, len(CHARS) + 1)], 2)
    mask = counts.sum(2) * 2 >= REF * REF
    col = counts.argmax(2) + 1
    return mask, np.where(mask, col, 0)


def shift(grid, dx, dy):
    """A whole-pixel move: the drawing exactly as drawn."""
    out = np.zeros_like(grid)
    H, W = grid.shape
    ys, xs = np.nonzero(grid)
    ok = (ys + dy >= 0) & (ys + dy < H) & (xs + dx >= 0) & (xs + dx < W)
    out[ys[ok] + dy, xs[ok] + dx] = grid[ys[ok], xs[ok]]
    return out > 0, out


# ---- poses ---------------------------------------------------------------------------------------------------
def q(deg):
    """A turn rounded to whole STEP degrees."""
    return round(deg / STEP) * STEP


def pose(loop, t):
    """The rig's numbers at clock tick t (each tick is HOLD frames)."""
    L = LOOPS[loop]
    ticks = L["n"] // HOLD
    tpb = len(STROKE) + L["glide"]                         # ticks a beat, the glide included

    def phase(tick):                                       # the tick's place in its beat's stroke (glide: 0)
        k = tick % tpb
        return k if k < len(STROKE) else 0

    def up(tick):
        return 1 if phase(tick) in UP_TICKS and tick % tpb < len(STROKE) else 0

    s = STROKE[phase(t)]
    far = STROKE[phase(t - 1)]
    lift = up(t)
    nod = lift - up(t - 1)                                 # the head rises and sinks a tick after the body
    dip1, dip2 = up(t - 1), up(t - 2)                      # the tail's chain: root a tick late, fan two
    if loop == "idle":
        head = q(3.0 * np.sin(2 * np.pi * (t + 0.5) / ticks))                     # one slow look a loop
        crest = q(-6.0 * dip1 + 3.0 * np.sin(2 * np.pi * (t - 2 + 0.5) / ticks))
        g = (t % tpb) - len(STROKE)                        # the glide's tick, or negative while beating
        if g >= 0:                                         # gliding: the fan lifts, spreads and settles
            tail_root, tail_fan, spread = GLIDE_TAIL[g]
        else:
            tail_root = q(4.5 * dip1)
            tail_fan = q(6.0 * dip2)
            spread = q(4.5 * dip2 + 3.0 * up(t - 3))
    else:
        head = q(-3.0 * up(t - 1))
        crest = q(-7.5 * dip1 - 1.5)
        tail_root = q(6.0 * dip1)
        tail_fan = q(9.0 * dip2)
        spread = q(6.0 * dip2 + 3.0 * up(t - 3))
    return dict(s=s, far=far, lift=lift, nod=nod, head=head, crest=crest, tail_root=tail_root, tail_fan=tail_fan,
                spread=spread)


# ---- one frame ----------------------------------------------------------------------------------------------
def _ring(mask):
    m = np.zeros_like(mask)
    m[1:, :] |= mask[:-1, :]
    m[:-1, :] |= mask[1:, :]
    m[:, 1:] |= mask[:, :-1]
    m[:, :-1] |= mask[:, 1:]
    return m & ~mask


def _rigid(T, anchor):
    """A whole-pixel move: the anchor's displacement under T, rounded."""
    x, y, _ = T @ np.array([anchor[0], anchor[1], 1.0])
    return tr(round(x - anchor[0]), round(y - anchor[1]))


def frame(p):
    """One frame from a pose: an array of palette indices (0 empty)."""
    body = tr(0, -p["lift"])
    head = body @ tr(0, p["nod"]) @ rot(p["head"], C.PIVOT["head"])
    root = body @ rot(p["tail_root"], C.PIVOT["tail_root"])
    fan = root @ rot(p["tail_fan"], C.PIVOT["tail_fan"])
    T = {
        "tail_root": root,
        "tail_up": fan @ rot(-p["spread"], C.PIVOT["tail_fan"]),
        "tail_mid": fan,
        "tail_low": fan @ rot(p["spread"], C.PIVOT["tail_fan"]),
        "body": body,
        "head": head,
        "crest": head @ rot(p["crest"], C.PIVOT["crest"]),
        "beak": _rigid(head, C.RIGID["beak"]),
    }
    fx, fy = C.FAR_WING_OFFSET
    posed = {n: sample(GRIDS[n], T[n]) for n in T}
    posed["wing"] = shift(WING_GRIDS[p["s"]], 0, -p["lift"])
    posed["far_wing"] = shift(FAR_GRIDS[p["far"]], fx, fy - p["lift"])
    out = np.zeros((C.H, C.W), np.int16)
    ink = np.zeros((C.H, C.W), bool)
    for g in C.GROUPS:
        parts = [posed[n] for n in g]
        union = np.any([m for m, _ in parts], 0)
        r = _ring(union)
        out[r] = IDX[C.OUTLINE]
        ink |= r
        for m, col in parts:
            out[m] = col[m]
            ink &= ~m
    _lit_edges(out, ink)
    # the eye, whole, at the head's place
    ex, ey = C.EYE.at
    w, h = len(C.EYE.rows[0]), len(C.EYE.rows)
    cx, cy, _ = T["head"] @ np.array([ex + w / 2, ey + h / 2, 1.0])
    x0, y0 = int(np.floor(cx - w / 2 + 0.5)), int(np.floor(cy - h / 2 + 0.5))
    for j, row in enumerate(C.EYE.rows):
        for i, ch in enumerate(row):
            out[y0 + j, x0 + i] = IDX[ch]
    for (x, y), ch in C.pixels(C.SHADOW_UP if p["lift"] else C.SHADOW).items():
        if out[y, x] == 0:
            out[y, x] = IDX[ch]
    return out


def _lit_edges(out, ink):
    """Selective outline: an outer outline pixel with air above or left of it and plumage below or right of it
    takes a lighter outline in that plumage's own hue (M over blue, N over the breast and beak), so the lit top of
    the bird is not cut out with black. The shadow side keeps the plum black."""
    blue, warm = {IDX[c] for c in C.BLUES}, {IDX[c] for c in C.WARMS}
    H, W = out.shape
    lit = []

    def at(x, y):
        return out[y, x] if 0 <= x < W and 0 <= y < H else 0
    for y, x in zip(*np.nonzero(ink)):
        def fill(xx, yy):
            return 0 <= xx < W and 0 <= yy < H and at(xx, yy) and not ink[yy, xx]
        air_ul = at(x, y - 1) == 0 or at(x - 1, y) == 0
        notch = (fill(x - 1, y) and fill(x + 1, y)) or (fill(x, y - 1) and fill(x, y + 1))
        below = [at(xx, yy) for xx, yy in ((x, y + 1), (x + 1, y)) if fill(xx, yy)]
        if air_ul and not notch and not (fill(x, y - 1) and fill(x - 1, y)) and below:
            if all(v in blue for v in below):
                lit.append((y, x, C.OUTLINE_LIT))
            elif all(v in warm for v in below):
                lit.append((y, x, C.OUTLINE_WARM))
    for y, x, ch in lit:
        out[y, x] = IDX[ch]


# ---- output -------------------------------------------------------------------------------------------------
def to_image(arr, bg=None):
    im = Image.new("RGBA", (arr.shape[1], arr.shape[0]), bg or (0, 0, 0, 0))
    px = im.load()
    for y in range(arr.shape[0]):
        for x in range(arr.shape[1]):
            if arr[y, x]:
                px[x, y] = C.rgb(CHARS[arr[y, x] - 1]) + (255,)
    return im


def loop_frames(loop):
    n = LOOPS[loop]["n"]
    poses = [pose(loop, t) for t in range(n // HOLD)]
    cache = {}
    frames = []
    for k in range(n):
        p = poses[k // HOLD]
        key = tuple(sorted(p.items()))
        if key not in cache:
            cache[key] = frame(p)
        frames.append(cache[key])
    return frames, poses


def strip(frames):
    im = Image.new("RGBA", (C.W * len(frames), C.H), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        im.alpha_composite(to_image(f), (k * C.W, 0))
    return im


REST = dict(s=1.0, far=1.0, lift=0, nod=0, head=0.0, crest=0.0, tail_root=0.0, tail_fan=0.0, spread=0.0)


def art_preview(path, zoom=8):
    im = to_image(frame(REST), bg=(232, 225, 212, 255))
    im.resize((C.W * zoom, C.H * zoom), Image.NEAREST).save(path)


def main(argv):
    for loop in LOOPS:
        frames, poses = loop_frames(loop)
        path = os.path.join(HERE, f"{C.KEY}_{loop}.png")
        strip(frames).save(path)
        print("wrote", os.path.relpath(path, HERE), f"({len(frames)} frames of {C.W}x{C.H})")
        if "--poses" in argv:
            for t, p in enumerate(poses):
                print(f"  {loop} tick {t:2d} (frames {t * HOLD}-{t * HOLD + HOLD - 1}): " +
                      " ".join(f"{k}={v}" for k, v in p.items()))
    path = os.path.join(HERE, f"{C.KEY}_art_8x.png")
    art_preview(path)
    print("wrote", os.path.relpath(path, HERE))


if __name__ == "__main__":
    main(sys.argv[1:])
