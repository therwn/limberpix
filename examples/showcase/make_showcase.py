"""Build the README's three pictures from the showcase creatures, with the repo's own tools.

    python examples/showcase/make_showcase.py            # writes docs/img/hero.gif, check.png, parts.png
    python examples/showcase/make_showcase.py --out DIR  # writes them to DIR instead

  hero.gif    the bird, the beast and the lizard on one ground strip: their idle loops, then their move loops,
              each at its own length, 30 fps (every pose held 2 frames), scaled 4x.
  check.png   pixel_anim_check run on the beast's walk twice: once with the eye lost on one pose (painted over,
              as when a head moves without its eye), once as it is. The lines shown are the check's own.
  parts.png   body_parts.py run on the beast's drawing (beast/beast_art_8x.png) with the bones in beast/marks.json;
              the labels it cut, drawn large.

It first checks that every creature's loops pass pixel_anim_check with 0 faults, and stops if one does not. It reads
the strips as they are on disk (run a creature's animate.py first to rebuild them). Needs Python 3.8+, numpy and
Pillow 10.1+ (its bundled Aileron font sets the captions; the terminal text is pixfont.py, the pixel font beside
this script)."""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "skills", "pixel-anim-check"))
sys.path.insert(0, os.path.join(ROOT, "skills", "pixel-animate"))
import body_parts as bp                                   # noqa: E402
import pixel_anim_check as pac                            # noqa: E402
import pixfont                                            # noqa: E402

# what pixel_anim_check is told of each creature (the same options as in each animate.py's docstring)
CREATURES = {
    "bird": dict(frame=50, eye="#120c1c", ink=("#1b1424", "#2b4180", "#8c3a2e"), flier=True,
                 shadow=("#3a3348", "#544b63")),
    "beast": dict(frame=52, eye="#3ad3a0", ink=("#2a1a2c", "#6b3343")),
    "lizard": dict(frame=72, eye="#f6c544", ink=("#1b1826", "#2c4438"), effects=("#e0517a",)),
}

# the pictures' colours
BG = (22, 19, 30)
PANEL = (32, 28, 43)
TILE = (63, 56, 80)
TEXT = (238, 230, 216)
MUTED = (148, 139, 166)
RED = (242, 88, 92)
GREEN = (98, 210, 144)
TERM = (13, 11, 19)


# ---- reading the creatures ----------------------------------------------------------------------------------------
def spec(key):
    c = CREATURES[key]
    return pac.Spec(eye=c["eye"], ink=set(c["ink"]), flier=c.get("flier", False), shadow=c.get("shadow", ()),
                    effects=c.get("effects", ()))


def loops(key):
    return {a: pac.load(os.path.join(HERE, key, f"{key}_{a}.png"), frame=CREATURES[key]["frame"])
            for a in ("idle", "move")}


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


def font(size):
    """Pillow's own bundled font (Aileron) at this size, so the captions come out alike on every machine."""
    try:
        f = ImageFont.load_default(size=size)
    except TypeError:                                     # Pillow before 10.1: no sized default
        f = None
    if not isinstance(f, ImageFont.FreeTypeFont):
        sys.exit(f"make_showcase needs Pillow 10.1+ built with FreeType for its bundled font (this is "
                 f"{Image.__version__})")
    return f


def card(w, h, radius=28):
    """The picture's ground: a dark rounded card, transparent outside, so it sits on a light or a dark page."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=BG + (255,))
    return im


# ---- hero.gif -----------------------------------------------------------------------------------------------------
def hero(path, order=("beast", "bird", "lizard"), S=4):
    """The three creatures on one ground strip: their idles together, then their moves, each loop repeated to a
    common length (144 and 160 frames at 30 fps), the 1x scene scaled S times."""
    L = {k: {a: [rgba(f) for f in v] for a, v in loops(k).items()} for k in order}
    boxes = {}
    for k in order:
        alpha = np.any([f[..., 3] > 0 for a in L[k] for f in L[k][a]], 0)
        ys, xs = np.nonzero(alpha)
        boxes[k] = (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1)
    margin, gap, top, below = 8, 9, 16, 7
    tall = max(b[3] - b[2] for b in boxes.values())
    G = top + tall - 2                                    # the ground's first row: a walker's paws stand on it, a
    W1 = 2 * margin + sum(b[1] - b[0] for b in boxes.values()) + gap * (len(order) - 1)   # flier's shadow lies on
    H1 = G + below + 1                                    # it and the row below
    scene = np.zeros((H1, W1, 3), np.uint8)
    sky = [(21, 18, 30), (26, 22, 37), (31, 26, 44), (37, 31, 52)]   # dusk in flat bands, a dithered row between
    cuts = [int(G * f) for f in (0.3, 0.55, 0.8)]
    for y in range(G):
        band = sum(y >= c for c in cuts)
        scene[y] = sky[band]
        if y + 1 in cuts:
            scene[y, y % 2::2] = sky[band + 1]
    ground = [(122, 108, 136), (98, 86, 114), (80, 69, 96)]   # the lit edge, the near ground, the far ground
    scene[G] = ground[0]
    scene[G + 1:G + 4] = ground[1]
    scene[G + 3, 1::2] = ground[2]
    scene[G + 4:] = ground[2]
    rng = np.random.default_rng(7)
    for _ in range(14):                                   # a few dim stars
        scene[rng.integers(2, int(G * 0.6)), rng.integers(2, W1 - 2)] = (64, 56, 86)
    for _ in range(W1 // 6):                              # pebbles
        x, y = rng.integers(1, W1 - 2), rng.integers(G + 2, H1 - 1)
        scene[y, x:x + int(rng.integers(1, 3))] = (112, 99, 128) if y < G + 3 else (92, 80, 108)
    places, x = {}, margin
    for k in order:
        x0, x1, y0, y1 = boxes[k]
        foot = G + (1 if CREATURES[k].get("flier") else 0)
        places[k] = (x - x0, foot - (y1 - 1))
        x += x1 - x0 + gap

    def lengths(a):
        n = 1
        for k in order:
            n = np.lcm(n, len(L[k][a]))
        return int(n)

    timeline = [("idle", t) for t in range(lengths("idle"))] + [("move", t) for t in range(lengths("move"))]
    frames = []
    for a, t in timeline:
        f = scene.copy()
        for k in order:
            paste(f, L[k][a][t % len(L[k][a])], *places[k])
        frames.append(f)
    labels = {}
    for a in ("idle", "move"):                            # "idle  move", the loop playing lit, on the 1x grid
        im = Image.new("RGB", (pixfont.width("idle  move"), 9), tuple(int(v) for v in scene[5, margin]))
        for word, x in (("idle", 0), ("move", pixfont.width("idle  ") + 1)):
            pixfont.draw(im, x, 0, word, (232, 214, 170) if word == a else (72, 64, 94))
        labels[a] = np.asarray(im)
    for (a, _), f in zip(timeline, frames):
        f[5:14, margin:margin + labels[a].shape[1]] = labels[a]
    # one palette for the whole GIF; a pose held over several frames is written once, with their whole time,
    # each image's start and end put on the 10 ms grid a GIF stores (poses held 2 frames at 30 fps: 70, 60, 70 ms)
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
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durations, loop=0, optimize=False,
                disposal=1)
    return ims[0].size, len(ims)


# ---- check.png ----------------------------------------------------------------------------------------------------
LOST = (6, 7)                                             # the beast's move frames whose eye is painted over


def poses(frames):
    """[first frame, last frame, the pose] for each run of identical frames."""
    out = []
    for k, f in enumerate(frames):
        if out and f == out[-1][2]:
            out[-1][1] = k
        else:
            out.append([k, k, f])
    return out


def lose_eye(frame, eye, glint):
    """The frame with its eye and glint painted the fur's colour beside them, as when the head moves on without
    its eye."""
    f = [list(r) for r in frame]
    for y, r in enumerate(frame):
        for x, v in enumerate(r):
            if v in (eye, glint):
                f[y][x] = next(r[i] for i in range(x - 1, -1, -1) if r[i] not in (eye, glint))
    return f


def terminal(lines, w, scale=3, pad=24, pitch=36):
    """A terminal panel: lines of [(text, colour), ...] runs in the pixel font, and an exit code at the right."""
    h = 2 * pad + pitch * (len(lines) - 1) + 7 * scale
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), 14, fill=TERM + (255,), outline=(52, 46, 68), width=2)
    for i, runs in enumerate(lines):
        x = pad
        for text, col in runs:
            if text.startswith(">"):                      # right-aligned
                text = text[1:]
                x = w - pad - pixfont.width(text, scale)
            pixfont.draw(im, x, pad + i * pitch, text, col, scale)
            x += len(text) * pixfont.CELL_W * scale
    return im


def check_png(path, S=5):
    """The beast's walk, four poses round the fault, broken and as drawn, each with what the check printed."""
    key, c = "beast", CREATURES["beast"]
    L = loops(key)
    glint = "#f4fff2"
    broken = dict(L, move=[lose_eye(f, c["eye"], glint) if k in LOST else f for k, f in enumerate(L["move"])])
    sp = spec(key)
    runs = {"broken": (broken, pac.check(broken, sp)), "fixed": (L, pac.check(L, sp))}
    if runs["fixed"][1] or [ln.split(":")[0] for ln in runs["broken"][1]] != ["eye", "eye"]:
        sys.exit(f"check: unexpected faults {runs}")
    eye_at = next((x, y) for y, r in enumerate(L["move"][LOST[0]]) for x, v in enumerate(r) if v == c["eye"])
    fw, fh = c["frame"], len(L["move"][0])
    pad = 2
    tw, th = (fw + 2 * pad) * S, (fh + 2 * pad) * S
    shown = [p for p in poses(L["move"]) if 2 <= p[0] <= 9]       # frames 2-3 to 8-9: the lost pose and its
    gap, M = 16, 48                                               # neighbours
    W = M * 2 + len(shown) * tw + (len(shown) - 1) * gap
    title, sub, head, small = font(40), font(23), font(24), font(20)
    heights = {"broken": 3, "fixed": 1}
    H = 40 + 96 + sum(56 + th + 44 + terminal([[("x", TEXT)]] * heights[r], 10).height + 40 for r in runs) + 8
    im = card(W, H)
    d = ImageDraw.Draw(im)
    d.text((M, 40), "pixel-anim-check", font=title, fill=TEXT)
    d.text((M, 92), "A walk loop with the eye painted over on one pose, and the same loop as drawn.", font=sub,
           fill=MUTED)
    y = 40 + 96 + 24
    for name, (lp, faults) in runs.items():
        bad = name == "broken"
        col = RED if bad else GREEN
        pill = name.upper()
        pw = int(d.textlength(pill, font=small)) + 28
        d.rounded_rectangle((M, y, M + pw, y + 34), 17, fill=col)
        d.text((M + 14, y + 17), pill, font=small, fill=BG, anchor="lm")
        d.text((M + pw + 16, y + 17), "eye lost on frames 6-7" if bad else "every pose as drawn", font=head,
               fill=TEXT, anchor="lm")
        y += 56
        x = M
        for k0, k1, _ in shown:
            f = lp["move"][k0]
            tile = np.zeros((fh + 2 * pad, fw + 2 * pad, 3), np.uint8)
            tile[:] = TILE
            tile[pad + fh - 1:] = (54, 48, 70)                   # the ground under the paws' row
            paste(tile, rgba(f), pad, pad)
            t = Image.fromarray(up(tile, S))
            mask = Image.new("L", t.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, t.width - 1, t.height - 1), 12, fill=255)
            im.paste(t, (x, y), mask)
            hit = k0 in LOST
            if hit:
                d.rounded_rectangle((x - 7, y - 7, x + tw + 6, y + th + 6), 18, outline=col, width=4)
            if k0 in LOST:                                        # a ring round the eye's place
                ex, ey = x + (pad + eye_at[0] + 0.5) * S, y + (pad + eye_at[1] + 0.5) * S
                r = 4.2 * S
                d.ellipse((ex - r, ey - r, ex + r, ey + r), outline=col, width=4)
            d.text((x + tw // 2, y + th + 24), f"frames {k0}-{k1}", font=small,
                   fill=col if hit else MUTED, anchor="mm")
            x += tw + gap
        y += th + 44
        ok = (GREEN if not faults else RED)
        lines = [[(f"{key}: {len(faults)} fault(s)", TEXT), (f">exit {1 if faults else 0}", ok)]]
        for ln in faults:
            kind, rest = ln.split(":", 1)
            lines.append([("  " + kind + ":", RED), (rest, TEXT)])
        term = terminal(lines, W - 2 * M)
        im.alpha_composite(term, (M, y))
        y += term.height + 40
    im.save(path, optimize=True)
    return im.size, runs["broken"][1]


# ---- parts.png ----------------------------------------------------------------------------------------------------
PART_COLOURS = {                                          # neighbours kept far apart in hue
    "torso": (124, 118, 244), "tail": (246, 192, 72), "neck": (238, 96, 104), "head": (104, 206, 128),
    "ear_far": (176, 128, 242), "ear_near": (240, 118, 200), "hind_near": (66, 206, 198),
    "hind_far": (250, 146, 72), "front_near": (186, 216, 80), "front_far": (80, 190, 240),
}
# where each part's name sits, in the drawing's game px (the chip's centre); the leader runs to the bone's middle
LABEL_AT = {
    "ear_far": (25, -4), "ear_near": (52, -4), "head": (58, 9), "neck": (58, 19), "tail": (-9, 3),
    "torso": (25, 8), "hind_near": (11, 40), "hind_far": (24, 45), "front_near": (34, 40), "front_far": (46, 45),
}


def parts_png(path, S=10):
    """body_parts.py's cut of the beast's drawing: each part tinted, the seams between parts drawn, the bones
    (placed by eye in marks.json) on top, every part named. The plain drawing beside it."""
    src = os.path.join(HERE, "beast", "beast_art_8x.png")
    with open(os.path.join(HERE, "beast", "marks.json"), encoding="utf-8") as fh:
        marks = json.load(fh)
    drawing = Image.open(src)
    res, aux = bp.analyse(drawing, marks)
    if res["warnings"]:
        sys.exit(f"parts: body_parts printed CHECK lines: {res['warnings']}")
    k = 8                                                 # the drawing is the creature at 8x
    lab8 = bp.full_labels(aux, drawing.size)
    art8 = np.asarray(drawing.convert("RGBA"))
    art = art8[k // 2::k, k // 2::k]                      # back to game px
    h, w = art.shape[:2]
    names = aux["names"]
    lab = np.full((h, w), -1)
    for y in range(h):                                    # each game pixel to the part holding most of it
        for x in range(w):
            if art[y, x, 3]:
                b = lab8[y * k:(y + 1) * k, x * k:(x + 1) * k].ravel()
                b = b[b >= 0]
                lab[y, x] = np.bincount(b).argmax() if len(b) else -1
    if (lab[art[..., 3] > 0] < 0).any():
        sys.exit("parts: a pixel of the drawing has no part")
    tint = np.zeros((h, w, 3))
    for i, n in enumerate(names):
        tint[lab == i] = PART_COLOURS[n]
    grey = art[..., :3].astype(float).mean(-1, keepdims=True) / 255.0
    body = np.clip(tint * (0.28 + 1.0 * grey), 0, 255).astype(np.uint8)   # the drawing's light and dark (its ink
                                                          # too) kept under the tint
    fig = Image.fromarray(np.dstack([up(body, S), up(art[..., 3], S)]), "RGBA")
    fd = ImageDraw.Draw(fig)
    for y in range(h):                                    # the seams: every edge between two parts
        for x in range(w):
            if lab[y, x] < 0:
                continue
            if x + 1 < w and lab[y, x + 1] >= 0 and lab[y, x + 1] != lab[y, x]:
                fd.line(((x + 1) * S, y * S - 1, (x + 1) * S, (y + 1) * S), fill=TEXT, width=3)
            if y + 1 < h and lab[y + 1, x] >= 0 and lab[y + 1, x] != lab[y, x]:
                fd.line((x * S - 1, (y + 1) * S, (x + 1) * S, (y + 1) * S), fill=TEXT, width=3)

    M, gutter_l, gutter_r, top_room, foot_room = 48, 200, 210, 70, 140
    thumb_s = 4
    tw, th = w * thumb_s, h * thumb_s
    fx = M + tw + 96 + gutter_l                           # the figure's left edge on the card
    W = fx + w * S + gutter_r + M - 60
    title, sub, chip_font, small = font(40), font(23), font(21), font(20)
    fy = 40 + 96 + 24 + top_room
    H = fy + h * S + foot_room
    im = card(W, H)
    d = ImageDraw.Draw(im)
    d.text((M, 40), "body_parts.py", font=title, fill=TEXT)
    d.text((M, 92), "Bones placed by eye (marks.json); the parts cut along the drawing's own ink and colour edges.",
           font=sub, fill=MUTED)
    # the plain drawing, and an arrow to the cut
    ty = fy + (h * S - th) // 2
    plate = Image.new("RGBA", (tw + 32, th + 32), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle((0, 0, plate.width - 1, plate.height - 1), 14, fill=PANEL + (255,))
    plate.alpha_composite(Image.fromarray(up(art, thumb_s), "RGBA"), (16, 16))
    im.alpha_composite(plate, (M, ty - 16))
    d.text((M + plate.width // 2, ty + th + 44), "the drawing", font=small, fill=MUTED, anchor="mm")
    ax0, ax1, ay = M + plate.width + 24, fx - gutter_l + 40, ty + th // 2
    d.line((ax0, ay, ax1 - 4, ay), fill=MUTED, width=3)
    d.polygon([(ax1, ay), (ax1 - 14, ay - 9), (ax1 - 14, ay + 9)], fill=MUTED)
    im.alpha_composite(fig, (fx, fy))

    def at(p):                                            # a point in the drawing's 8x pixels, on the card
        return fx + p[0] / k * S, fy + p[1] / k * S

    mids = {}
    for p in res["parts"]:
        pts = [q for q in p["bone"] if q is not None]
        mids[p["name"]] = at(pts[len(pts) // 2] if len(pts) % 2 else
                             [(a + b) / 2 for a, b in zip(pts[len(pts) // 2 - 1], pts[len(pts) // 2])])
    for p in res["parts"]:                                # leaders under the bones
        n = p["name"]
        cx, cy = fx + (LABEL_AT[n][0] + 0.5) * S, fy + (LABEL_AT[n][1] + 0.5) * S
        d.line((cx, cy, *mids[n]), fill=PART_COLOURS[n], width=2)
    for p in res["parts"]:                                # the bones: a dark-edged light line, dots at its points
        run = []
        for q in p["bone"] + [None]:
            if q is None:
                if len(run) > 1:
                    d.line(run, fill=BG, width=8, joint="curve")
                    d.line(run, fill=(250, 246, 238), width=3, joint="curve")
                run = []
            else:
                run.append(at(q))
        for j, q in enumerate(x for x in p["bone"] if x is not None):
            X, Y = at(q)
            r = 7 if j == 0 else 5
            d.ellipse((X - r, Y - r, X + r, Y + r), fill=PART_COLOURS[p["name"]], outline=BG, width=2)
    for p in res["parts"]:                                # the names
        n = p["name"]
        text = n.replace("_", " ")
        cx, cy = fx + (LABEL_AT[n][0] + 0.5) * S, fy + (LABEL_AT[n][1] + 0.5) * S
        tw_ = d.textlength(text, font=chip_font)
        d.rounded_rectangle((cx - tw_ / 2 - 12, cy - 16, cx + tw_ / 2 + 12, cy + 16), 16, fill=PART_COLOURS[n])
        d.text((cx, cy), text, font=chip_font, fill=BG, anchor="mm")
    im.save(path, optimize=True)
    return im.size, [(p["name"], p["area_share"]) for p in res["parts"]]


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
    for key in CREATURES:                                 # the pictures show clean animations, or none at all
        faults = pac.check(loops(key), spec(key))
        if faults:
            sys.exit(f"{key}: {len(faults)} fault(s), first: {faults[0]}  (fix the creature before the pictures)")
        print(f"{key}: 0 fault(s)")
    for name, build in (("hero.gif", hero), ("check.png", check_png), ("parts.png", parts_png)):
        path = os.path.join(out, name)
        tmp = path + ".new" + os.path.splitext(name)[1]
        size = build(tmp)[0]
        if unchanged(tmp, path):
            os.remove(tmp)
            print(f"same    {name}")
        else:
            os.replace(tmp, path)
            print(f"wrote   {name} ({size[0]}x{size[1]}, {os.path.getsize(path) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
