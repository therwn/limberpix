"""The lizard's legs: each one a thigh (or upper arm), a shin (or forearm) and a foot, posed by two-bone inverse
kinematics and drawn by turning the drawing's own pixels, never by shearing rows.

Why not shear: a thin shin sheared sideways keeps its width per row, so it thins across its length into a 1-2 px
noodle with stair-step edges, and its ink lines land inside the limb. Turned instead, a limb keeps its width, its
shading bands and its outline. The turn is RotSprite-like: the layer is drawn 8x larger by Scale2x (three times),
each game pixel of the turned limb takes the colour under its centre, mapped back into that big copy. A limb at its
drawn angle is copied pixel for pixel, so the rest pose is exactly the drawing.

  hip, knee, ankle  creature.RIG[leg][:3]; the hip rides the body, the ankle is where the pose puts the foot
  the knee          found from the two bone lengths (law of cosines), on the side the drawing bends it: the hind
                    knees forward, the front elbows back; a foot that lifts folds the leg up over the knee
  the shin          turned, and widened across its bone as it turns upright, so its rows keep the drawing's width
                    (a slanted shin is narrower across its bone than along a row; turned alone it would thin)
  the foot          moved whole, never turned: it keeps its pads, soles and ground ink
  the far legs      drawn a full value step darker in creature.py and inked all round, kept as drawn
"""
import cmath
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature as C  # noqa: E402

UP = 8                      # the big copy the turn samples from: Scale2x three times
OVERLAP = 2.0               # px of a bone kept past its joint (the drawn knee disc shared by both layers)
LEGS = {   # leg: (upper layer, lower layer, near?)
    "near_hind": ("near_hind_thigh", "near_hind_shin", True),
    "far_hind": ("far_hind_thigh", "far_hind_shin", False),
    "far_front": ("far_front_arm", "far_front_hand", False),
    "near_front": ("near_front_arm", "near_front_hand", True),
}


def _pt(p):
    return p if isinstance(p, complex) else complex(p[0], p[1])


def _scale2x(rows):
    """One Scale2x (EPX) pass over a grid of characters (None for air)."""
    h, w = len(rows), len(rows[0])
    out = [[None] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        for x in range(w):
            p = rows[y][x]
            a = rows[y - 1][x] if y else None
            b = rows[y][x + 1] if x + 1 < w else None
            c = rows[y][x - 1] if x else None
            d = rows[y + 1][x] if y + 1 < h else None
            e0 = a if (c == a and c != d and a != b) else p
            e1 = b if (a == b and a != c and b != d) else p
            e2 = c if (d == c and d != b and c != a) else p
            e3 = d if (b == d and b != a and d != c) else p
            out[2 * y][2 * x], out[2 * y][2 * x + 1] = e0, e1
            out[2 * y + 1][2 * x], out[2 * y + 1][2 * x + 1] = e2, e3
    return out


class Piece:
    """A piece of a layer: its pixels, and its big copy for turning."""

    def __init__(self, pixels):
        self.px = pixels
        xs, ys = [x for x, _ in pixels], [y for _, y in pixels]
        self.x0, self.y0 = min(xs) - 1, min(ys) - 1
        w, h = max(xs) - self.x0 + 2, max(ys) - self.y0 + 2
        rows = [[pixels.get((self.x0 + i, self.y0 + j)) for i in range(w)] for j in range(h)]
        for _ in range(3):
            rows = _scale2x(rows)
        self.big = rows

    def sample(self, sx, sy):
        i, j = math.floor((sx - self.x0 + 0.5) * UP), math.floor((sy - self.y0 + 0.5) * UP)
        if 0 <= j < len(self.big) and 0 <= i < len(self.big[0]):
            return self.big[j][i]
        return None

    def turned(self, a0, b0, a1, b1, keep_rows=False):
        """The piece moved so that its point a0 lands on a1 and b0 on b1 (a turn and a slight stretch about a0).
        keep_rows: the limb is also widened (or narrowed) across its bone so that a row through it keeps the width
        the drawing gives it: a slanted shin turned upright stays as wide as drawn, instead of thinning to the
        narrower width it has across its own bone."""
        a0, b0, a1, b1 = _pt(a0), _pt(b0), _pt(a1), _pt(b1)
        u0, u1 = b0 - a0, b1 - a1
        t = a1 - a0
        if abs(u1 / u0 - 1) < 1e-6 and abs(t.real - round(t.real)) < 1e-6 and abs(t.imag - round(t.imag)) < 1e-6:
            dx, dy = round(t.real), round(t.imag)
            return {(x + dx, y + dy): ch for (x, y), ch in self.px.items()}
        w = 1.0
        if keep_rows:
            w = max(1.0, min(1.4, (abs(u1.imag) / abs(u1)) / (abs(u0.imag) / abs(u0))))

        def fwd(q):
            k = (q - a0) / u0
            return a1 + u1 * complex(k.real, k.imag * w)

        def back(q):
            k = (q - a1) / u1
            return a0 + u0 * complex(k.real, k.imag / w)

        x1, y1 = self.x0 + len(self.big[0]) / UP, self.y0 + len(self.big) / UP
        corners = [fwd(complex(*p)) for p in ((self.x0, self.y0), (x1, self.y0), (self.x0, y1), (x1, y1))]
        out = {}
        for y in range(math.floor(min(c.imag for c in corners)) - 1, math.ceil(max(c.imag for c in corners)) + 2):
            for x in range(math.floor(min(c.real for c in corners)) - 1, math.ceil(max(c.real for c in corners)) + 2):
                s = back(complex(x, y))
                ch = self.sample(s.real, s.imag)
                if ch is not None:
                    out[(x, y)] = ch
        return out


def _side(p, a, b):
    """Which side of the line a->b the point p lies on: +1 or -1 (y down)."""
    v, w = b - a, p - a
    return 1 if (v.real * w.imag - v.imag * w.real) >= 0 else -1


def _along(p, a, b):
    """How far along the bone a->b the point p lies, in px from a."""
    v = b - a
    return ((p - a) * v.conjugate()).real / abs(v)


class Leg:
    def __init__(self, leg):
        upper, lower, self.near = LEGS[leg]
        self.hip, self.knee, self.ankle = (_pt(p) for p in C.RIG[leg][:3])
        up, low = C.layer_pixels(upper), C.layer_pixels(lower)
        ln1, ln2 = abs(self.knee - self.hip), abs(self.ankle - self.knee)
        # the thigh from just above the hip down to its knee disc; the shin from the knee down to the ankle; the
        # foot below (every pixel of a layer lands in one piece, so the rest pose is the drawing exactly)
        self.upper = Piece({p: ch for p, ch in up.items() if -OVERLAP <= _along(_pt(p), self.hip, self.knee)})
        # the thigh's top above the hip lies on the body: it rides the body and is not turned (turned, it would
        # swing the other way into the flank)
        self.root = {p: ch for p, ch in up.items() if _along(_pt(p), self.hip, self.knee) < 0}
        ay = int(self.ankle.imag)
        self.lower = Piece({p: ch for p, ch in low.items() if p[1] <= ay})
        self.foot = {p: ch for p, ch in low.items() if p[1] >= ay}
        self.l1, self.l2 = ln1, ln2
        self.bend = _side(self.knee, self.hip, self.ankle)

    def knee_for(self, hip, ankle):
        """The knee for a hip and an ankle: the bones keep their lengths (stretched evenly only when the foot is out
        of reach), bent the way the drawing bends them."""
        d = abs(ankle - hip)
        l1, l2 = self.l1, self.l2
        if d > l1 + l2:
            s = d / (l1 + l2) * 1.0001
            l1, l2 = l1 * s, l2 * s
        cos_a = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
        k = hip + (ankle - hip) / d * l1 * cmath.exp(1j * self.bend * math.acos(cos_a))
        if _side(k, hip, ankle) != self.bend:
            k = hip + (ankle - hip) / d * l1 * cmath.exp(-1j * self.bend * math.acos(cos_a))
        return k

    def place(self, body, foot_dx, lift, knee_push=0.0):
        """[(pixels, piece name)] back to front: the thigh, the shin, the foot. body moves the hip; the foot goes
        foot_dx from its drawn place and lifts by lift; knee_push moves the knee forward (px) on a swing."""
        hip = self.hip + complex(*body)
        ankle = self.ankle + complex(foot_dx, -lift)
        moved = not (body == (0, 0) and foot_dx == 0 and lift == 0 and not knee_push)
        knee = self.knee_for(hip, ankle) + knee_push if moved else self.knee      # at rest: the drawing exactly
        upper = {(x + body[0], y + body[1]): ch for (x, y), ch in self.root.items()}
        upper.update(self.upper.turned(self.hip, self.knee, hip, knee))
        lower = self.lower.turned(self.knee, self.ankle, knee, ankle, keep_rows=True)
        dx, dy = foot_dx, -lift
        foot = {(x + dx, y + dy): ch for (x, y), ch in self.foot.items()}
        if moved:
            upper, lower = _clean(upper, lower, foot)
        return [(upper, "upper"), (lower, "lower"), (foot, "foot")]


def _clean(upper, lower, foot):
    """Ink the turn carried inside the limb (a ring sampled twice, a knee's ink line under the other bone) becomes
    the limb's colour: an ink pixel with three or four of its neighbours the limb's own colour."""
    leg = dict(upper)
    leg.update(lower)
    leg.update(foot)
    fix = {}
    for (x, y), ch in leg.items():
        if ch not in C.INK or (x, y) in foot:
            continue
        nb = [leg.get(n) for n in ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1))]
        fill = [c for c in nb if c is not None and c not in C.INK]
        if len(fill) >= 3:
            fix[(x, y)] = max(sorted(set(fill)), key=fill.count)     # a tie goes the same way every run
    for part in (upper, lower):
        for p, ch in fix.items():
            if p in part:
                part[p] = ch
    return upper, lower


LEG = {leg: Leg(leg) for leg in LEGS}
