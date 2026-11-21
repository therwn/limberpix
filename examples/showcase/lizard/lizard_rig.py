"""The lizard's rig: the drawing's layers (creature.py) placed by a pose, by whole pixels only, and drawn back to
front with the outline last. animate.py writes the poses; this file turns one pose into one frame; lizard_legs.py
poses the legs.

A pose is a dict (every value whole pixels unless it says otherwise; y grows downward):
  body      (dx, dy)  the trunk, and the hips and shoulders on it
  breath    -1, 0, 1  the back over the belly: 1 lifts the whole back a pixel over the torso's full length (its
            row BREATH_ROW drawn twice), -1 lowers it a pixel (that row covered), so the torso stays one piece: no
            band of it moves apart from another, and the belly line stays
  neck      (dx, dy)  the neck (relative to the page): it lies over the torso's front and under the head, and
            carries the head; set it between the body and the head, a pose ahead of the head
  head      (dx, dy)  the head with the casque, the turret, the jaw, the mouth and the tongue (relative to the page)
  lift      (low, eye, cap)  optional: each of the head's three row bands moved that many px more (down): low
            (the face from the mouth corner down, with the jaw, the throat, the mouth and the tongue), eye (the
            turret, the pupil and the face round them) and cap (the casque). A rise or a fall carried up the head a
            band a pose (low, then eye, then cap) spreads a 1-px move over three poses, like a small turn; where
            two bands part, the upper band's last row is drawn again, so no gap opens
  turret    (dx, dy)  the eye's cone on the head, and the pupil in it
  roll      (dx, dy)  the turret rolled: its shading (the rings round the opening and the lit cap) shifted inside
            its own outline, so the cone turns while its silhouette stays
  pupil     (dx, dy)  the pupil inside the turret's opening
  throat    0, 1, 2   the gular pouch under the jaw sagging that many pixels (its ends one at most)
  jaw       px        how far the jaw's front drops, turning about its hinge (0 closed)
  tongue    None or (reach, stretch): the club's last column, and how many columns the club is drawn longer by
  spark     None, 1 or 2: a hit at the club: 1 the flash, 2 the scattered pixels after it
  tail      [(dx, dy), ...]  each tail link's own move (root first; the links are cut across the spine)
  legs      {leg: (foot_dx, lift, knee_push)}  the foot against its drawn place, its lift, the knee pushed forward
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature as C  # noqa: E402
import lizard_legs as L  # noqa: E402

LEGS = L.LEGS
BREATH_ROW = 18                     # body rows to this one rise (or sink) with the breath; this row stretches
CLUB = 8                            # the tongue's club: its last 8 columns
LIT = "O"                           # an outline opened on a lit side (air above or to the left) takes the lit ink
DARK = "o"
EYE_ROW, LOW_ROW = 13, 22          # the head's bands: the casque above row 13, the eye's band to row 21, the low
                                    # band from row 22 (the jaw and everything hung under the head goes with it)
THROAT = (range(50, 59), 29)        # the gular pouch: these columns of the jaw, from this row down, sag
SPARK_RGB = {"w": "#fff4e8", "s": "#ffc0b0"}       # the hit's flash and its scattered pixels (effect colours)
RGB = dict(C.PALETTE, **SPARK_RGB)

# the part map: one flat colour per rig part (the part strip pixel-anim-check reads); "tongue" (the mouth and the
# tongue) and "spark" are effects and stay out of it
PART_RGB = {"body": "#d0d0d0", "head": "#e05050", "jaw": "#e0a040", "tail_root": "#50a0e0",
            "tail_mid": "#3060c0", "tail_tip": "#2030a0", "near_hind": "#50d060", "far_hind": "#208040",
            "near_front": "#e0e050", "far_front": "#909020", "throat": "#c07030"}
EFFECT_PARTS = ("tongue", "spark")

BASE = {layer: C.layer_pixels(layer) for layer in C.ORDER}


def rnd(v):
    """Round half away from zero, the same way up and down."""
    return int(math.floor(abs(v) + 0.5)) * (1 if v >= 0 else -1)


# ---- the tail: a chain of links cut across its spine ----------------------------------------------------------------
# the drawing's spine, with one point added where the curl's last turn arcs over (the tip comes down from above)
SPINE_W = C.RIG["tail_spine"][:9] + [(11.6, 26.9, 1.3)] + C.RIG["tail_spine"][9:]
SPINE = [(x, y) for x, y, _ in SPINE_W]
TAIL_PARTS = ("tail_root",) * 4 + ("tail_mid",) * 3 + ("tail_tip",) * 3      # the tip: the inner whorl, links 7-9


def _link_of(x, y):
    """The spine segment nearest to a tail pixel (its link): the one whose tube (the tail's half-width) it lies
    deepest in."""
    best, at = None, 0
    for i in range(len(SPINE) - 1):
        (ax, ay), (bx, by) = SPINE[i], SPINE[i + 1]
        vx, vy = bx - ax, by - ay
        s = max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy)))
        hw = SPINE_W[i][2] * (1 - s) + SPINE_W[i + 1][2] * s
        d = math.hypot(x - ax - s * vx, y - ay - s * vy) - hw
        if best is None or d < best:
            best, at = d, i
    return at


TAIL_LINK = {p: _link_of(*p) for p in BASE["tail"]}


def tail_offsets(moves, base=(0, 0)):
    """Each link's whole-pixel move: its own (dx, dy) plus the body's, which the whole tail rides."""
    return [(dx + base[0], dy + base[1]) for dx, dy in moves]


def _seam(link):
    """A link's pixels that touch its parent link in the drawing: drawn again at the parent's place, under both,
    they close a joint the two moved apart by a pixel without adding to the tail's bulk."""
    if not link:
        return set()
    near = {(x + i, y + j) for (x, y), k in TAIL_LINK.items() if k == link - 1 for i in (-1, 0, 1) for j in (-1, 0, 1)}
    return {p for p, k in TAIL_LINK.items() if k == link and p in near}


SEAMS = [_seam(i) for i in range(len(SPINE) - 1)]


def place_tail(moves, base):
    """The tail's pixels, each link at its own move, with its seam also at its parent's (under it) and at every
    whole pixel between, so no joint opens a gap; returned as [(pixels, part)], back to front: the tip first, the
    root last (under the rump)."""
    offs = tail_offsets(moves, base)
    out = []
    for link in range(len(offs) - 1, -1, -1):
        if link:
            (px_, py_), (lx, ly) = offs[link - 1], offs[link]
            n = max(abs(lx - px_), abs(ly - py_))
            for k in range(n):                          # a joint pulled 2 px apart is bridged at each step
                dx, dy = px_ + rnd((lx - px_) * k / n), py_ + rnd((ly - py_) * k / n)
                out.append(({(x + dx, y + dy): BASE["tail"][(x, y)] for x, y in SEAMS[link]}, TAIL_PARTS[link]))
        dx, dy = offs[link]
        px = {(x + dx, y + dy): ch for (x, y), ch in BASE["tail"].items() if TAIL_LINK[(x, y)] == link}
        out.append((px, TAIL_PARTS[link]))
    return out


# ---- the body and the head ----------------------------------------------------------------------------------------
def place_body(body, breath):
    """The torso, one piece: breathing in, the back above BREATH_ROW rises a pixel in every column at once (that
    row drawn twice); settling (breath -1), it lowers a pixel the same way (that row covered by the one under it).
    So the topline moves along its whole length together, and the belly line stays."""
    out = {}
    back = [(p, ch) for p, ch in BASE["body"].items() if p[1] <= BREATH_ROW]
    under = [(p, ch) for p, ch in BASE["body"].items() if p[1] > BREATH_ROW]
    for (x, y), ch in back:
        out[(x + body[0], y + body[1] - breath)] = ch
        if breath > 0 and y == BREATH_ROW:
            out[(x + body[0], y + body[1])] = ch
    for (x, y), ch in under:
        out[(x + body[0], y + body[1])] = ch
    return out


def _filled_ink(px):
    """The pixels with every ink pixel given the fill colour next to it (the most common of its neighbours, the
    four first): a part turned this way keeps its footprint, and the outline drawn last inks its new edge in one
    clean line instead of carrying the old line turned."""
    out = dict(px)
    for (x, y), ch in px.items():
        if ch not in C.INK:
            continue
        for ring in (((0, -1), (-1, 0), (1, 0), (0, 1)), ((-1, -1), (1, -1), (-1, 1), (1, 1))):
            fill = [px[(x + i, y + j)] for i, j in ring if px.get((x + i, y + j), "o") not in C.INK]
            if fill:
                out[(x, y)] = max(sorted(set(fill)), key=fill.count)
                break
    return out


HINGE = C.RIG["jaw_hinge"]
JAW_FRONT = max(BASE["jaw"].items(), key=lambda it: (it[0][0], -it[0][1]))[0]     # the lower lip's tip
HEAD_LOW = {}                                   # the head's lowest pixel in each column (the upper lip's line)
for (_x, _y) in BASE["head"]:
    HEAD_LOW[_x] = max(_y, HEAD_LOW.get(_x, _y))
LIP = max(x for x in HEAD_LOW if x <= JAW_FRONT[0] and HEAD_LOW[x] >= JAW_FRONT[1] - 1)  # the upper lip's tip


def _line(pts):
    """The straight line (a, b) of y = a + b x nearest to the points (least squares)."""
    n = len(pts)
    mx, my = sum(x for x, _ in pts) / n, sum(y for _, y in pts) / n
    b = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
    return my - b * mx, b


# the upper lip's line as one straight edge: the mandible above it (tucked under the head at rest) is the inside of
# the mouth, below it the outer band the drawing shows
LIP_LINE = _line([(x, HEAD_LOW[x]) for x in range(HINGE[0], LIP + 1)])
# the mandible (the hinge's column and everything in front of it) turns as one piece; the throat behind the hinge
# stays, as skin, not bone
MANDIBLE = L.Piece({p: ch for p, ch in _filled_ink(BASE["jaw"]).items() if p[0] >= HINGE[0]})
THROAT_SKIN = {p: ch for p, ch in BASE["jaw"].items() if p[0] < HINGE[0]}


def place_jaw(drop, at, throat=0):
    """(jaw, pouch, inside): closed, the jaw as drawn, with the gular pouch sagging throat px (its top row
    stretched, the rows under it moved down; its ends one px at most). Opened, the mandible turns as one solid
    piece about the hinge (behind and below the eye) until its lip has dropped drop px: every pixel of it turns,
    none is moved by columns, so its underside stays one clean stair-step line; the throat behind the hinge stays.
    The gular pouch's pixels are returned apart in both (its own part in the part strip).
    inside: the mandible's inner face, the part above the upper lip's line at rest (turned back to the drawing,
    a pixel's centre lies above it), in the mouth's colour: so the opened jaw shows the band the drawing shows,
    under a straight mouth line, no thicker."""
    if drop:
        hinge, tip = complex(*HINGE), complex(*JAW_FRONT) - complex(*HINGE)
        ang = math.atan2(drop, abs(tip))
        rot = complex(math.cos(ang), math.sin(ang))
        turned = MANDIBLE.turned(HINGE, JAW_FRONT, HINGE, hinge + tip * rot)
        cols, row = THROAT
        out, pouch, inside = {}, {}, {}
        for (x, y), ch in THROAT_SKIN.items():
            (pouch if x in cols and y >= row else out)[(x + at[0], y + at[1])] = ch
        for (x, y), ch in turned.items():
            s = hinge + (complex(x, y) - hinge) / rot             # the pixel's centre back in the drawing
            if s.imag < LIP_LINE[0] + LIP_LINE[1] * s.real + 0.5:
                inside[(x + at[0], y + at[1])] = "m"
            else:
                in_pouch = rnd(s.real) in cols and rnd(s.imag) >= row
                (pouch if in_pouch else out)[(x + at[0], y + at[1])] = ch
        return out, pouch, inside
    cols, row = THROAT
    out, pouch = {}, {}
    for (x, y), ch in BASE["jaw"].items():
        part = pouch if x in cols and y >= row else out
        sag = min(throat, 1 if x in (cols[0], cols[-1]) else 2) if part is pouch else 0   # rounded: ends 1 px
        part[(x + at[0], y + at[1] + sag)] = ch
        if y == row:
            for k in range(sag):
                part[(x + at[0], y + at[1] + k)] = ch
    return out, pouch, {}


def place_mouth(jaw, inside, at):
    """The open mouth: the mandible's inner face, and every pixel between the upper lip's line (the head's lowest
    row) and the turned jaw's top, from the hinge to the lip's tip, solid dark red, so no air shows inside it."""
    top = {}
    for x, y in list(jaw) + list(inside):
        top[x] = min(y, top.get(x, y))
    out = dict(inside)
    for x in range(HINGE[0] + at[0], LIP + at[0] + 1):
        lo = HEAD_LOW.get(x - at[0])
        if lo is None or x not in top:
            continue
        for y in range(lo + at[1] + 1, top[x]):
            out[(x, y)] = "m"
    return out


def place_tongue(tongue, at):
    """The tongue's rod from the mouth to reach - CLUB - stretch, then its club (the middle column repeated stretch
    times) ending at reach; a reach past the drawn one draws the rod's last column on. None: in the mouth."""
    if tongue is None:
        return {}
    reach, stretch = tongue
    full = C.RIG["tongue_reach"]
    club0 = full - CLUB + 1
    out = {}
    for (x, y), ch in BASE["tongue"].items():
        if x < club0:
            nx = x
            if nx > reach - CLUB - stretch:
                continue
        else:
            nx = x - full + reach
            if x < club0 + CLUB // 2:
                nx -= stretch
        out[(nx + at[0], y + at[1])] = ch
    for x in range(club0, reach - CLUB + 1):       # past the drawn reach: the rod's last column, drawn on
        for (x0, y), ch in BASE["tongue"].items():
            if x0 == club0 - 1:
                out[(x + at[0], y + at[1])] = ch
    for i in range(stretch):                       # the club's middle, drawn longer on the smear frame
        for (x, y), ch in BASE["tongue"].items():
            if x == club0 + CLUB // 2:
                out[(x - full + reach - stretch + i + at[0], y + at[1])] = ch
    return out


# the hit at the club: a flash (a plus round the club's tip), then pixels flung out from it
SPARK_FLASH = [((0, 0), "w"), ((1, 0), "w"), ((2, 0), "s"), ((-1, -1), "w"), ((0, -1), "w"), ((1, -1), "s"),
               ((0, -2), "s"), ((-1, 1), "w"), ((0, 1), "w"), ((1, 1), "s"), ((0, 2), "s"), ((3, 0), "s")]
SPARK_FLY = [((3, -3), "w"), ((4, -3), "s"), ((4, 0), "w"), ((5, 0), "s"), ((3, 3), "w"), ((4, 4), "s"),
             ((0, -4), "s"), ((1, -4), "w"), ((0, 4), "s"), ((1, 5), "w")]


def place_spark(spark, tongue, at):
    if not spark or tongue is None:
        return {}
    tip = (tongue[0] - 2 + at[0], C.RIG["mouth"][1] + at[1])        # the club's middle, near its front
    return {(tip[0] + dx, tip[1] + dy): ch for (dx, dy), ch in (SPARK_FLASH if spark == 1 else SPARK_FLY)}


def band_of(y):
    """The head's band a drawing row belongs to: 0 low, 1 eye, 2 cap."""
    return 2 if y < EYE_ROW else 1 if y < LOW_ROW else 0


def place_head(head, lift):
    """The head layer at head, each band moved lift[band] px more (drawn low band first, the cap last). Where a
    band sits higher than the one under it, its last row is drawn again in the gap, so the head stretches a pixel
    there and never opens; where it sits lower, it covers the band under it by a row."""
    out = {}
    for band in (0, 1, 2):
        for (x, y), ch in BASE["head"].items():
            if band_of(y) == band:
                out[(x + head[0], y + head[1] + lift[band])] = ch
    for r, up, low in ((LOW_ROW, 1, 0), (EYE_ROW, 2, 1)):
        if lift[up] < lift[low]:
            for (x, y), ch in BASE["head"].items():
                if y == r - 1 and (x, r) in BASE["head"]:
                    for k in range(lift[up] + 1, lift[low] + 1):
                        out.setdefault((x + head[0], y + head[1] + k), ch)
    return out


TURRET = BASE["turret"]


def place_turret(at, roll):
    """The turret at its place, its shading rolled by roll inside its own outline: each inner pixel takes the
    colour the drawing has roll px behind it, when that pixel is inside too (the cone turns; the rim stays)."""
    out = {}
    inner = {p for p, ch in TURRET.items() if ch not in C.INK}
    for (x, y), ch in TURRET.items():
        src = (x - roll[0], y - roll[1])
        if (x, y) in inner and src in inner:
            ch = TURRET[src]
        out[(x + at[0], y + at[1])] = ch
    return out


def layers(pose):
    """[(pixels, part, lit outline?)] back to front for one pose."""
    body = pose["body"]
    lift = pose.get("lift", (0, 0, 0))
    low = (pose["head"][0], pose["head"][1] + lift[0])          # the jaw, the mouth and the tongue hang here
    eye = (pose["head"][0], pose["head"][1] + lift[1])          # the turret and the pupil sit here
    tur = (eye[0] + pose["turret"][0], eye[1] + pose["turret"][1])
    pup = (tur[0] + pose["pupil"][0], tur[1] + pose["pupil"][1])
    legs = {leg: L.LEG[leg].place(body, *pose["legs"][leg]) for leg in LEGS}
    out = []
    for leg in ("far_hind", "far_front"):
        out += [(px, leg, False) for px, _ in legs[leg]]
    out += [(px, part, True) for px, part in place_tail(pose["tail"], body)]
    out.append((place_body(body, pose["breath"]), "body", True))
    out.append((C.layer_pixels("neck", *pose.get("neck", (0, 0))), "body", True))
    jaw, pouch, inside = place_jaw(pose["jaw"], low, pose.get("throat", 0))
    if pose["jaw"]:
        out.append((place_mouth(jaw, inside, low), "tongue", False))
    out.append((place_tongue(pose["tongue"], low), "tongue", False))
    out.append((pouch, "throat", True))
    out.append((jaw, "jaw", True))
    out.append((place_head(pose["head"], lift), "head", True))
    out.append((place_turret(tur, pose.get("roll", (0, 0))), "head", True))
    out.append((C.layer_pixels("pupil", *pup), "head", True))
    for leg in ("near_hind", "near_front"):
        out += [(px, leg, True) for px, _ in legs[leg]]
    out.append((place_spark(pose.get("spark"), pose["tongue"], low), "spark", False))
    return out


def render(pose):
    """{(x, y): (char, part)} for one pose: the layers back to front, then the outline on every edge a pose
    opened (lit ink where the air is above or to the left of a lit layer, dark ink elsewhere); ink already
    drawn stays as drawn (the far legs are inked all round)."""
    canvas, lit = {}, {}
    for px, part, is_lit in layers(pose):
        for p, ch in px.items():
            canvas[p] = (ch, part)
            lit[p] = is_lit
    out = dict(canvas)
    for (x, y), (ch, part) in canvas.items():
        nbs = ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1))
        if part in EFFECT_PARTS or ch in C.EFFECTS:
            continue
        if ch in C.INK:
            continue
        air = [n for n in nbs if n not in canvas or canvas[n][1] == "spark"]
        if air:
            on_lit = lit[(x, y)] and any(n in ((x, y - 1), (x - 1, y)) for n in air)
            out[(x, y)] = (LIT if on_lit else DARK, part)
    return out
