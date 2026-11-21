"""The beast's rig: the drawing's layers (creature.py) placed by a pose, by whole pixels only, and drawn back to
front with the outline last. animate.py writes the poses; this file turns one pose into one frame.

A pose is a dict (whole pixels unless it says otherwise; y grows downward):
  body      (dx, rear_dy, front_dy, stretch)  the trunk, one piece: the hips ride (dx, rear_dy), the shoulders
            (dx + stretch, front_dy); the columns between take the mix, a tilt or a stretch in whole-pixel steps
            (a column the stretch leaves empty is filled from its neighbour), never a wave. Moved whole (rear_dy
            equal to front_dy) its topline and belly line never step; a tilt of 2 px or more spreads as a staircase
            over its length; a tilt of a lone pixel would cut it in two bands, so the poses never ask for one
  head      (dx, dy)   the head against the shoulders; the neck and ruff bend between the two
  poll      px         a small turn of the head: its back (the skull behind the eye, under the ears, columns
            before NOD_X) px lower than its front, for the pose a chain carries a rise or a fall from the neck to
            the muzzle, so the head's pixel spreads over two poses instead of stepping as one block
  neck      (dx, dy) or None  where the neck's top goes, against the shoulders (None: with the head); a neck a pose
            behind the head stages a 1-px head move over two poses
  ears      (dx, dy)   the ears against the head (a pose of lag); flick, flick_far: an ear's tip back by px
  pin       px         both ears laid back: each ear's rows slid back from its base, the tip pin px
  look      0 or 1     the pupil at the back of the eye (a glance back)
  jaw       px         how far the jaw's front drops about its hinge (behind and below the eye); 0 is shut
  tail      [(dx, dy), ...]  each tail link's own move (root first); a link adds its parent's, and the rows
            between two links' control rows take the mix, so the tail bends along its length
  tail_lift px or (px, span)  the tail raised: its columns lifted by their reach behind the root, the full lift
            span px back (TAIL_SPAN by default): a whip up and back
  legs      {leg: (foot_dx, lift, joint_dx, joint_dy, fold)}  the paw against its drawn place, its lift, the middle
            joint's own push (the hock or the elbow), and how far a forepaw folds back at the wrist (degrees)
  fx        [(x, y, char)]  effect pixels drawn over everything, no outline

The outline pass also closes five edge pixels the drawing left without an outline colour (two lit tufts on the back
take the lit line, three on the ruff's shadow side the ink), so every frame, the rest pose included, is closed.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature as C  # noqa: E402

FX = {"x": "#fff9e6", "y": "#ffd25e", "z": "#c3cdf0", "Z": "#7d89b8"}   # flash, spark, streak and dust, fading
RGB = dict(C.PALETTE, **FX)
OUTLINE = set("oabcde")           # the ink and the lit line (the ramp's darks on the top and left edges)
LIT = "d"                          # an edge opened on the lit side (air above or to the left) takes the lit line
KEEP = set("w")                    # the nose's glint stays on the edge, as drawn

HIP_Y, SHANK_Y, HOCK_Y, HPAW_Y = 28, 35, 43, 49   # hind leg: the swing's top row, the gaskin, the hock, the paw
SHOULDER_Y, ELBOW_Y, WRIST_Y, FPAW_Y = 29, 36, 45, 52   # foreleg: the swing's top row, elbow, wrist
REAR_X, FRONT_X = 30, 46                   # the trunk's tilt runs between these columns
NOD_X = 64                                 # the head's back (poll) lies before this column: the seam of its small
                                           # turn runs under the near ear and into the cheek ruff, behind the eye
NECK_TOP, NECK_LOW = 17, 29                # neck rows at and above NECK_TOP go with the head; at and below, the body
HINGE_X, JAW_FRONT = C.PIVOTS["jaw_hinge"][0], 73
EAR_BASE = 8                               # an ear's flick shears it above this row
LEGS = {"3": "near_hind", "1": "far_hind", "4": "near_front", "2": "far_front"}
WRIST_X = {"4": C.PIVOTS["wrist_near"][0] - 2, "2": C.PIVOTS["wrist_far"][0] - 2}   # a paw folds at its wrist's back
NEAR = "34"

PART_RGB = {"body": "#c8c8c8", "neck": "#8c8c8c", "head": "#e05050", "jaw": "#e0a040", "mouth": "#ff00ff",
            "ear_near": "#ff9090", "ear_far": "#a03030", "tail": "#3070c8", "near_hind": "#50d060",
            "far_hind": "#208040", "near_front": "#e0e050", "far_front": "#909020", "fx": "#ffffff"}


def rnd(v):
    """Round half away from zero, the same way up and down."""
    return int(math.floor(abs(v) + 0.5)) * (1 if v >= 0 else -1)


def clip01(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else v


BASE = {k: C.layer_pixels(k) for k in C.ORDER}


def bend(pixels, y0, y1, a, b, vy=None):
    """Rows of a layer moved along a joint: rows at and above y0 by a, at and below y1 by b, rows between by the
    mix (each rounded to whole pixels). vy = (top, bottom) gives the vertical move its own rows, so a limb that
    shortens loses its rows where it is narrow. A row moved down past the next row's place is repeated into the
    gap, so the limb stretches instead of tearing."""
    v0, v1 = vy or (y0, y1)
    return path_rows(pixels, [(y0, a[0], None), (y1, b[0], None)], [(v0, None, a[1]), (v1, None, b[1])])


def _lerp(ctrl, y, i):
    pts = [(cy, c[i]) for cy, *c in ctrl]
    if y <= pts[0][0]:
        return pts[0][1]
    for (ya, va), (yb, vb) in zip(pts, pts[1:]):
        if y <= yb:
            return va + (vb - va) * (y - ya) / (yb - ya) if yb != ya else vb
    return pts[-1][1]


def path_rows(pixels, xs, ys):
    """Rows moved by piecewise-linear moves: xs [(row, dx, None)], ys [(row, None, dy)], each held flat past its
    ends and rounded per row; a gap a stretch opens is filled by repeating the row above it."""
    rows = {}
    for (x, y), ch in pixels.items():
        rows.setdefault(y, {})[x] = ch
    xc = [(r, d) for r, d, _ in xs]
    yc = [(r, d) for r, _, d in ys]
    out, last = {}, None
    for y in sorted(rows):
        dx, dy = rnd(_lerp(xc, y, 0)), rnd(_lerp(yc, y, 0))
        ty = y + dy
        for yy in ([ty] if last is None or ty <= last + 1 else range(last + 1, ty + 1)):
            for x, ch in rows[y].items():
                out[(x + dx, yy)] = ch
        last = ty if last is None else max(last, ty)
    return out


def turn(pixels, pivot, deg):
    """A part turned about a pivot by three shears (x, then y, then x; each row or column moved whole), so every
    pixel is kept once: no hole and no doubled pixel, whatever the angle. Positive turns a part hanging below the
    pivot back (its lower end to the left)."""
    if not deg:
        return dict(pixels)
    a = math.radians(deg)
    t, s = -math.tan(a / 2), math.sin(a)
    px, py = pivot
    out = {}
    for (x, y), ch in pixels.items():
        u, v = x - px, y - py
        u += rnd(t * v)
        v += rnd(s * u)
        u += rnd(t * v)
        out[(u + px, v + py)] = ch
    return out


# ---- the trunk, the tail ---------------------------------------------------------------------------------------------
def column_move(body, x):
    """(dx, dy) of trunk column x: the rear's up to REAR_X, the front's from FRONT_X, the mix between."""
    dx, rear, front, stretch = body
    t = clip01((x - REAR_X) / (FRONT_X - REAR_X))
    return dx + rnd(stretch * t), rnd(rear + (front - rear) * t)


def place_body(body):
    """The trunk, one layer moved column by column (column_move): whole, tilted or stretched, never in bands."""
    cols = {}
    for (x, y), ch in BASE["B"].items():
        cols.setdefault(x, {})[y] = ch
    out, last = {}, None
    for x in sorted(cols):
        dx, dy = column_move(body, x)
        tx = x + dx
        for xx in ([tx] if last is None or tx <= last + 1 else range(last + 1, tx + 1)):
            for y, ch in cols[x].items():
                out[(xx, y + dy)] = ch
        last = tx if last is None else max(last, tx)
    return out


# the tail bends as a chain: each link's move is set at one control row and the rows between take the mix, so the
# tail curves along its length and keeps every row (a row shear; a lift repeats or covers a row at most)
TAIL_ROWS = (23, 30, 37, 45)                 # the root under the croup, two middles, the pale tip


def tail_offsets(moves, base):
    """Each link's whole-pixel place: its own move plus every parent's, plus the rump's (base)."""
    out, ox, oy = [], base[0], base[1]
    for dx, dy in moves:
        ox, oy = ox + dx, oy + dy
        out.append((ox, oy))
    return out


TAIL_ROOT_X, TAIL_SPAN = C.PIVOTS["tail_root"][0], 16   # a raised tail lifts its columns by their reach behind the root


def place_tail(moves, base, lift=0):
    """The tail bent as a chain (rows moved by the links), then raised: each column lifted whole by lift times its
    reach behind the root (span px back, TAIL_SPAN unless lift is (lift, span), takes the full lift), a shear across
    the bend, so the swung-back tail turns up and back about its root and keeps every pixel. A short span lifts the
    hanging length bodily (the root turning first); a long one turns the tip up most."""
    offs = tail_offsets(moves, base)
    ctrl = [(r, ox, oy) for r, (ox, oy) in zip(TAIL_ROWS, offs)]
    px = path_rows(BASE["T"], [(r, dx, None) for r, dx, _ in ctrl], [(r, None, dy) for r, _, dy in ctrl])
    lift, span = lift if isinstance(lift, tuple) else (lift, TAIL_SPAN)
    if lift:
        root = TAIL_ROOT_X + base[0]
        px = {(x, y - rnd(lift * clip01((root - x) / span))): ch for (x, y), ch in px.items()}
    return [(px, "tail")]


# ---- legs ------------------------------------------------------------------------------------------------------------
def place_leg(leg, pose_leg, top):
    """The segments of one leg ([pixels, ...] top first). The hip or shoulder rides the trunk (top); the paw sits
    at its drawn place plus foot_dx, lifted; the middle joint (hock, elbow) goes where it lies between the two at
    rest, plus its own push. The leg swings from HIP_Y or SHOULDER_Y down, and a lift shortens only its narrow
    shank (the gaskin over the hock, the forearm over the wrist), so it keeps its mass; a forepaw folds back at the
    wrist, turned whole about it by fold degrees (pixel for pixel; at 90 its sole faces back)."""
    fdx, lift, jdx, jdy, fold = pose_leg
    foot = (fdx, -lift)
    if leg in "31":
        t = (HOCK_Y - HIP_Y) / (HPAW_Y - HIP_Y)
        hock = (rnd(top[0] + (foot[0] - top[0]) * t) + jdx, foot[1] + jdy)
        return [bend(BASE[leg + "u"], HIP_Y, HOCK_Y, top, hock, (SHANK_Y, HOCK_Y)),
                bend(BASE[leg + "l"], HOCK_Y, HPAW_Y, hock, foot)]
    t = (ELBOW_Y - SHOULDER_Y) / (WRIST_Y - SHOULDER_Y)
    elbow = (rnd(top[0] + (foot[0] - top[0]) * t) + jdx, top[1] + jdy)
    folded = turn(BASE[leg + "p"], (WRIST_X[leg], WRIST_Y), fold)
    low = FPAW_Y - (1 if lift else 0)                       # a turned paw stays clear of the ground while lifted
    up = max(0, max(y for _, y in folded) + foot[1] - low)
    paw = {(x + foot[0], y + foot[1] - up): ch for (x, y), ch in folded.items()}
    return [bend(BASE[leg + "u"], SHOULDER_Y, ELBOW_Y, top, elbow), paw,       # the paw under the forearm's end
            bend(BASE[leg + "l"], ELBOW_Y, WRIST_Y, elbow, foot)]               # (drawn alike where they overlap)


# ---- the head --------------------------------------------------------------------------------------------------------
JAW_FUR_Y = 19                             # the lower jaw's fur row (the gums above it, its ink line below)


def place_jaw(drop, at):
    """The lower jaw turned down about the hinge (behind and below the eye) until its front has dropped drop px; it
    swings back a little as it turns, as a jaw does. Opened 2 px or more it comes out from behind the cheek ruff and
    shows its side: the fur row twice, the ink line under it, so a fur jaw with its tip reads under the open mouth."""
    deep = 1 if drop >= 2 else 0
    jaw = {}
    for (x, y), ch in BASE["J"].items():
        jaw[(x, y + (deep if y > JAW_FUR_Y else 0))] = ch
        if deep and y == JAW_FUR_Y:
            jaw[(x, y + 1)] = ch
    deg = math.degrees(math.atan2(drop, JAW_FRONT - HINGE_X))
    return {(x + at[0], y + at[1]): ch for (x, y), ch in turn(jaw, C.PIVOTS["jaw_hinge"], deg).items()}


def place_mouth(drop, at):
    """The open mouth: the drawing's mouth layer, and the dark inside drawn on down to the dropped jaw (the gums
    under the lip), with the tongue lying on the jaw's floor."""
    if not drop:
        return {}
    head_bottom = {}
    for (x, y) in BASE["H"]:
        head_bottom[x] = max(y, head_bottom.get(x, y))
    jaw = place_jaw(drop, (0, 0))
    jaw_top = {}
    for (x, y) in jaw:
        jaw_top[x] = min(y, jaw_top.get(x, y))
    out = {}
    for x in range(HINGE_X + 1, JAW_FRONT + 1):         # down to the jaw; past the jaw's tip the front is open
        for y in range(head_bottom.get(x, 18) + 1, jaw_top.get(x, 19)):
            out[(x + at[0], y + at[1])] = BASE["M"].get((x, y), "m")
    for (x, y), ch in BASE["G"].items():
        if x in jaw_top:
            out[(x + at[0], jaw_top[x] - 21 + y + at[1])] = ch
    return out


def place_head(look, poll=0):
    """The head layer; its back (columns before NOD_X) poll px lower than its front (a small turn). Where the back
    sits higher, its lowest row is drawn again in the gap under it, so the turned head never opens."""
    px = dict(BASE["H"])
    if look:                                   # the pupil to the back of the eye: E E o -> o E E
        px[(66, 14)], px[(67, 14)], px[(68, 14)] = "o", "E", "E"
    if not poll:
        return px
    out = {}
    for (x, y), ch in sorted(px.items(), key=lambda t: t[0][1]):
        if x < NOD_X:
            out[(x, y + poll)] = ch
            if poll < 0 and (x, y + 1) not in px:      # the back raised: its last row drawn again under it
                out[(x, y)] = ch
        else:
            out[(x, y)] = ch
    return out


def place_ear(key, at, flick=0, pin=0):
    """An ear and a 2-row strip of its base continued downward (drawn under the head, so an ear a pixel off the
    head never comes off it). The near ear flicks by shearing its tip back above EAR_BASE; pinned, an ear lies back
    as a whole: each row slides back in proportion to its height over the base, the tip pin px (whole rows move, so
    the ear keeps every pixel and its edges stay drawn lines)."""
    px = BASE[key]
    base = max(y for _, y in px)
    top = min(y for _, y in px)
    out, strip = {}, {}
    for (x, y), ch in px.items():
        h = clip01((EAR_BASE - y) / 4.0)
        lay = rnd(pin * clip01((base - 1 - y) / (base - 1 - top)))
        out[(x + at[0] - rnd(flick * h) - lay, y + at[1])] = ch
        if y == base or (key == "N" and y == base - 1):
            for k in (1, 2):
                strip[(x + at[0], y + at[1] + k)] = ch
    return out, strip


# ---- the frame -------------------------------------------------------------------------------------------------------
def layers(pose):
    """[(pixels, part, near?)] back to front for one pose."""
    body = pose["body"]
    rear = (body[0], body[1])
    front = (body[0] + body[3], body[2])
    hd = (front[0] + pose["head"][0], front[1] + pose["head"][1])
    ea = (hd[0] + pose["ears"][0], hd[1] + pose["ears"][1])
    legs = {}
    for leg in LEGS:
        top = rear if leg in "31" else front
        legs[leg] = place_leg(leg, pose["legs"][LEGS[leg]], top)
    out = []
    def segs(leg):
        return [(seg, LEGS[leg], leg in NEAR) for seg in legs[leg]]
    for leg in "12":
        out += segs(leg)
    out += [(px, part, True) for px, part in place_tail(pose["tail"], rear, pose["tail_lift"])]
    out.append((place_body(body), "body", True))
    out += segs("4")
    nk = pose.get("neck") or pose["head"]
    out.append((bend(BASE["K"], NECK_TOP, NECK_LOW, (front[0] + nk[0], front[1] + nk[1]), front), "neck", True))
    out += segs("3")
    far, far_strip = place_ear("F", ea, pose["flick_far"], pose["pin"])
    near, near_strip = place_ear("N", ea, pose["flick"], pose["pin"])
    out += [(far_strip, "ear_far", True), (far, "ear_far", True)]
    out.append((place_mouth(pose["jaw"], hd), "mouth", True))
    out.append((place_jaw(pose["jaw"], hd), "jaw", True))
    out.append((near_strip, "ear_near", True))
    out.append(({(x + hd[0], y + hd[1]): ch for (x, y), ch in place_head(pose["look"], pose["poll"]).items()},
                "head", True))
    out.append((near, "ear_near", True))
    return out


def render(pose):
    """{(x, y): (char, part)} for one pose: the layers back to front (a pocket two legs close filled, fill_pockets);
    a far leg's pixel beside a near leg's fill turns to ink, so the legs read apart; then the outline last: an edge
    pixel whose layer had it inside (a fill a pose uncovered) or whose colour is no outline colour takes the lit line
    where the air is above or to the left, the ink elsewhere. The effects go on top, with no outline."""
    canvas, owner = {}, {}
    placed = layers(pose)
    for i, (px, part, _) in enumerate(placed):
        for p, ch in px.items():
            canvas[p] = ch
            owner[p] = i
    fill_pockets(canvas, owner, placed)
    out = {p: (ch, placed[owner[p]][1]) for p, ch in canvas.items()}
    far = {i for i, (_, part, _) in enumerate(placed) if part in ("far_hind", "far_front")}
    near_leg = {i for i, (_, part, _) in enumerate(placed) if part in ("near_hind", "near_front")}
    for (x, y), ch in canvas.items():
        i = owner[(x, y)]
        if ch == "o":
            continue
        nbrs = ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1))
        if i in far and any(owner.get(n) in near_leg and canvas[n] != "o" for n in nbrs):
            out[(x, y)] = ("o", out[(x, y)][1])
            continue
        air = [n for n in nbrs if n not in canvas]
        if not air:
            continue
        inside = all(n in placed[i][0] for n in nbrs)
        if inside or (ch not in OUTLINE and ch not in KEEP):
            lit = any(n in ((x, y - 1), (x - 1, y)) for n in air)
            new = (ch if ch in "cde" else LIT) if lit else "o"
            if i in far and lit:
                new = "b"
            out[(x, y)] = (new, out[(x, y)][1])
    trim_nubs(out)
    for x, y, ch in pose.get("fx", ()):
        out[(x, y)] = (ch, "fx")
    return out


LEG_PARTS = ("near_hind", "far_hind", "near_front", "far_front")
POCKET_MAX = 24                            # px: a closed pocket of air this small between the legs is shadow


def fill_pockets(canvas, owner, placed):
    """Two legs crossing can close a little pocket of air between them, which reads at 1x as a hole punched through
    the figure. Fill such a pocket (air not joined to the outside, with a far leg on its rim and only legs or the
    trunk round it) with the far leg's core shadow, as its own: the far side of the body seen between the legs."""
    def nbrs(p):
        return ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1))
    xs, ys = [x for x, _ in canvas], [y for _, y in canvas]
    box = {(x, y) for x in range(min(xs) - 1, max(xs) + 2) for y in range(min(ys) - 1, max(ys) + 2)} - set(canvas)
    outside, todo = set(), [(min(xs) - 1, min(ys) - 1)]
    while todo:                                # the air joined to the outside, by flood fill from a corner
        p = todo.pop()
        if p in box and p not in outside:
            outside.add(p)
            todo += nbrs(p)
    holes = box - outside
    while holes:
        comp, todo = set(), [holes.pop()]
        while todo:
            p = todo.pop()
            comp.add(p)
            for n in nbrs(p):
                if n in holes:
                    holes.discard(n)
                    todo.append(n)
        rim = [owner[n] for p in comp for n in nbrs(p) if n in owner]
        far = [i for i in rim if placed[i][1] in ("far_hind", "far_front")]
        if len(comp) > POCKET_MAX or not far or any(placed[i][1] not in LEG_PARTS + ("body",) for i in rim):
            continue                           # only between the legs (the gap under the tail is drawn air)
        for p in comp:
            canvas[p], owner[p] = "b", far[0]


def trim_nubs(out):
    """A bent leg's rows slide past each other, so a drawn edge pixel can end up sticking out alone: a leg pixel
    with air on three sides is a burr, not a line. Take it off (twice, for a two-pixel spur)."""
    for _ in range(2):
        nubs = [(x, y) for (x, y), (ch, part) in out.items() if part in LEG_PARTS and
                sum(n not in out for n in ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1))) >= 3]
        for p in nubs:
            del out[p]


def head_world(pose):
    """Where the head group sits (dx, dy) against its drawn place."""
    b = pose["body"]
    return b[0] + b[3] + pose["head"][0], b[2] + pose["head"][1]


def stand(**kw):
    """The rest pose, with any field replaced."""
    pose = dict(body=(0, 0, 0, 0), head=(0, 0), poll=0, neck=None, ears=(0, 0), flick=0, flick_far=0, pin=0, look=0,
                jaw=0, tail=[(0, 0)] * 4, tail_lift=0, legs={leg: (0, 0, 0, 0, 0) for leg in LEGS.values()}, fx=[])
    pose.update(kw)
    return pose
