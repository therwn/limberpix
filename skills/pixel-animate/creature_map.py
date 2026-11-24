"""A first look at a creature's drawing, from its silhouette alone: which way it faces, where it meets the ground,
its spine, and a guess at its limbs and body plan, with a labelled overlay to look at.

    python creature_map.py <drawing.png> [--eye #rrggbb | --eye-at X,Y] [--floating] [--out DIR] [--name NAME]
    python creature_map.py --selftest
    python creature_map.py --help

A first look only. It sees shapes, not what they are: it reads the selftest's clean shapes, but on real art hidden
far legs, fur, held things, capes and hair defeat a silhouette, and most part names come out wrong. Take its facing,
ground line and spine as a first guess; cut the parts with body_parts.py, from landmarks placed by eye.
--eye-at X,Y (the eye's place in the drawing's pixels) is surer than --eye (its colour, any case, the # optional),
which also finds that colour anywhere else. --floating: it flies, swims or hovers (one drawing cannot show it).

How it reads the silhouette:
1. Silhouette: the drawing's alpha, or every pixel unlike the border's colour. Worked on a copy about 320 px across.
2. Thickness: a chamfer distance transform (3-4 weights): each pixel's distance to the nearest edge. Twice it is
   the body's width there.
3. Skeleton: Zhang-Suen thinning of the silhouette, its spurs shorter than the local width pruned.
4. Spine: the skeleton through the trunk's thick core (width at least 70 % of the widest), out to the eye at the
   front and, at the back, to the skeleton end lying straightest on and heaviest (a tail trails on; a leg drops
   away). Twin forks (two legs under an upright body, a forked tail) are cut back so both are limbs.
5. Head and tail: the spine's end nearer the eye (if one is given) is the head; else the end that is thicker over
   its last fifth. The neck is the narrowest point of the front third, the tail's root where the spine thins under
   half the trunk's width in the back half.
6. Limbs: every skeleton end off the spine is a limb, with the pixels nearest it (a geodesic Voronoi over the
   silhouette). Each is named by where it joins and which way it goes: on the head ears, horns, jaws or tentacles;
   on the tail fins; on the trunk legs (hanging to the ground), wings or sails (long, raised), arms (long, hanging
   free), crests and fins (short). The plan follows from the legs and wings counted.
7. Pivots: a limb's joint is where its branch leaves the spine; its root, where it leaves the trunk's outline
   (the branch point a trunk-width from the joint): a leg is sheared about its root's row, a wing turned about it.
Output: <name>_map.json (all coordinates in the drawing's own pixels) and <name>_map.png (regions tinted, the
skeleton, the spine, joints and labels). Exit code: 0 done, 1 no body found in the drawing, 2 a usage error (a bad
option, a missing file, or a strip of frames: give it one drawing)."""
import json
import math
import os
import sys
import tempfile
from collections import deque

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
except ImportError as e:                                  # python -I does not see a pip install --user
    raise type(e)(f"{e}: {os.path.basename(__file__)} needs numpy and Pillow. python -I (isolated mode) does "
                  "not see packages installed with pip install --user: install them in a virtual "
                  "environment or for the whole system, or run without -I", name=e.name) from None

WORK = 320                                                # the analysis copy's longest side


# ---- silhouette, thickness, skeleton ---------------------------------------------------------------------------
def silhouette(im):
    a = np.asarray(im.convert("RGBA")).astype(int)
    if (a[..., 3] < 250).any():
        return a[..., 3] >= 128
    rgb = a[..., :3]
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, 0)
    return np.abs(rgb - bg).sum(2) > 30


def distance(mask):
    """Chamfer 3-4 distance to the nearest background pixel, in pixels (divided by 3)."""
    h, w = mask.shape
    inf = 10 ** 6
    d = np.where(mask, inf, 0).astype(np.int64)
    d = np.pad(d, 1, constant_values=0)
    for y in range(1, h + 1):                             # forward pass
        row, up = d[y], d[y - 1]
        cand = np.minimum.reduce([up[:-2] + 4, up[1:-1] + 3, up[2:] + 4])
        row[1:-1] = np.minimum(row[1:-1], cand)
        for x in range(1, w + 1):
            if row[x] and row[x - 1] + 3 < row[x]:
                row[x] = row[x - 1] + 3
    for y in range(h, 0, -1):                             # backward pass
        row, dn = d[y], d[y + 1]
        cand = np.minimum.reduce([dn[:-2] + 4, dn[1:-1] + 3, dn[2:] + 4])
        row[1:-1] = np.minimum(row[1:-1], cand)
        for x in range(w, 0, -1):
            if row[x] and row[x + 1] + 3 < row[x]:
                row[x] = row[x + 1] + 3
    return d[1:-1, 1:-1] / 3.0


def skeleton(mask):
    """Zhang-Suen thinning."""
    s = np.pad(mask.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            p2, p3, p4 = s[:-2, 1:-1], s[:-2, 2:], s[1:-1, 2:]
            p5, p6, p7 = s[2:, 2:], s[2:, 1:-1], s[2:, :-2]
            p8, p9 = s[1:-1, :-2], s[:-2, :-2]
            c = s[1:-1, 1:-1]
            nb = [p2, p3, p4, p5, p6, p7, p8, p9]
            b = sum(nb)
            a = sum(((nb[i] == 0) & (nb[(i + 1) % 8] == 1)).astype(np.uint8) for i in range(8))
            if step == 0:
                m = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                m = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            kill = (c == 1) & (b >= 2) & (b <= 6) & (a == 1) & m
            if kill.any():
                c[kill] = 0
                changed = True
        if not changed:
            return s[1:-1, 1:-1].astype(bool)


N8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
RING = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]   # clockwise round a pixel


def _nbrs(sk, x, y):
    h, w = sk.shape
    return [(x + a, y + b) for a, b in N8 if 0 <= x + a < w and 0 <= y + b < h and sk[y + b, x + a]]


def crossings(sk, x, y):
    """How many separate runs of skeleton pixels touch this one (the crossing number): 1 an end, 2 a line, 3 or more
    a junction. Counting neighbours instead calls every diagonal step a junction."""
    h, w = sk.shape
    v = [1 if 0 <= x + a < w and 0 <= y + b < h and sk[y + b, x + a] else 0 for a, b in RING]
    return sum(1 for i in range(8) if v[i] == 0 and v[(i + 1) % 8] == 1) or (1 if sum(v) else 0)


def graph(sk):
    """The skeleton as nodes (ends and junctions) and the paths between them."""
    pts = list(zip(*np.nonzero(sk)))
    node = {(x, y) for y, x in pts if crossings(sk, x, y) != 2}
    if not node and pts:
        node = {(pts[0][1], pts[0][0])}
    edges, seen = [], set()
    for n in node:
        for first in _nbrs(sk, *n):
            if (n, first) in seen:
                continue
            path, prev, cur = [n, first], n, first
            visited = {n, first}
            while cur not in node:
                nxt = [p for p in _nbrs(sk, *cur) if p != prev and p not in visited]
                if not nxt:
                    break
                nxt.sort(key=lambda p: (p not in node, abs(p[0] - cur[0]) + abs(p[1] - cur[1])))
                prev, cur = cur, nxt[0]
                path.append(cur)
                visited.add(cur)                           # a ring with no node on it ends here, not forever
            seen.add((n, first))
            if len(path) > 1:
                seen.add((path[-1], path[-2]))
            edges.append(path)
    return node, edges


def prune(sk, dist, rounds=6):
    """Spurs: end branches shorter than the width where they meet the rest, removed (a bump on an edge, not a limb)."""
    sk = sk.copy()
    for _ in range(rounds):
        node, edges = graph(sk)
        ends = {n for n in node if crossings(sk, *n) == 1}
        cut = False
        for e in edges:
            a, b = e[0], e[-1]
            if (a in ends) == (b in ends):                # not a spur (end to junction)
                continue
            j = b if a in ends else a
            if len(e) < 1.3 * dist[j[1], j[0]] + 3:
                for x, y in e:
                    if (x, y) != j:
                        sk[y, x] = False
                cut = True
        if not cut:
            break
    return skeleton(sk)


# ---- spine, regions ----------------------------------------------------------------------------------------------
def _reach(sk, start, block):
    """Every skeleton pixel reachable from start without crossing block, and the step it was reached from."""
    prev, q = {start: None}, deque([start])
    while q:
        p = q.popleft()
        for r in _nbrs(sk, *p):
            if r not in prev and r not in block:
                prev[r] = p
                q.append(r)
    return prev


def _path_to(prev, end):
    """The skeleton path from _reach's start to end; [end] alone when end was not reached (the skeleton of a small
    or scaled-up pixel drawing can fall apart into pieces, the core's two ends in different ones)."""
    if end not in prev:
        return [end]
    path, p = [], end
    while p is not None:
        path.append(p)
        p = prev[p]
    return path[::-1]


def spine(sk, dist, toward=None):
    """The trunk's axis: the skeleton through the thick core of the body (width at least 70 % of the widest), then
    out of each end of the core: toward the eye on the head's side (when the eye is known), and on the other side to
    the skeleton end that lies furthest along the axis, judged by its reach times the sixth power of how straight on
    it lies, the square of the path's mean width and the square of how straight on the path sets off (a tail trails
    on; a leg drops away, a raised wing turns off). With nothing straight on (cosine under 0.55: a jellyfish's
    bell, a blob) the spine stops at the core. A greedy walk instead ran into ears and wings."""
    pts = [(x, y) for y, x in zip(*np.nonzero(sk))]
    if not pts:
        return []
    top = max(dist[y, x] for x, y in pts)
    core = [p for p in pts if dist[p[1], p[0]] >= 0.7 * top]   # the trunk only (a broad wing root reached 45 %)
    c = np.array(core, float)
    mean = c.mean(0)
    u, sv, vt = np.linalg.svd(c - mean, full_matrices=False)
    long_axis = vt[0]                                     # the core's own long axis
    elongated = len(sv) > 1 and sv[0] > 1.6 * max(sv[1], 1e-6)
    if toward is not None and math.dist(toward, mean) > 0.25 * top:   # the head's way: from the core to the eye
        axis = (np.array(toward, float) - mean) / math.dist(toward, mean)
    else:
        axis = long_axis
    if np.dot(long_axis, axis) < 0:                       # the long axis pointed head-wards
        long_axis = -long_axis
    away = -long_axis - axis                              # away from the head: between the trunk's own length and
    away /= max(1e-6, float(np.hypot(*away)))             # straight back from the eye
    back_end = tuple(map(int, c[int(np.argmax((c - mean) @ away))]))   # the core's ends: furthest that way, and
    front_end = tuple(map(int, c[int(np.argmax((c - mean) @ axis))]))  # nearest the head (a wing's broad root in
                                                          # the core put its end by the long axis up in the wing)
    mid = _path_to(_reach(sk, back_end, set()), front_end) if back_end != front_end else [back_end]
    if mid[0] != back_end:
        mid = [back_end, front_end]
    on = set(mid)

    def extend(start, direction, block):
        """From the core's end out to the skeleton end lying furthest straight on and carrying the trunk's mass:
        reach x cos^6 x (mean width)^2 (a tail continues the trunk; a long thin wing or a leg turns off). The core's
        last stretch, as wide as the core there, may be passed through (a tail often joins a pixel inside it)."""
        near = {p for p in block if math.dist(p, start) <= max(3.0, dist[start[1], start[0]])}
        prev = _reach(sk, start, block - near - {start})
        best, best_score = None, 0.0
        for p in prev:
            if p == start or crossings(sk, *p) != 1 or p in block:
                continue
            v = np.array(p, float) - np.array(start, float)
            L = float(np.hypot(*v))
            cos = float(np.dot(v / max(L, 1e-6), direction))
            if cos < 0.55:                                # well off the way on: a raised wing, a leg
                continue
            path = _path_to(prev, p)
            mass = float(np.mean([dist[y, x] for x, y in path])) ** 2
            lead = path[min(len(path) - 1, max(6, int(dist[start[1], start[0]])))]   # the way it sets off: a tail
            u = np.array(lead, float) - np.array(start, float)          # leaves the core going away; the route to
            set_off = float(np.dot(u / max(1e-6, float(np.hypot(*u))), direction))   # a wing turns back first
            if set_off <= 0:
                continue
            score = L * cos ** 6 * mass * set_off ** 2
            if score > best_score:
                best, best_score = p, score
        return [q for q in _path_to(prev, best)[1:] if q not in block] if best else []

    if toward is not None:                                # the head's side: on to the eye (through the core's last
        near = {p for p in on if math.dist(p, front_end) <= max(3.0, dist[front_end[1], front_end[0]])}   # stretch)
        prev = _reach(sk, front_end, on - near - {front_end})
        target = min(prev, key=lambda p: math.dist(p, toward))
        head = [q for q in _path_to(prev, target)[1:] if q not in on]
    else:
        head = extend(front_end, axis, on)
    tail = extend(back_end, away, on | set(head)) if elongated or toward is not None else []   # along the trunk,
    return tail[::-1] + mid + head                        # away from the head (a raised head tilts the eye's way;
                                                          # a round core, a bell or a blob, has no tail to follow)


def fork_trim(sp, sk, dist, trunk):
    """A spine that ran out along one of a pair (one of two legs under an upright body, one of two tail fins) is cut
    back to the fork, so both are limbs. From each end toward the middle, at every fork (a branch leaving the spine:
    the crossing number misses a T whose arm touches two spine pixels): when the stretch beyond it is thin (under
    60 % of the widest) and another branch leaves there going the same way (cosine over 0.5) about as far (half to
    twice), the two are twins and the spine stops at the fork. A tail beside a hind leg goes another way: kept."""
    on = set(sp)
    widest = float(dist.max())
    for end in (-1, 0):
        seq = sp if end == -1 else sp[::-1]
        for junc in range(len(seq) - 2, len(seq) // 3, -1):
            jx, jy = seq[junc]
            arms = [q for q in _nbrs(sk, jx, jy) if q not in on]
            if not arms:
                continue
            stretch = seq[junc + 1:]
            if np.mean([dist[y, x] for x, y in stretch]) >= 0.6 * widest:
                break                                     # the trunk itself from here on
            ex, ey = stretch[-1]
            reach = math.dist((ex, ey), (jx, jy))
            twin = False
            for start in arms:
                seen, q, far = {start}, deque([start]), (start, 0.0)
                while q:
                    p = q.popleft()
                    d = math.dist(p, (jx, jy))
                    if d > far[1]:
                        far = (p, d)
                    for r in _nbrs(sk, *p):
                        if r not in seen and r not in on:
                            seen.add(r)
                            q.append(r)
                (fx, fy), fd = far
                cos = ((fx - jx) * (ex - jx) + (fy - jy) * (ey - jy)) / max(1e-6, fd * reach)
                if 0.5 * reach <= fd <= 2 * reach and cos > 0.5:
                    twin = True
            if twin:
                seq = seq[:junc + 1]
                sp = seq if end == -1 else seq[::-1]
                on = set(sp)
                break
    return sp


def regions(mask, sk, spine_pts):
    """The limbs and the silhouette's pixels nearest each (a geodesic Voronoi grown over the silhouette): label 0 is
    the trunk. Every skeleton end off the spine is its own limb, traced back to where it leaves its parent: the
    spine, or a fork shared with a sibling (two legs from one hip, the two prongs of an antler); a shared stem
    belongs to the trunk."""
    on = set(spine_pts)
    rest = sk.copy()
    for x, y in on:
        rest[y, x] = False
    branches, n = {}, 0
    seed = np.zeros(mask.shape, int)
    stems = []
    for y, x in zip(*np.nonzero(rest)):
        if seed[y, x] or (x, y) in [q for st in stems for q in st]:
            continue
        comp, q, seen = [], deque([(x, y)]), {(x, y)}
        while q:
            p = q.popleft()
            comp.append(p)
            for r in _nbrs(rest, *p):
                if r not in seen:
                    seen.add(r)
                    q.append(r)
        touching = any((p[0] + a, p[1] + b) in on for p in comp for a, b in N8)
        if not touching:                                  # cut off from the spine by the thinning (an ear on a thin
            sx = np.array(spine_pts, float)               # stalk): one limb, joined where it comes nearest the spine
            near = min(comp, key=lambda p: float(np.min(np.hypot(sx[:, 0] - p[0], sx[:, 1] - p[1]))))
            n += 1
            for px, py in comp:
                seed[py, px] = n
            branches[n] = dict(pixels=sorted(comp, key=lambda p: math.dist(p, near)), joint=near)
            continue
        ends = [p for p in comp if crossings(rest, *p) <= 1 and not any((p[0] + a, p[1] + b) in on for a, b in N8)]
        used = set()
        for e in ends or comp[:1]:
            path, prev, cur = [e], None, e
            while True:                                   # back from the end to a fork or to the spine
                if crossings(rest, *cur) >= 3 and cur != e:
                    break
                touch = next(((cur[0] + a, cur[1] + b) for a, b in N8 if (cur[0] + a, cur[1] + b) in on), None)
                if touch:
                    path.append(touch)
                    break
                nxt = [p for p in _nbrs(rest, *cur) if p != prev and p not in path]
                if not nxt:
                    break
                prev, cur = cur, nxt[0]
                path.append(cur)
            joint = path[-1]
            n += 1
            limb = [p for p in path[:-1] if p not in on]
            used |= set(limb)
            for px, py in limb:
                seed[py, px] = n
            branches[n] = dict(pixels=limb, joint=joint)
        stems.append([p for p in comp if p not in used])
    region = np.full(mask.shape, -1, int)                 # grow every label over the silhouette at once
    q = deque()
    for x, y in list(spine_pts) + [p for st in stems for p in st]:
        region[y, x] = 0
        q.append((x, y))
    for y, x in zip(*np.nonzero(seed)):
        region[y, x] = seed[y, x]
        q.append((x, y))
    h, w = mask.shape
    while q:
        x, y = q.popleft()
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = x + a, y + b
            if 0 <= X < w and 0 <= Y < h and mask[Y, X] and region[Y, X] < 0:
                region[Y, X] = region[y, x]
                q.append((X, Y))
    return region, branches


# ---- outlines ----------------------------------------------------------------------------------------------------
def outline(m):
    """The boundary of a mask's largest piece, traced (Moore neighbourhood), as a closed list of points."""
    ys, xs = np.nonzero(m)
    if not len(xs):
        return []
    i = np.lexsort((xs, ys))[0]
    start = (int(xs[i]), int(ys[i]))
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    h, w = m.shape
    inside = lambda p: 0 <= p[0] < w and 0 <= p[1] < h and m[p[1], p[0]]   # noqa: E731
    pts, cur, d = [start], start, 0
    for _ in range(8 * m.size):
        for k in range(8):
            nd = (d + 6 + k) % 8
            nxt = (cur[0] + dirs[nd][0], cur[1] + dirs[nd][1])
            if inside(nxt):
                cur, d = nxt, nd
                break
        else:
            break
        if cur == start:
            break
        pts.append(cur)
    return pts


def simplify(pts, eps):
    """Ramer-Douglas-Peucker."""
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0], float), np.array(pts[-1], float)
    ab = b - a
    L = np.hypot(*ab) or 1.0
    d = [abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / L for p in pts]   # the 2D cross product's size
    i = int(np.argmax(d))
    if d[i] > eps:
        return simplify(pts[:i + 1], eps)[:-1] + simplify(pts[i:], eps)
    return [pts[0], pts[-1]]


# ---- the map -----------------------------------------------------------------------------------------------------
def analyse(im, eye=None, floating=False, eye_at=None):
    """eye: the eye's colour (#rrggbb), or eye_at: its place (x, y) in the drawing, which is surer when the colour
    is found elsewhere too (a fennec's eye and its flame)."""
    full = silhouette(im)
    H, W = full.shape
    k = max(1, math.ceil(max(H, W) / WORK))
    small_img = Image.fromarray((full * 255).astype(np.uint8)).resize((max(1, W // k), max(1, H // k)), Image.BOX)
    small = np.asarray(small_img) > 127
    if small.sum() < 2:
        raise ValueError("no body found")
    dist = distance(small)
    sk = prune(skeleton(small), dist)
    if not sk.any():                                      # thinning a compact, even-width shape can erase its centre
        sk[np.unravel_index(dist.argmax(), dist.shape)] = True
    eyexy = (eye_at[0] / k, eye_at[1] / k) if eye_at else None   # the eye: the head's end
    if eye and not eyexy:
        rgb = np.asarray(im.convert("RGB")).astype(int)
        e = eye.strip().lstrip("#")
        t = np.array([int(e[0:2], 16), int(e[2:4], 16), int(e[4:6], 16)])
        delta = np.abs(rgb - t).sum(2)
        hit = full & (delta == 0)
        if not hit.any():
            hit = full & (delta < 40)
            if hit.any():
                candidates = set(zip(*np.nonzero(hit)))
                stack = [candidates.pop()]
                while stack:
                    y, x = stack.pop()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            q = (y + dy, x + dx)
                            if q in candidates:
                                candidates.remove(q)
                                stack.append(q)
                if candidates or hit.sum() > full.sum() / 4:
                    raise ValueError(f"eye colour {eye!r} has ambiguous matches; give --eye-at X,Y")
        if hit.any():
            ys, xs = np.nonzero(hit)
            eyexy = (xs.mean() / k, ys.mean() / k)
    sp = spine(sk, dist, eyexy)
    left, top, right, bottom = Image.fromarray(small).getbbox()
    ground = bottom - 1
    n5 = max(2, len(sp) // 5)
    thick = lambda seg: float(np.mean([dist[y, x] for x, y in seg]))   # noqa: E731
    if eyexy:
        head_first = math.dist(sp[0], eyexy) < math.dist(sp[-1], eyexy)
    else:
        head_first = thick(sp[:n5]) >= thick(sp[-n5:])
    if not head_first:
        sp = sp[::-1]
    widths = np.array([dist[y, x] for x, y in sp])
    trunk = float(np.median(widths))
    sp = fork_trim(sp, sk, dist, trunk)                   # an upright body's legs, a forked tail: both limbs
    widths = np.array([dist[y, x] for x, y in sp])
    front = widths[:max(3, len(sp) // 3)]
    neck = int(np.argmin(front[2:])) + 2 if len(front) > 4 else None
    tail_root = None
    for i in range(len(sp) // 2, len(sp)):
        if widths[i] < 0.5 * trunk:
            tail_root = i
            break
    region, branches = regions(small, sk, sp)
    total = int(small.sum())
    index = {p: i for i, p in enumerate(sp)}
    hr = 1.6 * max(1.0, dist[sp[0][1], sp[0][0]])         # spine zones: the head is the blob round the spine's
    head_end = next((i for i, p in enumerate(sp) if math.dist(p, sp[0]) > hr), max(2, len(sp) // 6))   # head end
    tail_start = tail_root if tail_root else len(sp)
    ground_margin = max(2, int(0.03 * max(right - left, bottom - top)))   # independent of canvas padding
    near = max(0, ground - ground_margin)
    cols = (region[near:] == 0).any(0)                    # the trunk touches ground across a fifth of its width
    tx = np.nonzero((region == 0).any(0))[0]
    trunk_on_ground = (not floating and len(tx) and cols.sum() >= 0.2 * (tx.max() - tx.min() + 1))
    parts = []
    for n, b in branches.items():
        m = region == n
        area = int(m.sum())
        if not area or not b["joint"]:
            continue
        jx, jy = b["joint"]
        width = max(1.0, dist[jy, jx])
        pix = sorted(b["pixels"], key=lambda p: math.dist(p, (jx, jy)))
        tip = pix[-1]
        length = math.dist(tip, (jx, jy))
        share = area / total
        if share < 0.004 or length < 0.8 * width + 2:     # a crumb of the outline or a bump, not a part: trunk
            region[m] = 0
            continue
        ys, xs = np.nonzero(m)
        vx, vy = tip[0] - jx, tip[1] - jy
        up, down = vy < -0.35 * length, vy > 0.35 * length
        hangs = vy > 1.2 * abs(vx)                        # straight down, as a leg; a tail trails back instead
        i = index.get(b["joint"])                         # its zone: of the spine point nearest its joint (a
        if i is None:                                     # fork under the body is not on the spine itself)
            i = min(range(len(sp)), key=lambda j: math.dist(sp[j], b["joint"]))
        zone = "head" if i <= head_end else "tail" if i >= tail_start else "trunk"
        touches = ys.max() >= near
        long_ = length > 0.45 * len(sp) or share > 0.08
        if zone == "head":
            kind = ("ear/horn/antenna" if up else "tentacle/beard" if down and long_ else
                    "jaw/tusk/whisker" if not long_ else "head crest/frill")
        elif zone == "tail":
            kind = "tail fin/tuft" if not long_ else "tail branch"
        elif touches and hangs and not trunk_on_ground and not floating:
            kind = "leg"
        elif long_ and up:
            kind = "wing/sail/mane (upper)"
        elif long_ and down and (not touches or floating):
            kind = "arm/tentacle/lifted leg"
        elif long_:
            kind = "wing/fin (side)"
        elif up:
            kind = "back spine/crest"
        elif down:
            kind = "fin/claw (under)"
        else:
            kind = "appendage"
        root = next((p for p in pix if math.dist(p, (jx, jy)) >= dist[jy, jx]), pix[-1])
        poly = simplify(outline(m), 1.5)
        parts.append(dict(kind=kind, zone=zone, area_share=round(share, 3),
                          joint=[int(jx * k), int(jy * k)], root=[int(root[0] * k), int(root[1] * k)],
                          tip=[int(tip[0] * k), int(tip[1] * k)], length=int(length * k),
                          poly=[[int(x * k), int(y * k)] for x, y in poly]))
    counts = {}
    for p in sorted(parts, key=lambda p: p["root"][0]):
        base = p["kind"].split("/")[0].split(" ")[0]
        counts[base] = counts.get(base, 0) + 1
        p["name"] = f"{base}_{counts[base]}"
    legs = [p for p in parts if p["kind"] == "leg"]
    wings = [p for p in parts if p["kind"].startswith("wing")]
    hanging = [p for p in parts if p["kind"].startswith(("arm", "tentacle"))]
    hx, hy = sp[0]
    tx, ty = sp[-1]
    upright = abs(hy - ty) > 1.3 * abs(hx - tx)
    body_len = len(sp)
    slender = body_len > 6 * max(1.0, trunk)
    if len(sp) == 1 and (eyexy is None or eyexy[0] == hx):
        facing = "unknown"
    elif eyexy:
        cx = float(np.mean([p[0] for p in sp]))
        facing = "right" if eyexy[0] > cx else "left"
    else:
        facing = "right" if hx > tx else "left"
    if body_len < 2.2 * max(1.0, trunk) and len(parts) <= 1:
        plan = "blob (slime, golem, egg-like): a body with no limbs to swing"
    elif not legs and trunk_on_ground and slender:
        plan = "serpent or worm (no legs, long body on the ground)"
    elif len(legs) >= 8:
        plan = f"octopod (spider-like, {len(legs)} legs)"
    elif len(legs) >= 6:
        plan = f"hexapod (insect-like, {len(legs)} legs)"
    elif len(legs) >= 4:
        plan = "winged quadruped (dragon, griffin)" if wings else "quadruped"
    elif len(legs) >= 2:
        plan = ("winged biped (standing bird, harpy)" if wings else
                "biped (upright: humanoid, golem, bear)" if upright else "biped (leaning: bird, raptor, kangaroo)")
    elif wings:
        plan = "flier (bird, bat, insect on the wing)"
    elif len(hanging) >= 3:
        plan = "floater with tentacles (jellyfish, eye-beast, octopus)"
    elif not trunk_on_ground and slender:
        plan = "swimmer or flying serpent (fish, eel, sky-dragon)"
    elif not trunk_on_ground:
        plan = "floater (ghost, wisp, orb)"
    else:
        plan = "crawler (slug, snail) or a body on the ground"
    out = dict(size=[W, H], scale=k, facing=facing, plan=plan, upright=upright, ground_y=int(ground * k),
               trunk_width=round(2 * trunk * k, 1),
               spine=[[int(x * k), int(y * k)] for x, y in sp[::max(1, len(sp) // 40)]],
               head=[int(sp[0][0] * k), int(sp[0][1] * k)], tail_tip=[int(sp[-1][0] * k), int(sp[-1][1] * k)],
               neck=[int(sp[neck][0] * k), int(sp[neck][1] * k)] if neck else None,
               tail_root=[int(sp[tail_root][0] * k), int(sp[tail_root][1] * k)] if tail_root else None,
               legless=not legs, parts=parts)
    return out, dict(small=small, region=region, sk=sk, sp=sp, k=k)


COLS = [(230, 90, 90), (90, 200, 120), (90, 140, 230), (230, 190, 70), (190, 100, 220), (80, 210, 210),
        (240, 140, 60), (150, 220, 90), (220, 110, 170), (120, 120, 240)]


def overlay(im, res, aux, path):
    base = im.convert("RGB").copy()
    W, H = base.size
    k = aux["k"]
    tint = np.zeros((aux["small"].shape[0], aux["small"].shape[1], 3), np.uint8)
    for n in np.unique(aux["region"]):
        if n < 0:
            continue
        tint[aux["region"] == n] = (60, 60, 60) if n == 0 else COLS[(n - 1) % len(COLS)]
    t = Image.fromarray(tint).resize((tint.shape[1] * k, tint.shape[0] * k), Image.NEAREST).crop((0, 0, W, H))
    out = Image.blend(base, t.resize((W, H)), 0.45)
    d = ImageDraw.Draw(out)
    for y, x in zip(*np.nonzero(aux["sk"])):
        d.point((x * k, y * k), fill=(255, 255, 255))
    sp = [(x * k, y * k) for x, y in aux["sp"]]
    d.line(sp, fill=(255, 230, 60), width=3)
    for key, col in (("head", (255, 80, 80)), ("tail_tip", (80, 160, 255)), ("neck", (255, 160, 60)),
                     ("tail_root", (80, 220, 220))):
        if res.get(key):
            x, y = res[key]
            d.ellipse((x - 7, y - 7, x + 7, y + 7), outline=col, width=3)
            d.text((x + 9, y - 6), key, fill=col)
    for p in res["parts"]:
        x, y = p["root"]
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 255, 255))
        d.text((x + 7, y), p["name"], fill=(255, 255, 255))
    d.line([(0, res["ground_y"]), (W, res["ground_y"])], fill=(120, 255, 120))
    out.save(path)


def _looks_like_strip(im):
    """A wide sheet with repeated silhouettes at a regular cell pitch, including detached effects."""
    if im.width <= 3 * im.height:
        return False
    mask = silhouette(im)
    occupied = mask.any(axis=0)
    edges = np.diff(np.r_[False, occupied, False].astype(int))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    if len(starts) >= 3 and im.width % len(starts) == 0:
        width = im.width // len(starts)
        cells = np.arange(len(starts))
        if np.array_equal(starts // width, cells) and np.array_equal((ends - 1) // width, cells):
            if mask.reshape(im.height, len(cells), width).all(axis=1).any():
                return True
    # The wolf and bird attacks have effects beside some bodies. Their adjacent cells still share a large body
    # footprint, and their boundaries (unlike slices through a single snake) do not cut connected pixels.
    for width in range(max(2, im.height // 2), min(3 * im.height, im.width // 3) + 1):
        if im.width % width:
            continue
        cells = mask.reshape(im.height, -1, width).transpose(1, 0, 2)
        if np.any(cells[:-1, :, -1] & cells[1:, :, 0]):
            continue
        areas = cells.sum(axis=(1, 2))
        common = (cells[:-1] & cells[1:]).sum(axis=(1, 2))
        if areas.min() > 0 and np.all(2 * common >= np.minimum(areas[:-1], areas[1:])):
            return True
    return False


def main(argv):
    """The command line (see the module's help). Returns the exit code: 0 done, 1 no body found, 2 a usage error."""
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    valued, flags = {"--eye", "--eye-at", "--out", "--name"}, {"--floating"}
    pos, opts, i = [], {}, 0
    try:
        while i < len(argv):
            a = argv[i]
            if a in valued:
                if i + 1 >= len(argv):
                    raise ValueError(f"{a} needs a value")
                opts[a] = argv[i + 1]
                i += 2
            elif a in flags:
                opts[a] = True
                i += 1
            elif a.startswith("-"):
                raise ValueError(f"unknown option {a!r}")
            else:
                pos.append(a)
                i += 1
        if len(pos) != 1:
            raise ValueError("give one drawing" if not pos else f"one drawing only, not {pos}")
        if not os.path.isfile(pos[0]):
            raise ValueError(f"no such file: {pos[0]}")
        eye = opts.get("--eye")
        if eye is not None:
            e = eye.strip().lstrip("#")
            if len(e) != 6 or any(c not in "0123456789abcdefABCDEF" for c in e):
                raise ValueError(f"--eye takes a colour #rrggbb, not {eye!r}")
        at = opts.get("--eye-at")
        try:
            at = tuple(int(round(float(v))) for v in at.split(",")) if at else None
        except (ValueError, OverflowError):
            at = ()
        if at is not None and len(at) != 2:
            raise ValueError(f"--eye-at takes X,Y, not {opts['--eye-at']!r}")
    except ValueError as e:
        print(f"error: {e}  (--help lists the options)", file=sys.stderr)
        return 2
    src = pos[0]
    name = opts.get("--name", os.path.splitext(os.path.basename(src))[0])
    out = os.path.realpath(opts.get("--out", "."))
    filenames = (f"{name}_map.json", f"{name}_map.png")
    try:
        if not name or name in (".", "..") or any(c in '/\\:<>"|?*' or ord(c) < 32 for c in name):
            raise ValueError(f"--name must be a file name, not {name!r}")
        for filename in filenames:
            target = os.path.join(out, filename)
            if os.path.isdir(target):
                raise ValueError(f"output {target} is a directory")
            resolved = os.path.realpath(target)
            if os.path.normcase(os.path.dirname(resolved)) != os.path.normcase(out):
                raise ValueError(f"output {target} resolves outside {out}")
            if (os.path.normcase(resolved) == os.path.normcase(os.path.realpath(src))
                    or os.path.exists(target) and os.path.samefile(target, src)):
                raise ValueError(f"output {target} would overwrite source {src}; choose a different --out or --name")
        with Image.open(src) as image:
            im = image.convert("RGBA")
    except (OSError, ValueError, Image.DecompressionBombError) as e:
        print(f"error: {src}: {e}", file=sys.stderr)
        return 2
    if _looks_like_strip(im):
        print(f"error: {src} is {im.width}x{im.height}: one drawing, not a strip (crop one frame)  "
              "(--help lists the options)", file=sys.stderr)
        return 2
    try:
        res, aux = analyse(im, eye, "--floating" in opts, at)
    except ValueError as e:
        print(f"error: {src}: {e}", file=sys.stderr)
        return 1 if str(e) == "no body found" else 2
    try:
        os.makedirs(out, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=out) as stage:
            with open(os.path.join(stage, filenames[0]), "w", encoding="utf-8") as fh:
                json.dump(res, fh, indent=1)
            overlay(im, res, aux, os.path.join(stage, filenames[1]))
            for filename in filenames:
                os.replace(os.path.join(stage, filename), os.path.join(out, filename))
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(f"{name}: {res['plan']}; facing {res['facing']}, trunk {res['trunk_width']} px")
    for p in res["parts"]:
        print(f"  {p['name']:14s} {p['kind']:28s} {p['zone']:5s} share {p['area_share']:.3f} root {p['root']} "
              f"tip {p['tip']}")
    print("map:", os.path.abspath(os.path.join(out, f"{name}_map.png")))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            import creature_map_selftest
        except ImportError:
            print("error: --selftest needs creature_map_selftest.py beside this file", file=sys.stderr)
            sys.exit(2)
        sys.exit(0 if creature_map_selftest.run() else 1)
    sys.exit(main(sys.argv[1:]))
