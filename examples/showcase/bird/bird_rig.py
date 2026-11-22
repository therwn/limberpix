"""The bird's rig: places the drawing's parts (creature.py) for one pose and draws the frame. animate.py says which
pose each tick takes; this file only knows how to put a pose on the frame.

A pose is a dict (every offset in whole game px, y down):
    s, far      the near and the far wing's key (creature.WINGS: up, half_up, level, half_down, down, fold, and the
                attack's cock and sweep)
    x, y        the whole bird's offset from the drawing's place
    rot, pivot  the body, tail, wings and feet turned about pivot (a frame point), degrees, nose down positive (only
                in the attack's dive and recoil; 0 everywhere else)
    hkey        the head's drawn key (bird_heads.HEADS: the nods -3, 3 and 6 degrees, the dive's 10 to 45, nose down
                positive), or 0 for the drawing's own head;
                either way the head is never turned at run time: it is moved whole to where the body's turn takes
                the neck (NECK), so the face stays one drawing however the body turns
    head        (dx, dy) of the head, bill and crest against the body; the neck bends to carry it (neck_pixels)
    nape        (dx, dy) of the crest against the head (it follows the head a pose late)
    jaw         the lower mandible opened about its hinge (a drawn key, JAW): 0 shut, 1 or 2 px at the tip
    tail        (root, middle, tip): each link's dy against the body; a link takes its parent's place and adds its own
    feet        (dx, dy) of the feet against the body; drawn up into it (dy < 0) they tuck behind the belly (tuck), a
                few pixels a pose (TUCK in animate.py); None leaves them out
    fx          the effects drawn round the bird: a list of (name, step) (see effects())
    hit_pose    the contact pose, whose bill tip the hit's sparks keep flying from (else the pose itself)

Nothing is redrawn. A part moved by whole pixels is the drawing's own pixels; the wing keys, the open bill and the
head's turns (the nods and the dive's keys) are drawn keys. Only the body, neck, tail, wings and feet are ever turned (the dive and its recoil): scaled
up 8x with Scale2x (three passes, so the diagonals stay smooth), turned there and sampled back once at each game
pixel's centre, the RotSprite way. The outline is drawn last by creature.compose, round whatever the parts cover.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bird_heads as HK  # noqa: E402
import creature as C  # noqa: E402

PAD = (4, 6, 14, 12)                     # room round the drawing's own 80x64 frame (left, top, right, bottom) for
CANVAS = (C.W + PAD[0] + PAD[2], C.H + PAD[1] + PAD[3])   # the dive's reach; animate.py crops every loop to one box
PIVOT = (46.0, 34.0)                     # the default turn centre: the shoulder's front, mid-body
BILL_TIP = (70, 27)                      # where the dive's hit lands
NECK = (47.0, 31.0)                      # where the head sits on the body: a turned body carries the head there
NECK_STEP = 35                           # the neck's rows down to this one ride with the head, the rows below with the
                                         # body: the neck carries the head on the body as a bend (neck_pixels)
HEAD_GROUP = ("nape", "head", "bill_low", "bill_up")    # the head and what rides on it
TAIL_CUTS = (17, 23)                     # tail links: tip x < 17, middle 17-22, root x >= 23
CHARS = list(C.PALETTE)
IDX = {ch: i + 1 for i, ch in enumerate(CHARS)}

FAR_SET = {"half_down": (3, -1), "down": (5, -2),   # the far wing on the downstroke, set forward of creature's
            "sweep": (1, -2)}            # FAR_OFFSET so its tip shows under the breast (it never vanishes); swept
                                         # back, it shows above the near wing, over the back
REST = dict(s="up", far="up", x=0, y=0, rot=0, pivot=PIVOT, hkey=0, head=(0, 0), nape=(0, 0), jaw=0,
            tail=(0, 0, 0), feet=(0, 0), fx=())

# effects: their own colours, none in the drawing's palette (pixel-anim-check --effects)
FX_STREAK = "#e2f8ff"                    # the dive's speed lines, lit
FX_TRAIL = "#7fb6c8"                     # the lines fading, a frame later
FX_SPARK = "#fff0a8"                     # the hit's flash and the sparks thrown from it
FX_COLOURS = (FX_STREAK, FX_TRAIL, FX_SPARK)


# ---- placing parts --------------------------------------------------------------------------------------------
def moved(px, dx, dy):
    return {(x + dx, y + dy): ch for (x, y), ch in px.items()}


def tail_pixels(links):
    """The tail as a chain of three links cut across its length. Each link adds its own dy to its parent's and is
    drawn at its parent's place too, underneath, so a joint never opens a gap. links: (root, middle, tip) dy."""
    px = C.layer_pixels("tail")
    cum = [links[0], links[0] + links[1], links[0] + links[1] + links[2]]

    def link(x):
        return 0 if x >= TAIL_CUTS[1] else 1 if x >= TAIL_CUTS[0] else 2
    out = {}
    for i in (2, 1, 0):
        for at in sorted({max(0, i - 1), i}):
            for (x, y), ch in px.items():
                if link(x) == i:
                    out[(x, y + cum[at])] = ch
    return out


# The lower mandible opened about its hinge, drawn as keys (one character per pixel, from creature.JAW_HINGE): it
# stays a solid wedge, its base on the hinge, its tip dropped 1 or 2 px, and the mouth inside (plum) shows between
# the mandibles. Key 0 is the drawing's own mandible.
JAW = {
    0: ["tuuuutlllkkkk",
        "stttskkkk",
        "rssk"],
    1: ["tuuuutrrrrr",
        "stttsklllkkkk",
        "rsskkkkkkkkk"],
    2: ["tuuuurrrrrr",
        "stttstllllkk",
        "rsskkkkkkkkkk"],
}


def jaw_pixels(open_px):
    hx, hy = C.JAW_HINGE
    return {(hx + i, hy + r): ch for r, row in enumerate(JAW[open_px]) for i, ch in enumerate(row) if ch != "."}


def neck_pixels(dx, dy):
    """The neck, carrying the head on the body: its rows down to NECK_STEP (under the head, and the throat's top just
    below it) ride with the head's (dx, dy), the rows below stay with the body. Every row is also drawn at the body's
    place, underneath, so the neck never opens a gap between head and breast, and its one-pixel bend falls on a row
    where the neck's front and back already slope (the breast curving in under the throat, the nape out to the
    back): no step shows in its outline."""
    px = C.layer_pixels("neck")
    out = dict(px)
    out.update({(x + dx, y + dy): ch for (x, y), ch in px.items() if y <= NECK_STEP})
    return out


def nape_pixels(dx, dy):
    """The crest. Where a column of it ends on the cap, its lowest pixel is carried 2 px down, under the head, so a
    raised crest never comes off the cap (a strip of overlap)."""
    px = C.layer_pixels("nape")
    head = C.layer_pixels("head")
    out = {}
    for x in {x for x, _ in px}:
        yb = max(y for xx, y in px if xx == x)
        if (x, yb + 1) in head or (x, yb + 2) in head:
            for k in (1, 2):
                out[(x + dx, yb + dy + k)] = px[(x, yb)]
    out.update(moved(px, dx, dy))
    return out


def tuck(foot, body, at):
    """A foot drawn up into the body (dy < 0) goes behind the belly: its pixels inside the body layer are left out,
    so the feet tuck up row by row and come out the same way, never vanishing in one frame. At rest (dy >= 0) the
    foot is drawn whole over the body, as the drawing has it."""
    return foot if at[1] >= 0 else {q: ch for q, ch in foot.items() if q not in body}


def place(p):
    """The pose's parts at their places, before the whole-bird turn: [(group, pixels)]."""
    hx, hy = p["head"]
    nx, ny = p["nape"]
    fdx, fdy = FAR_SET.get(p["far"], (0, 0))
    body = C.layer_pixels("body")
    feet = [] if p["feet"] is None else [(name, tuck(C.layer_pixels(name, *p["feet"]), body, p["feet"]))
                                         for name in ("foot_far", "foot_near")]
    return [("wing_far", C.wing_pixels(p["far"], far=True, dx=fdx, dy=fdy)),
            ("tail", tail_pixels(p["tail"])),
            ("body", body), ("neck", neck_pixels(hx, hy))] + feet + [
            ("wing", C.wing_pixels(p["s"])),
            ("nape", nape_pixels(hx + nx, hy + ny)),
            ("head", C.layer_pixels("head", hx, hy)),
            ("bill_low", moved(jaw_pixels(p["jaw"]), hx, hy)),
            ("bill_up", C.layer_pixels("bill_up", hx, hy))]


# ---- turning parts (RotSprite: Scale2x three times, turn, sample once) ----------------------------------------
def scale2x(a):
    p = np.pad(a, 1, mode="edge")
    A, B, Cc, D, P = p[:-2, 1:-1], p[1:-1, 2:], p[1:-1, :-2], p[2:, 1:-1], a   # up, right, left, down, centre
    out = np.zeros((a.shape[0] * 2, a.shape[1] * 2), a.dtype)
    out[0::2, 0::2] = np.where((Cc == A) & (Cc != D) & (A != B), A, P)
    out[0::2, 1::2] = np.where((A == B) & (A != Cc) & (B != D), B, P)
    out[1::2, 0::2] = np.where((D == Cc) & (D != B) & (Cc != A), Cc, P)
    out[1::2, 1::2] = np.where((B == D) & (B != A) & (D != Cc), D, P)
    return out


def turn(px, deg, pivot):
    """A part's pixels turned deg about pivot (frame coordinates), RotSprite style."""
    if not px or not deg:
        return dict(px)
    xs, ys = [x for x, _ in px], [y for _, y in px]
    x0, y0 = min(xs) - 1, min(ys) - 1
    g = np.zeros((max(ys) - y0 + 2, max(xs) - x0 + 2), np.int16)
    for (x, y), ch in px.items():
        g[y - y0, x - x0] = IDX[ch]
    big = scale2x(scale2x(scale2x(g)))
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    cx, cy = pivot
    corners = [(x0 - 1, y0 - 1), (x0 + g.shape[1] + 1, y0 - 1), (x0 - 1, y0 + g.shape[0] + 1),
               (x0 + g.shape[1] + 1, y0 + g.shape[0] + 1)]
    rx = [cx + (x - cx) * c - (y - cy) * s for x, y in corners]
    ry = [cy + (x - cx) * s + (y - cy) * c for x, y in corners]
    X, Y = np.meshgrid(np.arange(math.floor(min(rx)), math.ceil(max(rx)) + 1),
                       np.arange(math.floor(min(ry)), math.ceil(max(ry)) + 1))
    u, v = X + 0.5 - cx, Y + 0.5 - cy                      # each game pixel's centre, turned back
    sx, sy = cx + u * c + v * s, cy - u * s + v * c
    bi, bj = np.floor((sy - y0) * 8).astype(int), np.floor((sx - x0) * 8).astype(int)
    ok = (bi >= 0) & (bi < big.shape[0]) & (bj >= 0) & (bj < big.shape[1])
    val = np.zeros(X.shape, np.int16)
    val[ok] = big[bi[ok], bj[ok]]
    return {(int(x), int(y)): CHARS[k - 1] for x, y, k in zip(X[val > 0], Y[val > 0], val[val > 0])}


def turn_point(pt, deg, pivot=PIVOT):
    t = math.radians(deg)
    (x, y), (cx, cy) = pt, pivot
    return cx + (x - cx) * math.cos(t) - (y - cy) * math.sin(t), cy + (x - cx) * math.sin(t) + (y - cy) * math.cos(t)


# ---- one frame --------------------------------------------------------------------------------------------------
def head_key(p):
    """The head's drawn key for p["hkey"] (bird_heads.HEADS) as {group: pixels}, at the pose's head and crest
    offsets, drawn for a head turned about KEY_PIVOT."""
    (x0, y0), rows = HK.HEADS[p["hkey"]]
    hx, hy = p["head"]
    nx, ny = p["nape"]
    out = {g: {} for g in HEAD_GROUP}
    key = {}
    for r, (row, own) in enumerate(rows):
        for i, (ch, o) in enumerate(zip(row, own)):
            if ch != ".":
                key[(x0 + i, y0 + r)] = (ch, HEAD_OWNER[o])
    # the crest runs on under the cap, 2 px down each column and 2 px on along each row where the cap meets it
    # (hidden there, as nape_pixels does for the drawing's own head), so a crest set off a pixel never comes off it
    crest = {k: ch for k, (ch, g) in key.items() if g == "nape"}
    under = {}
    for (x, y), ch in crest.items():
        for dx, dy in ((0, 1), (1, 0)):
            if (x + dx, y + dy) not in crest:
                for k in (1, 2):
                    q = (x + dx * k, y + dy * k)
                    if key.get(q, (None, None))[1] == "head":
                        under.setdefault(q, ch)
    for (x, y), (ch, g) in list(key.items()) + [(q, (ch, "nape")) for q, ch in under.items()]:
        dx, dy = (hx + nx, hy + ny) if g == "nape" else (hx, hy)
        out[g].setdefault((x + dx, y + dy), ch)
    return out


HEAD_OWNER = {"N": "nape", "H": "head", "L": "bill_low", "U": "bill_up"}


def posed(p):
    """The parts of pose p at their final place on the canvas: [(group, pixels)]. A turned body carries the head
    whole (the drawing's own head, or the key p["hkey"]) to where its turn takes the neck, by whole pixels."""
    ox, oy = PAD[0] + p["x"], PAD[1] + p["y"]
    rot, hk = p["rot"], p["hkey"]
    nx, ny = turn_point(NECK, rot, p["pivot"])
    kx, ky = turn_point(NECK, hk, HK.PIVOTS.get(hk, HK.KEY_PIVOT))
    hshift = (int(round(nx - kx)), int(round(ny - ky)))
    key = head_key(p) if hk else None
    out = []
    for group, px in place(p):
        if group in HEAD_GROUP:
            px = moved(key[group] if key else px, *hshift)
        elif rot:
            px = turn(px, rot, p["pivot"])
        out.append((group, moved(px, ox, oy)))
    return out


def render(p):
    """One frame: (rows of palette characters, the owner map {(x, y): group}, the effect pixels {(x, y): hex})."""
    parts = posed(p)
    C.W, C.H = CANVAS                    # compose draws on the creature module's frame size: the padded canvas
    owner = {}
    rank = {g: i for i, g in enumerate(C.ORDER)}
    for group, px in sorted(parts, key=lambda q: rank[q[0]]):
        for k in px:
            owner[k] = group
    rows = halo(C.compose(parts), owner)
    fx = effects(p, rows)
    return rows, owner, fx


def halo(rows, owner):
    """The crest's glowing tips keep their colour to the edge (creature.GLOW). Round them goes the line the rest of
    the bird has on its edge, drawn just outside the tip: the lit outline (O) above and left of it, ink below and
    right; in the air, and over a part behind the crest that it does not merge with (a raised wing), as compose()
    lines any part lying over another. Those pixels become the crest's (owner is updated)."""
    g = [list(r) for r in rows]
    merge = {o for o in C.ORDER if frozenset(("nape", o)) in C.MERGE} | {"nape"}
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in C.GLOW:
                for dx, dy, line in ((0, -1, "O"), (-1, 0, "O"), (1, 0, "o"), (0, 1, "o")):
                    q = (x + dx, y + dy)
                    if rows[q[1]][q[0]] in C.GLOW or owner.get(q) in merge:
                        continue
                    if g[q[1]][q[0]] not in "O":
                        g[q[1]][q[0]] = line
                    owner[q] = "nape"
    return ["".join(r) for r in g]


STREAKS = ((-7, 9), (-2, 13), (3, 11), (8, 7))   # (offset across the path from the figure's middle, length)
HIT_FLASH = ((0, 0), (1, 0), (0, 1), (1, 1), (2, -1), (-1, 2), (2, 2), (3, 1), (1, 3), (-1, -1), (3, -1), (-2, 1))
# the sparks thrown from the flash point: (angle off the strike line, distance) of one pixel each, scattered (no two
# in a row, so they read as flying grains, not a glyph); step 2 is the same grains further out, darker
HIT_SPARKS = ((-100, 3), (-62, 4), (-30, 3), (8, 4), (38, 3), (70, 4), (112, 3), (150, 4))
HIT_FAR = 2.1                            # step 2 throws each grain this many times as far


def bill_tip(q):
    """Where pose q's bill tip lands on the canvas: the head key's own turn, carried with the head."""
    hx, hy = q["head"]
    piv = HK.PIVOTS.get(q["hkey"], HK.KEY_PIVOT)
    tx, ty = turn_point((BILL_TIP[0] + hx, BILL_TIP[1] + hy), q["hkey"], piv)
    nx, ny = turn_point(NECK, q["rot"], q["pivot"])
    kx, ky = turn_point(NECK, q["hkey"], piv)
    return (int(round(tx + round(nx - kx) + PAD[0] + q["x"])) + 1,
            int(round(ty + round(ny - ky) + PAD[1] + q["y"])) + 1)


def effects(p, rows):
    """The attack's effects, drawn only where the bird is not (pixel-animate 3.12 and 3.13):
        streak k   speed lines behind the diving bird, along its body's line (the bill's thrust): from a gap behind
                   its trailing edge, at four places across that line (k 0: lit; k 1, the next pose: shorter,
                   further back and darker, fading)
        hit k      at the bill's tip: k 0 a flash (a small ragged burst); k 1 single grains thrown out of the flash
                   point round the strike line; k 2 the same grains further out and darker, fading"""
    out = {}
    W, H = CANVAS

    def put(x, y, col):
        if 0 <= x < W and 0 <= y < H and rows[y][x] == ".":
            out[(x, y)] = col
    for name, k in p["fx"]:
        if name == "streak":
            ux, uy = math.cos(math.radians(p["rot"])), math.sin(math.radians(p["rot"]))   # along the body's line
            fig = [(x, y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != "."]
            mid = sum(x * -uy + y * ux for x, y in fig) / len(fig)
            for off, length in STREAKS:
                row = [(x * ux + y * uy, x, y) for x, y in fig if abs(x * -uy + y * ux - mid - off) < 0.71]
                if not row:
                    continue
                _, sx, sy = min(row)                              # the trailing pixel on that line
                start, length = (3, length) if k == 0 else (8, length // 2)
                for d in range(start, start + length):
                    put(int(round(sx - ux * d)), int(round(sy - uy * d)), FX_STREAK if k == 0 else FX_TRAIL)
        elif name == "hit":
            q = p.get("hit_pose") or p              # the sparks fly from where the flash was, not from the bill now
            tx, ty = bill_tip(q)
            if k == 0:
                for ddx, ddy in HIT_FLASH:
                    put(tx + ddx, ty + ddy, FX_SPARK)
                continue
            for ang, d in HIT_SPARKS:              # thrown out of the flash point, round the strike line
                a = math.radians(q["rot"] + ang)
                d = d * (HIT_FAR if k == 2 else 1)
                put(int(round(tx + 0.5 + d * math.cos(a))), int(round(ty + 0.5 + d * math.sin(a))),
                    FX_SPARK if k == 1 else FX_TRAIL)
    return out
