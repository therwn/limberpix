"""Animate the Emberback skink (creature.py) by posing its parts, the pixel-animate way.

    python animate.py             # writes lizard_idle.png (36 frames) and lizard_move.png (40 frames), 30 fps
    python animate.py --ticks     # also prints each loop's pose per clock tick, to read before rendering

Check:  python ../../../skills/pixel-anim-check/pixel_anim_check.py --loop idle=lizard_idle.png
          --loop move=lizard_move.png --frame 72 --eye "#f6c544" --ink "#1b1826,#2c4438" --effects "#e0517a"
          --out check --name lizard
(--ink names both outline colours, the lit one being lighter than the check's default; --effects names the tongue,
1 px thick and drawn without an outline.)

Nothing is redrawn: every frame is the one drawing with its parts moved by whole pixels.
  - One clock: every part changes pose on the same 2-frame tick (k // 2 * 2), so each pose is held 2 frames.
  - The walk is a sprawling diagonal gait: the near front and the far hind foot step together, then the far front and
    the near hind. A leg is sheared from its shoulder or hip (each row shifted in proportion to its depth, the joint
    row fixed), and the swinging foot draws in a pixel (it is off the ground).
  - The spine bends side to side, which this view shows as up and down: the trunk bows one way between the girdles
    while the head and the tail root swing the other, then it flips (an S). The girdles stay put, so the legs ride
    no bend. Each column moves whole, so the body keeps its thickness: it is never squashed. An ember spot moves as
    one, so a bend never shears it.
  - The tail follows as a chain of links (its taper steps): a wave runs from its root to its tip, later and larger
    toward the tip.
  - The head is rigid; its swing (and its lift in the idle) is staged over two or three ticks, so no single step moves
    the whole head. In the move no step changes more than about a fifth of the figure.
  - In the idle the trunk stays still. It breathes a pixel at the belly, the head lifts (the snout first, then the
    eye, then the back of the head) and flicks its tongue, the eye half-blinks, and the tail tip curls.
  - Outline last: where a bend opens the edge, a pixel of ink is drawn on the air side (pixel-animate 2.5).
"""
import math
import os
import sys

import creature as C

FPS = 30
IDLE_FRAMES, MOVE_FRAMES = 36, 40
HOLD = 2                                       # one clock for every part: a new pose every 2 frames (15/s)
BELLY = range(32, 40)                          # the trunk columns whose belly swells a pixel on the breath
INK = "o"


def rnd(v):
    """Round half away from zero, the same way up and down."""
    return int(math.floor(abs(v) + 0.5)) * (1 if v >= 0 else -1)


def blank():
    return [["."] * C.W for _ in range(C.H)]


def column_part(x):
    return next((C.PARTS[y][x] for y in range(C.H) if C.PARTS[y][x] != "."), ".")


# ---- the body: each column moved whole along the spine's normal ------------------------------------------------
def body_layer(dy, breath=0):
    """dy[x]: whole pixels the body column x moves down (negative: up). breath: the belly columns grow a pixel down
    (the last scale row repeated, the outline under it)."""
    g = blank()
    for x in range(C.W):
        col = [C.BODY[y][x] for y in range(C.H)]
        if all(c == "." for c in col):
            continue
        if breath and x in BELLY:
            low = max(y for y in range(C.H) if col[y] != ".")          # the outline under the belly
            col[low + 1] = col[low]
            col[low] = col[low - 1]
        d = dy.get(x, 0)
        for y, c in enumerate(col):
            if c != "." and 0 <= y + d < C.H:
                g[y + d][x] = c
    return g


# ---- legs: sheared below the joint, the swinging foot drawn in ----------------------------------------------------
def leg_rows(leg, dx, lift=0):
    """The leg's rows placed in the frame: [(y, x0, row)]. The pivot row (the joint) stays; each row from it to the
    foot is shifted by dx times its depth (the foot's rows by dx). lift drops the shin row next to the foot, so the
    foot comes a pixel nearer the body."""
    rows, (ox, oy), pivot, foot = leg["rows"], leg["origin"], leg["pivot"], leg["foot"]
    h = len(rows)
    idx = list(range(h))
    if lift:
        idx.remove(foot if leg["far"] else h - foot - 1)
    out = []
    for k, j in enumerate(idx):
        if leg["far"]:                          # the foot at the top: rows above the dropped one come down a pixel
            y = oy + k + (h - len(idx))
            depth = (pivot - j) / (pivot - (foot - 1))
        else:                                   # the foot at the bottom: rows below it go up a pixel
            y = oy + k
            depth = (j - pivot) / ((h - foot) - pivot)
        depth = min(1.0, max(0.0, depth))
        out.append((y, ox + rnd(dx * depth), rows[j]))
    return out


def draw_leg(g, leg, dx, lift, dy):
    for y, x0, row in leg_rows(leg, dx, lift):
        for i, c in enumerate(row):
            if c != "." and 0 <= y + dy < C.H and 0 <= x0 + i < C.W:
                g[y + dy][x0 + i] = c


def outline_last(g):
    """Ink every air pixel that touches a coloured pixel (not ink, not the tongue) on a side: a bend can open the
    edge by a pixel; the outline is drawn last, as the method says."""
    add = []
    for y in range(C.H):
        for x in range(C.W):
            if g[y][x] != ".":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v = g[y + dy][x + dx] if 0 <= y + dy < C.H and 0 <= x + dx < C.W else "."
                if v not in (".", C.TONGUE) and v not in C.INK:
                    add.append((x, y))
                    break
    for x, y in add:
        g[y][x] = INK
    return g


SPOTS = [x for x in range(C.W) if any(C.BODY[y][x] in "rR" for y in range(C.H))]


def whole_spots(dy):
    """A spot two columns wide moves as one: its right column takes its left column's place, so a bend never
    shears an ember spot in two."""
    dy = dict(dy)
    for x in SPOTS:
        if x - 1 in SPOTS:
            dy[x] = dy.get(x - 1, 0)
    assert all(abs(dy.get(x + 1, 0) - dy.get(x, 0)) <= 1 for x in range(C.W - 1) if column_part(x) != "."), dy
    return dy


def frame(p):
    """One frame from a pose dict."""
    g = blank()
    dy = whole_spots(p["dy"])
    for name in ("far_hind", "far_front"):
        leg = C.LEGS[name]
        dx, lift = p["legs"][name]
        draw_leg(g, leg, dx, lift, dy.get(C.HIP_X if "hind" in name else C.SHOULDER_X, 0))
    body = body_layer(dy, p["breath"])
    for y in range(C.H):
        for x in range(C.W):
            if body[y][x] != ".":
                g[y][x] = body[y][x]
    for name in ("near_hind", "near_front"):
        leg = C.LEGS[name]
        dx, lift = p["legs"][name]
        draw_leg(g, leg, dx, lift, dy.get(C.HIP_X if "hind" in name else C.SHOULDER_X, 0))
    ex, ey = C.LID["origin"]
    if p["lid"]:
        C.paste(g, (ex, ey + dy.get(ex, 0)), C.LID["rows"])
    if p["tongue"]:
        t = C.TONGUE_OUT[p["tongue"] - 1]
        tx, ty = t["origin"]
        C.paste(g, (tx, ty + dy.get(tx - 1, 0)), t["rows"])
    return ["".join(r) for r in outline_last(g)]


# ---- the loops -------------------------------------------------------------------------------------------------
def head_dy(dy, back, mid, front):
    """The head lifted in three stages, each a whole pixel: the face columns (snout and the front of the jaw) by
    `front`, the eye's columns by `mid`, the back of the head and the last two neck columns by `back` (a shear
    between the trunk and the head). Staged so no single step moves the whole head."""
    for x in range(C.HEAD_X - 2, C.W):
        if column_part(x) in "NH":
            dy[x] = front if x >= C.FACE_X else mid if x >= C.EYE_X else back
    return dy


# The tail's taper steps: runs of columns whose top row is the same. A thin tail bent column by column dents
# wherever a bend step meets a taper step, so each run moves as one link of the chain.
LINKS = []
for _x in range(C.HIP_X):
    if column_part(_x) in "TB":
        _top = min(y for y in range(C.H) if C.BODY[y][_x] != ".")
        if LINKS and LINKS[-1][1] == _top and column_part(_x) == column_part(LINKS[-1][0][0]):
            LINKS[-1][0].append(_x)
        else:
            LINKS.append(([_x], _top))
LINKS = [xs for xs, _ in LINKS]
while all(C.BODY[y][x] in C.INK + "." for x in LINKS[0] for y in range(C.H)):   # the tip's own outline goes with the tip
    LINKS[1:2] = [LINKS[0] + LINKS[1]]
    LINKS.pop(0)


def tail_chain(dy, theta, amp, lag, base=0.0, start=C.HIP_X):
    """The tail as a chain from the hip to the tip: each link (a taper step, see LINKS) lags its root by lag * u and
    swings amp * u (u: 0 at `start`, 1 at the tip, read at the link's middle), so the wave reaches the tip later and
    larger. Links next to each other never differ by more than a pixel."""
    prev = None
    for xs in reversed(LINKS):
        xm = sum(xs) / len(xs)
        if xm >= start:
            continue
        u = (start - xm) / start
        v = rnd((base + amp * u ** 1.2) * math.sin(theta - lag * u))
        if prev is not None:
            v = max(prev - 1, min(prev + 1, v))
        for x in xs:
            dy[x] = v
        prev = v
    return dy


def idle_pose(k):
    t = k // HOLD                                  # the tick (18 a loop)
    theta = 2 * math.pi * (t * HOLD) / IDLE_FRAMES
    dy = {}
    tail_chain(dy, theta, 2.4, 2.2, start=22)      # the tail beyond its root sways, the tip curling most
    front = -1 if 3 <= t <= 12 else 0              # the snout rises first and comes down last: a tilt up and back
    mid = -1 if 4 <= t <= 11 else 0
    back = -1 if 5 <= t <= 10 else 0
    head_dy(dy, back, mid, front)
    return {
        "dy": dy, "breath": 1 if t >= 13 or t == 0 else 0,
        "legs": {n: (0, 0) for n in C.LEGS},
        "tongue": {7: 1, 8: 2, 9: 1}.get(t, 0),     # out, forked, out: while the head is up and still
        "lid": t in (15, 16),                      # a slow half-blink with the head down
    }


def foot(p):
    """A foot's place (dx) and lift over a stride, p in [0, 1): stance (planted, sliding back under the body) for
    5/8 of it, then the swing forward, drawn in."""
    p %= 1.0
    if p < 0.625:
        return 2.0 - 4.0 * p / 0.625, 0
    s = (p - 0.625) / 0.375
    return -2.0 + 4.0 * s, 1 if 0.1 < s < 0.95 else 0


def move_pose(k, head_ph=0.3, trunk_ph=0.5, tail_ph=2.7, tail_amp=1.8):
    t = k // HOLD                                  # the tick (20 a stride)
    n = MOVE_FRAMES // HOLD
    phi = 2 * math.pi * t / n
    dy = {}
    for x in range(C.HIP_X, C.SHOULDER_X + 1):    # the trunk bows between the girdles
        bump = max(0.0, 1 - abs(x - 36) / 7.5)
        dy[x] = rnd(1.4 * bump * math.cos(phi - trunk_ph))
    # the head swings the other way, in two stages: the neck and the back of the head, then the face
    # a tick later (one rigid head; the stages only spread its move over two ticks)
    back = -1.2 * math.cos(phi + head_ph)
    face = -1.2 * math.cos(phi + head_ph - 2 * math.pi / n)
    for x in range(C.SHOULDER_X + 1, C.W):
        w = min(1.0, (x - C.SHOULDER_X) / (C.HEAD_X - C.SHOULDER_X))
        dy[x] = rnd(face) if x >= C.FACE_X else rnd(back * w)
    tail_chain(dy, phi - tail_ph - math.pi / 2, tail_amp, 2.6, base=0.3)   # the root opposite the trunk, behind it
    legs = {}
    for name in C.LEGS:
        pair_a = name in ("near_front", "far_hind")
        dx, lift = foot(t / n + (0.0 if pair_a else 0.5))
        legs[name] = (dx, lift)
    return {"dy": dy, "breath": 0, "legs": legs, "tongue": 0, "lid": False}


def loop(pose, n):
    return [frame(pose(k)) for k in range(n)]


def key(p):
    """A pose as a hashable tuple, to find two ticks running that are the same (a lost update)."""
    return (tuple(sorted(p["dy"].items())), p["breath"],
            tuple(sorted((n, rnd(dx * 4), l) for n, (dx, l) in p["legs"].items())), p["tongue"], p["lid"])


def ticks(name, pose, n):
    ps = [pose(k) for k in range(0, n, HOLD)]
    print(f"{name}: {len(ps)} ticks of {HOLD} frames")
    for i, p in enumerate(ps):
        tail = "".join("%+d" % p["dy"].get(x, 0) for x in range(1, 29, 3))
        legs = " ".join(f"{n[:1]}{n.split('_')[1][0]}{dx:+.1f}{'^' if l else ' '}" for n, (dx, l) in p["legs"].items())
        print(f"  t{i:02d} tail {tail} trunk {p['dy'].get(36, 0):+d} head {p['dy'].get(52, 0):+d}"
              f"/{p['dy'].get(60, 0):+d} legs {legs} breath {p['breath']} tongue {p['tongue']} lid {int(p['lid'])}")
    same = [i for i in range(len(ps)) if key(ps[i]) == key(ps[(i + 1) % len(ps)])]
    print(f"  identical neighbours: {same or 'none'}")


def strip(frames, box):
    from PIL import Image
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    im = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        for y in range(y0, y1):
            for x in range(x0, x1):
                c = f[y][x]
                if c != ".":
                    v = C.PALETTE[c]
                    im.putpixel((k * w + x - x0, y - y0), (int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16), 255))
    return im


def union_box(loops, margin=1):
    xs, ys = [], []
    for frames in loops:
        for f in frames:
            for y, r in enumerate(f):
                for x, c in enumerate(r):
                    if c != ".":
                        xs.append(x)
                        ys.append(y)
    return (max(0, min(xs) - margin), max(0, min(ys) - margin), min(C.W, max(xs) + 1 + margin),
            min(C.H, max(ys) + 1 + margin))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--ticks" in sys.argv:
        ticks("idle", idle_pose, IDLE_FRAMES)
        ticks("move", move_pose, MOVE_FRAMES)
    idle, move = loop(idle_pose, IDLE_FRAMES), loop(move_pose, MOVE_FRAMES)
    box = union_box([idle, move, [C.rest()]])     # one fixed grid for every frame of every loop
    for name, frames in (("idle", idle), ("move", move)):
        strip(frames, box).save(os.path.join(here, f"{C.KEY}_{name}.png"))
    print(f"frame {box[2] - box[0]}x{box[3] - box[1]}: wrote {C.KEY}_idle.png ({len(idle)} frames), "
          f"{C.KEY}_move.png ({len(move)} frames) at {FPS} fps")


if __name__ == "__main__":
    main()
