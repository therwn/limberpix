"""The README's two still pictures, check.png and parts.png, drawn from the beast. make_showcase.py calls these after
it has checked every creature; see its docstring. All their text is pixfont.py, the pixel font beside this file, so
they come out the same with any Pillow."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import body_parts as bp
import make_showcase as ms
import pixel_anim_check as pac
import pixfont

BG = (22, 19, 30)
PANEL = (32, 28, 43)
TILE = (63, 56, 80)
TEXT = (238, 230, 216)
MUTED = (148, 139, 166)
RED = (242, 88, 92)
GREEN = (98, 210, 144)
TERM = (13, 11, 19)
CAP = 7                                                   # a capital's height in font pixels


def put(im, x, y, text, colour, scale=3, centre=False):
    """A line of pixel text with its top-left at (x, y), or with centre=True centred on (x, y) (the capitals' middle)."""
    if centre:
        x, y = x - pixfont.width(text, scale) // 2, y - CAP * scale // 2
    pixfont.draw(im, int(round(x)), int(round(y)), text, colour, scale)


def card(w, h, radius=28):
    """The picture's ground: a dark rounded card, transparent outside, so it sits on a light or a dark page."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=BG + (255,))
    return im


TOP = 168                                                 # the first row under the heading


def heading(im, title, sub, M=48):
    put(im, M, 44, title, TEXT, 5)
    put(im, M, 108, sub, MUTED, 3)


# ---- check.png ----------------------------------------------------------------------------------------------------
LOST = (6, 7)                                             # the beast's move frames whose eye is painted over
GLINT = "#b3631f"                                         # the eye's lower half, painted over with it


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
    """The frame with its eye painted the fur's colour beside it, as when the head moves on without its eye."""
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
    """The beast's walk, three poses round the fault, broken and as drawn, each with what the check printed. The
    tiles show the walk's own box (the frame's room for the lunge left out)."""
    key, c = "beast", ms.CREATURES["beast"]
    L = ms.loops(key)
    broken = dict(L, move=[lose_eye(f, c["eye"], GLINT) if k in LOST else f for k, f in enumerate(L["move"])])
    sp = ms.spec(key)
    runs = {"broken": (broken, pac.check(broken, sp)), "fixed": (L, pac.check(L, sp))}
    if runs["fixed"][1] or [ln.split(":")[0] for ln in runs["broken"][1]] != ["eye", "eye"]:
        sys.exit(f"check: unexpected faults {runs['broken'][1]} / {runs['fixed'][1]}")
    alpha = np.any([ms.rgba(f)[..., 3] > 0 for f in L["move"]], 0)
    ys, xs = np.nonzero(alpha)
    bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    eye = [(x - bx0, y - by0) for y, r in enumerate(L["move"][LOST[0]]) for x, v in enumerate(r) if v == c["eye"]]
    eye_at = (sum(p[0] for p in eye) / len(eye), sum(p[1] for p in eye) / len(eye))
    fw, fh = bx1 - bx0, by1 - by0
    pad = 3
    tw, th = (fw + 2 * pad) * S, (fh + 2 * pad) * S
    shown = [p for p in poses(L["move"]) if 4 <= p[0] <= 9]      # the lost pose and its neighbours
    gap, M = 24, 48
    W = M * 2 + len(shown) * tw + (len(shown) - 1) * gap
    heights = {"broken": 3, "fixed": 1}
    H = TOP + sum(60 + th + 52 + terminal([[("x", TEXT)]] * heights[r], 10).height + 40 for r in runs) + 8
    im = card(W, H)
    heading(im, "pixel-anim-check", "The walk with the eye painted over on one pose, and as drawn.")
    d = ImageDraw.Draw(im)
    y = TOP
    for name, (lp, faults) in runs.items():
        bad = name == "broken"
        col = RED if bad else GREEN
        pill = name.upper()
        pw = pixfont.width(pill, 3) + 32
        d.rounded_rectangle((M, y, M + pw, y + 38), 19, fill=col)
        put(im, M + pw / 2, y + 19, pill, BG, 3, centre=True)
        put(im, M + pw + 20, y + 19 - CAP * 3 // 2, f"eye lost on frames {LOST[0]}-{LOST[1]}" if bad else
            "every pose as drawn", TEXT, 3)
        y += 60
        x = M
        for k0, k1, _ in shown:
            f = ms.rgba(lp["move"][k0])[by0:by1, bx0:bx1]
            tile = np.zeros((fh + 2 * pad, fw + 2 * pad, 3), np.uint8)
            tile[:] = TILE
            tile[pad + fh:] = (54, 48, 70)                      # the ground under the paws' row
            ms.paste(tile, f, pad, pad)
            t = Image.fromarray(ms.up(tile, S))
            mask = Image.new("L", t.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, t.width - 1, t.height - 1), 14, fill=255)
            im.paste(t, (x, y), mask)
            if bad and k0 in LOST:
                d.rounded_rectangle((x - 8, y - 8, x + tw + 7, y + th + 7), 20, outline=col, width=4)
            if k0 in LOST:                                        # a ring round the eye's place
                ex, ey = x + (pad + eye_at[0] + 0.5) * S, y + (pad + eye_at[1] + 0.5) * S
                r = 4.0 * S
                d.ellipse((ex - r, ey - r, ex + r, ey + r), outline=col, width=4)
            put(im, x + tw / 2, y + th + 28, f"frames {k0}-{k1}", col if k0 in LOST else MUTED, 3, centre=True)
            x += tw + gap
        y += th + 52
        ok = GREEN if not faults else RED
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
    "jaw": (250, 236, 120), "ear_far": (176, 128, 242), "ear_near": (240, 118, 200), "hind_near": (66, 206, 198),
    "hind_far": (250, 146, 72), "front_near": (186, 216, 80), "front_far": (80, 190, 240),
}
# where each part's name sits, in the drawing's game px (the chip's centre); the leader runs to the bone's middle
LABEL_AT = {
    "ear_far": (49, 1), "ear_near": (76, 1), "head": (87, 10), "jaw": (85, 21), "neck": (85, 32),
    "tail": (-6, 30), "torso": (32, 10), "hind_near": (8, 52), "hind_far": (25, 58), "front_near": (69, 52),
    "front_far": (47, 58),
}


def parts_png(path, S=10):
    """body_parts.py's cut of the beast's drawing: each part tinted, the seams between parts drawn, the bones
    (placed by eye in marks.json) on top, every part named. The plain drawing beside it."""
    src = os.path.join(ms.HERE, "beast", "beast_art_8x.png")
    with open(os.path.join(ms.HERE, "beast", "marks.json"), encoding="utf-8") as fh:
        marks = json.load(fh)
    drawing = Image.open(src)
    res, aux = bp.analyse(drawing, marks)
    if res["warnings"]:
        sys.exit(f"parts: body_parts printed CHECK lines: {res['warnings']}")
    k = 8                                                 # the drawing is the creature at 8x
    lab8 = bp.full_labels(aux, drawing.size)
    art8 = np.asarray(drawing.convert("RGBA"))
    full = art8[k // 2::k, k // 2::k]                     # back to game px
    ys, xs = np.nonzero(full[..., 3])
    cx0, cy0 = xs.min(), ys.min()                         # the figure's box: the canvas's room for the lunge left out
    art = full[cy0:ys.max() + 1, xs.min():xs.max() + 1]
    h, w = art.shape[:2]
    names = aux["names"]
    lab = np.full((h, w), -1)
    for y in range(h):                                    # each game pixel to the part holding most of it
        for x in range(w):
            if art[y, x, 3]:
                b = lab8[(y + cy0) * k:(y + cy0 + 1) * k, (x + cx0) * k:(x + cx0 + 1) * k].ravel()
                b = b[b >= 0]
                lab[y, x] = np.bincount(b).argmax() if len(b) else -1
    if (lab[art[..., 3] > 0] < 0).any():
        sys.exit("parts: a pixel of the drawing has no part")
    inside = {p["name"]: p.get("inside") for p in res["parts"]}
    tint = np.zeros((h, w, 3))
    for i, n in enumerate(names):                         # a part inside its parent (the jaw in the head) wears
        tint[lab == i] = PART_COLOURS[inside[n] or n]     # the parent's colour, hatched in its own below
    grey = art[..., :3].astype(float).mean(-1, keepdims=True) / 255.0
    shade = 0.34 + 1.1 * grey                             # the drawing's light and dark (its ink too) under the tint
    body = ms.up(np.clip(tint * shade, 0, 255).astype(np.uint8), S).copy()
    Y, X = np.mgrid[0:h * S, 0:w * S]
    stripe = ((X + Y) // 4) % 3 == 0
    for i, n in enumerate(names):
        if inside[n]:
            sel = ms.up((lab == i).astype(np.uint8), S).astype(bool) & stripe
            own = np.clip(np.array(PART_COLOURS[n], float) * ms.up(shade, S)[..., 0:1].repeat(3, -1), 0, 255)
            body[sel] = own[sel].astype(np.uint8)
    fig = Image.fromarray(np.dstack([body, ms.up(art[..., 3], S)]), "RGBA")
    fd = ImageDraw.Draw(fig)
    for y in range(h):                                    # the seams: every edge between two parts
        for x in range(w):
            if lab[y, x] < 0:
                continue
            if x + 1 < w and lab[y, x + 1] >= 0 and lab[y, x + 1] != lab[y, x]:
                fd.line(((x + 1) * S, y * S - 1, (x + 1) * S, (y + 1) * S), fill=TEXT, width=3)
            if y + 1 < h and lab[y + 1, x] >= 0 and lab[y + 1, x] != lab[y, x]:
                fd.line((x * S - 1, (y + 1) * S, (x + 1) * S, (y + 1) * S), fill=TEXT, width=3)

    M, gutter_l, gutter_r, top_room, foot_room = 48, 120, 180, 60, 160
    thumb_s = 3
    tw, th = w * thumb_s, h * thumb_s
    fx = M + tw + 32 + 64 + gutter_l                      # the figure's left edge on the card
    W = fx + w * S + gutter_r + M
    fy = TOP + top_room
    H = fy + h * S + foot_room
    im = card(W, H)
    heading(im, "body_parts.py", "Bones placed by eye (marks.json), parts cut along the drawing's edges.")
    d = ImageDraw.Draw(im)
    # the plain drawing, and an arrow to the cut
    ty = fy + (h * S - th) // 2
    plate = Image.new("RGBA", (tw + 32, th + 32), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle((0, 0, plate.width - 1, plate.height - 1), 14, fill=PANEL + (255,))
    plate.alpha_composite(Image.fromarray(ms.up(art, thumb_s), "RGBA"), (16, 16))
    im.alpha_composite(plate, (M, ty - 16))
    put(im, M + plate.width / 2, ty + th + 48, "the drawing", MUTED, 3, centre=True)
    ax0, ax1, ay = M + plate.width + 24, fx - gutter_l + 24, ty + th // 2
    d.line((ax0, ay, ax1 - 4, ay), fill=MUTED, width=3)
    d.polygon([(ax1, ay), (ax1 - 14, ay - 9), (ax1 - 14, ay + 9)], fill=MUTED)
    im.alpha_composite(fig, (fx, fy))

    def at(p):                                            # a point in the drawing's 8x pixels, on the card
        return fx + (p[0] / k - cx0) * S, fy + (p[1] / k - cy0) * S

    def chip_at(n):
        return fx + (LABEL_AT[n][0] + 0.5) * S, fy + (LABEL_AT[n][1] + 0.5) * S

    mids = {}
    for p in res["parts"]:
        pts = [q for q in p["bone"] if q is not None]
        mids[p["name"]] = at(pts[len(pts) // 2] if len(pts) % 2 else
                             [(a + b) / 2 for a, b in zip(pts[len(pts) // 2 - 1], pts[len(pts) // 2])])
    for p in res["parts"]:                                # leaders under the bones
        d.line((*chip_at(p["name"]), *mids[p["name"]]), fill=PART_COLOURS[p["name"]], width=2)
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
        cx, cy = (int(round(v)) for v in chip_at(n))     # whole pixels: Pillows round half pixels differently
        half = pixfont.width(text, 3) // 2 + 12
        d.rounded_rectangle((cx - half, cy - 18, cx + half, cy + 18), 18, fill=PART_COLOURS[n], outline=BG, width=2)
        put(im, cx, cy, text, BG, 3, centre=True)
    im.save(path, optimize=True)
    return im.size, [(p["name"], p["area_share"]) for p in res["parts"]]
