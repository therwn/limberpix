"""Cut a drawing into its body parts along its own ink lines and colour edges, from a few landmarks placed by eye.

    python body_parts.py <drawing.png> <landmarks.json> [--out DIR] [--name NAME]
    python body_parts.py <drawing.png> --grid [--step 50] [--out DIR] [--name NAME]   # a labelled grid, to read
    python body_parts.py --selftest                                                    # coordinates off by eye
    python body_parts.py --help

--out defaults to the drawing's folder and is made if missing; --name to the drawing's file name.

Why landmarks: the silhouette alone cannot tell what a shape is. A bow held out and an arm, a quiver and a wing,
hair and a fin, a cape and a tail are the same to a skeleton (creature_map.py shows it: it names a staff's head an
ear). What a part is needs recognising; where it ends can be measured. So the work is split:
- Recognise (by eye, coarse): for each part, a bone, a line of 1-4 points down its middle in the drawing's pixels
  (a shoulder, elbow and hand; the crown and chin; a cape's collar and hem). A rough line is enough: it only has
  to lie inside the part, away from its edges.
- Measure (here, exact): the drawing is split into flat colour patches and its dark ink lines; each part grows
  from its bone over the figure along the cheapest path, and crossing an ink line, a colour edge or a patch
  border costs (a geodesic, seeded segmentation). Parts meet where the drawing draws them apart. Last, a colour
  patch that one part holds most of is given to it whole, so edges follow the drawn ones.

landmarks.json:
    {"parts": {
        "torso":    {"kind": "torso", "bone": [[480, 640], [470, 1000]]},
        "arm_near": {"kind": "arm", "parent": "torso", "bone": [[560, 650], [600, 800], [640, 900]]},
        "bow":      {"kind": "prop", "parent": "arm_near", "bone": [[760, 140], [800, 500], [720, 760]]},
        ...},
     "points": {"eye": [520, 300]}}
kind is free text, copied into the json for your own code (the cut does not read it); common words: head, neck,
torso, pelvis, arm, hand, leg, foot, tail, wing, fin, ear, horn, antenna, jaw, hair, mane, cloth, prop, pack, shell,
tentacle, crest. parent names the part this one hangs from: its pivot is the bone's first point (where it joins the
parent). A null in a bone starts a new piece: use it for a part seen in pieces (a staff above and below the hand
that holds it, a cape on both sides of the legs). Each piece is 1-4 points, e.g.
    "cape": {"kind": "cloth", "bone": [[200, 690], [215, 520], null, [395, 520], [410, 690]]}

Out: <name>_parts.png (each part tinted, its outline, bone and name), <name>_patches.png (the colour patches and ink
the cut follows), <name>_parts.json (per part: kind, parent, pivot, bone, area share, bounding box, label, pieces
and a simplified outline of the largest piece) and <name>_labels.png. To cut a part, select every pixel equal
to its JSON label in the label image. Labels start at 1 in JSON part order, with 0 for the background.
Each part's line gives its kind, area share, pieces and bounding box. "pieces" counts every fragment, however
small; that alone is no fault (a part drawn half behind another often has a few). A "CHECK:" line is printed for a
bone point off the figure, a bone wholly off the figure, a part with no pixels, a part in pieces whose second piece
is 12 px or more and 8 % or more of the part (not for a bone broken by null: those are meant to be in pieces), a part
whose bone ended up in another part's ground (the bone strays over a neighbour), a part mostly of colours not under
its bone, and figure pixels no part reached. Fix those bones and run again.
Exit code: 0 a clean cut (or the grid written), 1 a cut with CHECK lines, 2 a usage error."""
import heapq
import json
import math
import os
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFont

WORK = 420                                                # the analysis copy's longest side
STEP, INK_COST, EDGE_COST, PATCH_COST = 0.3, 16.0, 0.5, 0.5   # a step's cost: STEP + these (going onto or off ink,
                                                          # colour change per Lab unit, a patch border crossed); the
                                                          # step is small so a drawn edge outweighs a long way round
INK_ONLY = 0.9                                            # a bone this much on ink: the part is an ink line
JOINT = 5                                                 # working pixels left unseeded at a joint end of a bone
INK_STEP = 1.2                                            # a step along an ink line
FIT, FIT_TOL, FIT_CAP = 0.05, 8.0, 60.0                  # a part entering a colour unlike its own pays FIT per Lab
                                                          # unit past FIT_TOL (capped): a leg does not flood a cape
SEED_R = 1                                                # bone pixels widened by this (the width of a thin part)
ALIEN = 0.25                                              # a part this share unlike its own colours is flagged
VOTE_MAX = 0.2                                            # ...unless a loser would lose this share of itself
VOTE = 0.7                                                # a colour patch this share one part's goes to it whole
SNAP = 8                                                  # a bone point off the figure moves to it, within this many
                                                          # working pixels (a rough point at the edge of a thin bow)
PALETTE = [(255, 99, 132), (54, 162, 235), (255, 206, 86), (75, 192, 120), (153, 102, 255), (255, 159, 64),
           (0, 200, 200), (240, 80, 220), (160, 220, 60), (230, 120, 90), (120, 160, 255), (250, 240, 120),
           (90, 230, 170), (200, 140, 255), (255, 140, 180), (140, 200, 220), (220, 180, 100), (100, 120, 220)]


# ---- the drawing ------------------------------------------------------------------------------------------------
def silhouette(rgba):
    a = rgba.astype(int)
    if (a[..., 3] < 250).any() and (a[..., 3] > 5).any():
        return a[..., 3] >= 128
    rgb = a[..., :3]
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, 0)
    like = np.abs(rgb - bg).sum(2) <= 30
    # background is only what is like the border colour AND joined to the border: a dark body tone close to the
    # background's (a magpie's black) lies inside the figure's closed outline, so it stays figure
    h, w = like.shape
    out = np.zeros_like(like)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if like[y, x] and not out[y, x]:
                out[y, x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if like[y, x] and not out[y, x]:
                out[y, x] = True
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for X, Y in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= X < w and 0 <= Y < h and like[Y, X] and not out[Y, X]:
                out[Y, X] = True
                q.append((X, Y))
    return ~out


def to_lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    xyz /= np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def load(im):
    """The working copy: its scale k (drawing px per working px), the figure mask, Lab colours."""
    rgba = np.asarray(im.convert("RGBA"))
    full = silhouette(rgba)
    H, W = full.shape
    k = max(1.0, max(H, W) / WORK)
    w, h = max(1, round(W / k)), max(1, round(H / k))
    rgb = np.asarray(Image.fromarray(rgba[..., :3]).resize((w, h), Image.BOX)).astype(float)
    mask = np.asarray(Image.fromarray((full * 255).astype(np.uint8)).resize((w, h), Image.BOX)) > 127
    return k, mask, to_lab(rgb), full


def ink_lines(lab, mask):
    """The drawing's dark outlines: pixels much darker than the figure's own tones (a fifth of the median
    lightness, or under L 18) that are darker than what is round them."""
    L = lab[..., 0]
    med = float(np.median(L[mask])) if mask.any() else 50.0
    pad = np.pad(L, 2, mode="edge")
    h, w = L.shape
    local = np.max([pad[2 + dy:2 + dy + h, 2 + dx:2 + dx + w] for dy in (-2, 0, 2) for dx in (-2, 0, 2)], 0)
    return mask & ((L < min(18.0, 0.4 * med)) | ((L < 0.45 * med) & (local - L > 18)))


def patches(lab, mask, ink, n=22, iters=8):
    """Flat colour patches: the figure's colours clustered (k-means in Lab, n clusters), and each cluster cut into
    4-connected pieces; ink is its own label (-2). Tiny pieces (under 4 px) go to the neighbour closest in colour."""
    h, w = mask.shape
    pts = lab[mask & ~ink]
    if len(pts) == 0:
        return np.full(mask.shape, -1), np.zeros((0, 3))
    rng = np.random.default_rng(7)
    cent = pts[rng.choice(len(pts), min(n, len(pts)), replace=False)]
    for _ in range(iters):
        lab_of = np.argmin(((pts[:, None, :] - cent[None]) ** 2).sum(2), 1)
        for i in range(len(cent)):
            if (lab_of == i).any():
                cent[i] = pts[lab_of == i].mean(0)
    cl = np.full(mask.shape, -1)
    cl[mask & ~ink] = np.argmin(((lab[mask & ~ink][:, None, :] - cent[None]) ** 2).sum(2), 1)
    cl[ink] = -2
    patch = np.full(mask.shape, -1)
    n_p = 0
    for y in range(h):
        for x in range(w):
            if cl[y, x] < 0 or patch[y, x] >= 0:
                continue
            q, patch[y, x] = deque([(x, y)]), n_p
            while q:
                a, b = q.popleft()
                for X, Y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= X < w and 0 <= Y < h and patch[Y, X] < 0 and cl[Y, X] == cl[y, x]:
                        patch[Y, X] = n_p
                        q.append((X, Y))
            n_p += 1
    size = np.bincount(patch[patch >= 0], minlength=n_p)
    mean = np.zeros((n_p, 3))
    for c in range(3):
        mean[:, c] = np.bincount(patch[patch >= 0], weights=lab[..., c][patch >= 0], minlength=n_p) / np.maximum(size, 1)
    for _ in range(3):                                    # tiny pieces join their closest neighbour
        for y, x in zip(*np.nonzero(patch >= 0)):
            p = patch[y, x]
            if size[p] >= 4:
                continue
            nb = [patch[Y, X] for X, Y in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                  if 0 <= X < w and 0 <= Y < h and patch[Y, X] >= 0 and patch[Y, X] != p]
            if nb:
                best = min(nb, key=lambda o: ((mean[o] - mean[p]) ** 2).sum())
                patch[patch == p] = best
                size[best] += size[p]
                size[p] = 0
    patch[ink] = -2
    return patch, mean


# ---- the cut ----------------------------------------------------------------------------------------------------
def snap(mask, x, y):
    """The figure pixel nearest (x, y) within SNAP working pixels, or the point itself."""
    h, w = mask.shape
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < w and 0 <= yi < h and mask[yi, xi]:
        return x, y
    best = None
    for dy in range(-SNAP, SNAP + 1):
        for dx in range(-SNAP, SNAP + 1):
            X, Y = xi + dx, yi + dy
            if 0 <= X < w and 0 <= Y < h and mask[Y, X] and (best is None or dx * dx + dy * dy < best[0]):
                best = (dx * dx + dy * dy, X, Y)
    return (best[1], best[2]) if best else (x, y)


def _bone_pixels(bone, k, mask, trim, trim_end=True, widen=None):
    """The working pixels along a bone, its ends trimmed (a joint is where two parts meet: not a sure seed). A null
    in the bone breaks it: the line jumps (a staff passing behind the hand that holds it)."""
    if any(p is None for p in bone):
        out, run = [], []
        for p in bone + [None]:
            if p is None:
                if run:
                    out += _bone_pixels(run, k, mask, trim, trim_end, widen)
                run = []
            else:
                run.append(p)
        return list(dict.fromkeys(out))
    pts = [snap(mask, x / k, y / k) for x, y in bone]
    out = []
    if len(pts) == 1:                                     # a point: just it (widened below like any bone)
        x, y = pts[0]
        out.append((int(round(x)), int(round(y))))
    else:
        L = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
        n = max(2, int(L * 2))
        acc = 0.0
        segs = list(zip(pts, pts[1:]))
        for i in range(n + 1):
            d = L * i / n
            cut_at = min(trim * L, JOINT)
            if L > 0 and (d < cut_at or (trim_end and d > L - cut_at)):
                continue
            acc = 0.0
            for a, b in segs:
                s = math.dist(a, b)
                if d <= acc + s or (a, b) == segs[-1]:
                    t = (d - acc) / s if s else 0
                    out.append((int(round(a[0] + t * (b[0] - a[0]))), int(round(a[1] + t * (b[1] - a[1])))))
                    break
                acc += s
    h, w = mask.shape
    r = SEED_R if widen is None else widen
    wide = [(x + a, y + b) for x, y in out for a in range(-r, r + 1) for b in range(-r, r + 1)]
    return [(x, y) for x, y in dict.fromkeys(wide) if 0 <= x < w and 0 <= y < h and mask[y, x]]


def palette(lab, px, ink, tol=12.0, most=8):
    """A part's own colours: the Lab colours under its bone, gathered greedily (a new one when more than tol from
    every one so far), at most `most`."""
    cs = []
    for x, y in px:
        if ink[y, x]:
            continue
        c = lab[y, x]
        if all(np.sqrt(((c - o) ** 2).sum()) > tol for o in cs):
            cs.append(c)
            if len(cs) >= most:
                break
    return np.array(cs)


def cut(lab, mask, ink, patch, seeds, cores=None):
    """Every figure pixel to the part it is cheapest to reach from (multi-source Dijkstra). cores: each bone's own
    line, unwidened, which tells a part drawn in ink alone (its line lies on ink)."""
    h, w = mask.shape
    label = np.full(mask.shape, -1)
    cost = np.full(mask.shape, np.inf)
    heap = []
    ink_only = []
    for i, px in enumerate(seeds):
        core = cores[i] if cores else px
        on_ink = sum(ink[y, x] for x, y in core) >= INK_ONLY * max(1, len(core))   # drawn in ink alone (a string;
                                                          # not dark cloth, whose bone is only partly on ink-dark)
        ink_only.append(on_ink)                           # grows along ink only, never into a neighbour's colour
        for x, y in px:
            if (on_ink or not ink[y, x]) and cost[y, x] > 0:
                cost[y, x], label[y, x] = 0.0, i
                heap.append((0.0, x, y, i))
    pal = [palette(lab, px, ink) for px in seeds]
    fit = np.zeros((len(seeds),) + mask.shape)            # each part's cost of each pixel's colour
    for i, cs in enumerate(pal):
        if len(cs) and not ink_only[i]:
            d = np.min(np.sqrt(((lab[:, :, None, :] - cs[None, None]) ** 2).sum(-1)), -1)
            fit[i] = FIT * np.clip(d - FIT_TOL, 0, FIT_CAP)
    heapq.heapify(heap)
    while heap:
        c, x, y, i = heapq.heappop(heap)
        if c > cost[y, x]:
            continue
        for X, Y, step in ((x + 1, y, STEP), (x - 1, y, STEP), (x, y + 1, STEP), (x, y - 1, STEP)):
            if not (0 <= X < w and 0 <= Y < h and mask[Y, X]) or (ink_only[i] and not ink[Y, X]):
                continue
            if ink[Y, X] and ink[y, x]:
                step = INK_STEP                           # an outline is no road: running along it costs
            d = step + EDGE_COST * float(np.sqrt(((lab[Y, X] - lab[y, x]) ** 2).sum()))
            if ink[Y, X] != ink[y, x]:
                d += INK_COST
            if not ink[Y, X]:
                d += fit[i, Y, X]
            if patch[Y, X] != patch[y, x] and patch[Y, X] >= 0 and patch[y, x] >= 0:
                d += PATCH_COST
            if c + d < cost[Y, X]:
                cost[Y, X], label[Y, X] = c + d, i
                heapq.heappush(heap, (c + d, X, Y, i))
    seeded = label.copy()
    area = np.bincount(label[label >= 0], minlength=len(seeds))
    for p in np.unique(patch[patch >= 0]):                # a patch mostly one part's goes to it whole, unless that
        sel = patch == p                                  # takes a real share of another part (one colour running on
        votes = np.bincount(label[sel][label[sel] >= 0], minlength=len(seeds))   # from body into tail)
        if not votes.sum() or votes.max() < VOTE * votes.sum():
            continue
        win = int(np.argmax(votes))
        if all(votes[j] <= VOTE_MAX * area[j] for j in range(len(seeds)) if j != win):
            label[sel] = win
    for i, px in enumerate(seeds):                        # a part's own bone stays its own
        for x, y in px:
            if seeded[y, x] == i and cost[y, x] == 0:
                label[y, x] = i
    for _ in range(2):                                    # outline ink takes the label most round it
        for y, x in zip(*np.nonzero(ink)):
            if label[y, x] >= 0 and ink_only[label[y, x]]:
                continue
            nb = [label[Y, X] for X, Y in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                  if 0 <= X < w and 0 <= Y < h and label[Y, X] >= 0 and not ink[Y, X]]
            if nb:
                label[y, x] = max(set(nb), key=nb.count)
    return label


def adopt(label, mask):
    """Figure pixels no part reached (a spark, an ember, a loose drop apart from the body): each goes to the part
    nearest it (a breadth-first grow over the whole frame). Returns how many there were."""
    lost = (label < 0) & mask
    n = int(lost.sum())
    if not n:
        return 0
    h, w = mask.shape
    near = label.copy()
    q = deque((x, y) for y, x in zip(*np.nonzero(label >= 0)))
    while q:
        x, y = q.popleft()
        for X, Y in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= X < w and 0 <= Y < h and near[Y, X] < 0:
                near[Y, X] = near[y, x]
                q.append((X, Y))
    label[lost] = near[lost]
    return n


def pieces(sel):
    h, w = sel.shape
    seen = np.zeros(sel.shape, bool)
    out = []
    for y, x in zip(*np.nonzero(sel)):
        if seen[y, x]:
            continue
        q, comp = deque([(x, y)]), []
        seen[y, x] = True
        while q:
            a, b = q.popleft()
            comp.append((a, b))
            for X, Y in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                if 0 <= X < w and 0 <= Y < h and sel[Y, X] and not seen[Y, X]:
                    seen[Y, X] = True
                    q.append((X, Y))
        out.append(comp)
    return sorted(out, key=len, reverse=True)


def outline(sel):
    """The boundary of the mask's largest piece (Moore tracing), closed list of (x, y)."""
    ps = pieces(sel)
    if not ps:
        return []
    m = np.zeros(sel.shape, bool)
    for x, y in ps[0]:
        m[y, x] = True
    m = np.pad(m, 1)
    ys, xs = np.nonzero(m)
    start = (xs[np.argmin(ys * 10 ** 6 + xs)], ys.min())
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    out, cur, back = [start], start, 4
    for _ in range(8 * m.sum() + 8):
        for i in range(8):
            d = (back + 1 + i) % 8
            nx, ny = cur[0] + dirs[d][0], cur[1] + dirs[d][1]
            if m[ny, nx]:
                cur, back = (nx, ny), (d + 4) % 8
                break
        else:
            break
        if cur == start:
            break
        out.append(cur)
    return [(x - 1, y - 1) for x, y in out]


def simplify(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0], float), np.array(pts[-1], float)
    ab = b - a
    n = np.hypot(*ab)
    d = [abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / n if n else math.dist(p, pts[0]) for p in pts]
    i = int(np.argmax(d))
    if d[i] > eps:
        return simplify(pts[:i + 1], eps)[:-1] + simplify(pts[i:], eps)
    return [pts[0], pts[-1]]


def analyse(im, marks):
    k, mask, lab, full = load(im)
    ink = ink_lines(lab, mask)
    patch, _ = patches(lab, mask, ink)
    names = list(marks["parts"])
    trims = [0.0 if len(marks["parts"][n]["bone"]) == 1 else 0.12 for n in names]
    parents = {marks["parts"][n].get("parent") for n in names}
    # the start of a bone is a joint, not a sure seed; its end too when another part hangs from this one
    seeds = [_bone_pixels(marks["parts"][n]["bone"], k, mask, t, n in parents) for n, t in zip(names, trims)]
    cores = [_bone_pixels(marks["parts"][n]["bone"], k, mask, t, n in parents, 0) for n, t in zip(names, trims)]
    label = cut(lab, mask, ink, patch, seeds, cores)
    pal = [palette(lab, px, ink) for px in seeds]
    total = int(mask.sum())
    loose = adopt(label, mask)
    aux = dict(k=k, mask=mask, ink=ink, patch=patch, label=label, names=names, full=full)
    labels_full = full_labels(aux, im.size)
    aux["labels_full"] = labels_full
    parts, warn = [], []
    for i, n in enumerate(names):
        spec = marks["parts"][n]
        bone = [p for p in spec["bone"] if p is not None]
        sel = label == i
        ps = pieces(sel)
        area = int(sel.sum())
        def on_fig(p):
            x, y = snap(mask, p[0] / k, p[1] / k)
            X, Y = int(round(x)), int(round(y))
            return 0 <= Y < mask.shape[0] and 0 <= X < mask.shape[1] and mask[Y, X]
        off = [p for p in bone if not on_fig(p)]
        if off:
            warn.append(f"{n}: bone point(s) off the figure {off}")
        if not seeds[i]:
            warn.append(f"{n}: its bone lies wholly off the figure")
        if not area:
            warn.append(f"{n}: no pixels")
        elif len(ps) > 1 and len(ps[1]) >= max(12, 0.08 * area) and None not in spec["bone"]:
            warn.append(f"{n}: in {len(ps)} pieces (second {len(ps[1])} px of {area}): a neighbour's bone may cut it")
        stolen = [s for s in seeds[i] if label[s[1], s[0]] != i]
        if seeds[i] and len(stolen) > 0.3 * len(seeds[i]):
            other = names[int(np.bincount([label[s[1], s[0]] for s in stolen if label[s[1], s[0]] >= 0]
                                          or [i]).argmax())]
            warn.append(f"{n}: {len(stolen)} of {len(seeds[i])} bone pixels ended in {other}: the bone strays")
        if area and len(pal[i]):                          # much of it unlike every colour under its bone
            cd = np.min(np.sqrt(((lab[sel & ~ink][:, None, :] - pal[i][None]) ** 2).sum(-1)), -1)
            alien = float((cd > FIT_TOL + 25).mean()) if len(cd) else 0.0
            if alien > ALIEN:
                warn.append(f"{n}: {alien:.0%} of it is a colour not under its bone: a piece of another part seen "
                            "apart (a cape either side of a leg) may lack a bone, or this bone misses a colour")
        poly = [(int(x * k), int(y * k)) for x, y in simplify(outline(sel), 1.2)] if area else []
        bbox = Image.fromarray(labels_full == i).getbbox()
        parts.append(dict(name=n, label=i + 1, kind=spec.get("kind", n), parent=spec.get("parent"),
                          pivot=bone[0], bone=spec["bone"], area_share=round(area / max(1, total), 4), pieces=len(ps),
                          bbox=list(bbox) if bbox else None, poly=poly))
    if loose > 0.02 * total:
        warn.append(f"{loose} figure pixels reached by no part, given to the nearest: a piece apart from the body "
                    "with no bone in it (give it one if it is a part of its own)")
    return dict(size=[im.width, im.height], k=round(k, 3), parts=parts, warnings=warn, points=marks.get("points", {})), aux


# ---- drawing the result -----------------------------------------------------------------------------------------
FONTS = ("segoeuib.ttf", "arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf")


def _font(size, names=FONTS):
    """A bold system font at this size; else Pillow's own font at this size (Pillow 10.1+), else its small bitmap."""
    for f in names:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:                                     # Pillow before 10.1: no sized default
        return ImageFont.load_default()


def full_labels(aux, size):
    """The labels at the drawing's own size, every figure pixel owned: the working copy's labels scaled up, then
    figure pixels the small copy lost (thin dark shading, gaps between feathers) given to the nearest label by
    growing the labels a pixel at a time inside the figure. -1 off the figure."""
    W, H = size
    lab = np.asarray(Image.fromarray(aux["label"].astype(np.int32) + 1).resize((W, H), Image.NEAREST)).astype(int) - 1
    fig = aux["full"]
    lab[~fig] = -1
    missing = fig & (lab < 0)
    if not missing.any():
        return lab
    near = np.pad(missing, 1)
    border = near[1:-1, :-2] | near[1:-1, 2:] | near[:-2, 1:-1] | near[2:, 1:-1]
    frontier = deque(zip(*np.nonzero(border & (lab >= 0))))
    while frontier:
        y, x = frontier.popleft()
        for Y, X in ((y, x - 1), (y, x + 1), (y - 1, x), (y + 1, x)):
            if 0 <= X < W and 0 <= Y < H and fig[Y, X] and lab[Y, X] < 0:
                lab[Y, X] = lab[y, x]
                frontier.append((Y, X))
    adopt(lab, fig)                                       # detached details too small to survive the working copy
    return lab


def draw(im, res, aux, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    k, label, mask = aux["k"], aux["label"], aux["mask"]
    W, H = im.size
    flab = aux["labels_full"] if "labels_full" in aux else full_labels(aux, (W, H))
    col = np.zeros((H, W, 4), np.uint8)
    for i in range(len(aux["names"])):
        col[flab == i] = PALETTE[i % len(PALETTE)] + (120,)
    tint = Image.fromarray(col)
    base = im.convert("RGBA")
    over = Image.alpha_composite(base, tint)
    d = ImageDraw.Draw(over)
    f = _font(max(14, W // 60))
    for i, p in enumerate(res["parts"]):
        c = PALETTE[i % len(PALETTE)]
        if p["poly"]:
            d.line(p["poly"] + p["poly"][:1], fill=c + (255,), width=max(2, W // 400))
        run = []
        for q in p["bone"] + [None]:
            if q is None:
                if len(run) > 1:
                    d.line(run, fill=(255, 255, 255, 255), width=max(2, W // 350))
                run = []
            else:
                run.append(tuple(q))
        for q in [q for q in p["bone"] if q is not None]:
            r = max(4, W // 220)
            d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=c + (255,), outline=(0, 0, 0, 255), width=2)
        pts = [q for q in p["bone"] if q is not None]
        x, y = pts[len(pts) // 2]
        d.text((x + 8, y - 8), p["name"], fill=c + (255,), font=f, stroke_width=3, stroke_fill=(0, 0, 0, 255))
    over.save(os.path.join(out_dir, f"{name}_parts.png"))
    pa = aux["patch"]
    rng = np.random.default_rng(3)
    pc = rng.integers(60, 255, (int(pa.max()) + 2, 3), dtype=np.uint8) if pa.max() >= 0 else np.zeros((1, 3), np.uint8)
    pimg = np.zeros(pa.shape + (3,), np.uint8)
    pimg[pa >= 0] = pc[pa[pa >= 0]]
    pimg[pa == -2] = (0, 0, 0)
    pimg[~mask] = (40, 34, 46)
    Image.fromarray(pimg).resize((W, H), Image.NEAREST).save(os.path.join(out_dir, f"{name}_patches.png"))
    label_type = np.uint8 if len(res["parts"]) <= 255 else np.uint16
    Image.fromarray((flab + 1).astype(label_type)).save(os.path.join(out_dir, f"{name}_labels.png"))
    with open(os.path.join(out_dir, f"{name}_parts.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)


def grid(im, path, step=50):
    """A copy of the drawing with a labelled grid, for reading landmark coordinates by eye."""
    g = im.convert("RGBA")
    d = ImageDraw.Draw(g)
    f = _font(max(11, step // 4))
    W, H = g.size
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=(0, 255, 255, 110 if x % (2 * step) else 200), width=1)
        if x % (2 * step) == 0:
            for y0 in range(0, H, 4 * step):
                d.text((x + 2, y0 + 2), str(x), fill=(0, 255, 255, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0))
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=(255, 255, 0, 110 if y % (2 * step) else 200), width=1)
        if y % (2 * step) == 0:
            for x0 in range(0, W, 4 * step):
                d.text((x0 + 2, y + 2), str(y), fill=(255, 255, 0, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0))
    g.save(path)


def main(argv):
    """The command line (see the module's help). Returns the exit code: 0 a clean cut or the grid, 1 CHECK lines,
    2 a usage error."""
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    if "--selftest" in argv:
        try:
            import body_parts_selftest
        except ImportError:
            print("error: --selftest needs body_parts_selftest.py beside this file", file=sys.stderr)
            return 2
        return 0 if body_parts_selftest.run() else 1
    valued, flags = {"--out", "--name", "--step"}, {"--grid"}
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
        grid_only = "--grid" in opts
        if not pos:
            raise ValueError("no drawing given")
        if len(pos) != (1 if grid_only else 2):
            raise ValueError("give a drawing and --grid" if grid_only else "give a drawing and its landmarks.json")
        for p in pos:
            if not os.path.isfile(p):
                raise ValueError(f"no such file: {p}")
        step = opts.get("--step", "50")
        if not step.isdigit() or int(step) <= 0:
            raise ValueError(f"--step must be a whole number over 0, not {step!r}")
    except ValueError as e:
        print(f"error: {e}  (--help lists the options)", file=sys.stderr)
        return 2
    src = pos[0]
    im = Image.open(src)
    name = opts.get("--name", os.path.splitext(os.path.basename(src))[0])
    out = opts.get("--out", os.path.dirname(os.path.abspath(src)))
    os.makedirs(out, exist_ok=True)
    if grid_only:
        p = os.path.join(out, f"{name}_grid.png")
        grid(im, p, int(step))
        print(p)
        return 0
    try:
        with open(pos[1], encoding="utf-8") as fh:
            marks = json.load(fh)
        if not isinstance(marks, dict) or not isinstance(marks.get("parts"), dict) or not marks["parts"]:
            raise ValueError('no "parts" in it')
    except ValueError as e:
        print(f"error: {pos[1]}: not a landmarks file ({e})", file=sys.stderr)
        return 2
    res, aux = analyse(im, marks)
    draw(im, res, aux, out, name)
    for p in res["parts"]:
        print(f"{p['name']:14s} {p['kind']:10s} share {p['area_share']:.3f} pieces {p['pieces']} bbox {p['bbox']}")
    for w in res["warnings"]:
        print("CHECK:", w)
    return 1 if res["warnings"] else 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))
