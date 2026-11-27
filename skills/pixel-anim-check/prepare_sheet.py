"""Turn a sprite sheet an image model drew (a grid of poses on a flat background, at its own size) into a strip of
frames on the approved drawing's own pixel grid, ready for pixel_anim_check.py and repair_sheet.py.

    python prepare_sheet.py SHEET.png --ref DRAWING.png [--grid CxR] [--colours N] [--cover 0.42] [--out DIR]
                            [--name NAME]
    python prepare_sheet.py --selftest
    python prepare_sheet.py --help

SHEET is the generated image. DRAWING is the approved character at game size (transparent background): every
frame comes out at its size, with the figure on its box.
1. Background: transparency when the sheet has it; else the colour of its four corners, every pixel within 90
   (summed over the channels) of it, and on a green key its greenish fringe too.
2. Cells: --grid CxR splits the sheet evenly (C columns, R rows, read row by row). Without it the grid is found:
   bands of rows with figure pixels split by empty rows, each band's columns by empty columns (gaps of 0.5 % of the
   sheet's side), a run under a quarter of the median (a spark alone in a gap) joined to its nearest. Give --grid
   when poses touch.
3. One scale: each cell's figure height against the drawing's; the median for every cell, a cell more than 8 % off
   taking its own (named in the log: the model drew it bigger or smaller). That own scale is read from the pose's
   height, so a pose that also crouches or rises is a little off: look at those frames.
4. One anchor: the lowest row of the figure on the drawing's lowest row, the middle of its lowest quarter (the feet,
   the hem) on the drawing's.
5. Down to the drawing's grid by vote, never an average: every sheet pixel is snapped to one palette first; a game
   pixel is drawn when --cover of its cell is figure, in the colour with the most area there. The palette is the
   drawing's own colours when it has 64 or fewer, else --colours tones (default 32) cut from the sheet's figure
   and 16 more from its saturated or bright pixels alone (a crystal, a glow, gold trim: small areas a cut over the
   whole figure merges away).
Out, in --out: <name>_strip.png (the frames side by side, the drawing's size each) and <name>_prepare.json (the
background, each cell's box and scale, the palette). The next command is printed.
Exit code: 0 done, 2 a usage error (no grid found, a missing file, a drawing without transparency).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

KEY_TOL = 90                                              # summed channel distance from the key colour that is air
GAP = 0.005                                               # an empty gap between poses, of the sheet's side
SLIVER = 0.25                                             # a run this share of the median run is a spark: joined
OWN_SCALE = 0.08                                          # a cell this far off the median scale keeps its own
REF_COLOURS = 64                                          # a drawing with this many colours or fewer is the palette
ACCENTS = 16                                              # tones cut from the sheet's vivid pixels alone


def _air(sheet):
    """(air mask, how it was read): transparency, or the corners' colour and its fringe."""
    alpha = sheet[..., 3]
    if (alpha < 128).mean() > 0.05:
        return alpha < 128, "transparency"
    rgb = sheet[..., :3].astype(int)
    corners = np.concatenate([rgb[:8, :8].reshape(-1, 3), rgb[:8, -8:].reshape(-1, 3), rgb[-8:, :8].reshape(-1, 3),
                              rgb[-8:, -8:].reshape(-1, 3)])
    key = np.median(corners, 0)
    air = np.abs(rgb - key).sum(-1) < KEY_TOL
    if key[1] > key[0] + 60 and key[1] > key[2] + 60:     # a green key leaves a greenish fringe round the figure
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        air |= (g > r + 40) & (g > b + 30)
    return air, "the colour #%02x%02x%02x and its fringe" % tuple(int(v) for v in key)


def _runs(filled, gap):
    """[(start, end)] of the runs of True, joined across gaps shorter than gap."""
    idx = np.nonzero(filled)[0]
    if not len(idx):
        return []
    out, start, last = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - last > gap:
            out.append((int(start), int(last)))
            start = i
        last = i
    out.append((int(start), int(last)))
    while len(out) > 1:                                   # a spark alone in a gap is joined to the nearest pose
        sizes = [b - a + 1 for a, b in out]
        k = min(range(len(out)), key=sizes.__getitem__)
        if sizes[k] >= SLIVER * float(np.median(sizes)):
            break
        left = out[k][0] - out[k - 1][1] if k > 0 else None
        right = out[k + 1][0] - out[k][1] if k + 1 < len(out) else None
        j = k - 1 if right is None or (left is not None and left <= right) else k + 1
        a, b = min(k, j), max(k, j)
        out[a:b + 1] = [(out[a][0], out[b][1])]
    return out


def cells(air, grid=None):
    """[(top, left, bottom, right)] of the cells, row by row."""
    H, W = air.shape
    if grid:
        cols, rows = grid
        return [(r * H // rows, c * W // cols, (r + 1) * H // rows - 1, (c + 1) * W // cols - 1)
                for r in range(rows) for c in range(cols)]
    fig = ~air
    gap = max(2, round(GAP * max(H, W)))
    out = []
    for top, bottom in _runs(fig.any(1), gap):
        for left, right in _runs(fig[top:bottom + 1].any(0), gap):
            out.append((top, left, bottom, right))
    return out


def _box(m):
    ys, xs = np.nonzero(m)
    return int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())


def _lower_middle(m):
    """The middle column of the figure's lowest quarter (the feet and the hem, not a staff's or a cape's reach)."""
    y0, y1, _, _ = _box(m)
    _, xs = np.nonzero(m[y0 + 3 * (y1 - y0) // 4:y1 + 1])
    return float(np.median(xs))


def _palette(ref, sheet_px, n):
    ref_px = ref[ref[..., 3] >= 128][:, :3]
    own = np.unique(ref_px, axis=0)
    if len(own) <= REF_COLOURS:
        return own.astype(np.uint8), "the drawing's own"
    def cut(px, k):
        q = Image.fromarray(px.reshape(-1, 1, 3).astype(np.uint8), "RGB").quantize(colors=k,
                                                                                    method=Image.Quantize.MEDIANCUT)
        return np.array(q.getpalette()[:3 * k], np.uint8).reshape(-1, 3)
    px = sheet_px.astype(int)
    mx, mn = px.max(1), px.min(1)
    lum = 0.299 * px[:, 0] + 0.587 * px[:, 1] + 0.114 * px[:, 2]
    vivid = px[(((mx - mn) > 0.45 * np.maximum(mx, 1)) & (mx > 120)) | (lum > 170)]
    pal = cut(px, n)                                      # a cut over the whole figure merges small vivid areas (a
    if len(vivid) >= ACCENTS:                             # crystal, a glow, gold trim) into their surroundings
        pal = np.unique(np.concatenate([pal, cut(vivid, ACCENTS)]), axis=0)
    return pal, f"{n} cut from the sheet and {ACCENTS} from its vivid pixels"


def _snap(rgb, pal):
    """Each pixel's nearest palette index (no dithering), exact: each distinct colour is matched once. (PIL's own
    palette mapping drops bits, and a grain tone 4 apart from its base collapsed into it.)"""
    rgb = rgb.astype(np.int64)
    packed = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
    colours, inverse = np.unique(packed.ravel(), return_inverse=True)
    c = np.stack([colours >> 16, (colours >> 8) & 255, colours & 255], -1)
    nearest = np.empty(len(c), np.int64)
    for i in range(0, len(c), 4096):
        d = ((c[i:i + 4096, None, :] - pal[None, :, :].astype(np.int64)) ** 2).sum(-1)
        nearest[i:i + 4096] = d.argmin(1)
    return nearest[inverse].reshape(packed.shape)


def down(rgb, air, s, oy, ox, pal, size, cover):
    """One cell brought down to size (h, w) by vote: game pixel (Y, X) reads the cell's pixels whose
    ((y - oy) / s, (x - ox) / s) fall in it; drawn when cover of them is figure, in their commonest palette colour."""
    h, w = size
    H, W = air.shape
    yy, xx = np.mgrid[0:H, 0:W]
    Y, X = np.floor((yy + 0.5 - oy) / s).astype(int), np.floor((xx + 0.5 - ox) / s).astype(int)
    inside = (Y >= 0) & (Y < h) & (X >= 0) & (X < w)
    flat = (Y * w + X)[inside]
    total = np.bincount(flat, minlength=h * w)
    fig = inside & ~air
    idx = _snap(rgb, pal)
    votes = np.bincount((Y * w + X)[fig] * len(pal) + idx[fig], minlength=h * w * len(pal)).reshape(h * w, len(pal))
    shown = votes.sum(1) >= cover * np.maximum(total, 1)
    shown &= total > 0
    out = np.zeros((h * w, 4), np.uint8)
    out[shown, :3] = pal[votes[shown].argmax(1)]
    out[shown, 3] = 255
    return out.reshape(h, w, 4)


def prepare(sheet, ref, grid=None, colours=32, cover=0.42):
    """(frames as an (n, h, w, 4) array, log): see the module's help."""
    air, background = _air(sheet)
    boxes = [b for b in cells(air, grid) if (~air[b[0]:b[2] + 1, b[1]:b[3] + 1]).any()]
    if len(boxes) < 2:
        raise ValueError("found fewer than 2 poses on the sheet: give --grid CxR")
    rm = ref[..., 3] >= 128
    if not rm.any() or rm.all():
        raise ValueError("the drawing needs a transparent background and a figure")
    ry0, ry1, _, _ = _box(rm)
    rh, rmid = ry1 - ry0 + 1, _lower_middle(rm)
    parts = []
    for top, left, bottom, right in boxes:
        a = air[top:bottom + 1, left:right + 1]
        y0, y1, _, _ = _box(~a)
        parts.append((sheet[top:bottom + 1, left:right + 1, :3], a, (y1 - y0 + 1) / rh))
    scales = [p[2] for p in parts]
    s_all = float(np.median(scales))
    pal, which = _palette(ref, np.concatenate([rgb[~a] for rgb, a, _ in parts]), colours)
    frames, notes = [], []
    for (top, left, bottom, right), (rgb, a, s) in zip(boxes, parts):
        own = abs(s / s_all - 1) > OWN_SCALE
        use = s if own else s_all
        _, y1, _, _ = _box(~a)
        oy = (y1 + 1) - (ry1 + 1) * use
        ox = (_lower_middle(~a) + 0.5) - (rmid + 0.5) * use   # pixel centres on both sides
        frames.append(down(rgb, a, use, oy, ox, pal, ref.shape[:2], cover))
        notes.append({"box": [top, left, bottom, right], "scale": round(use, 3), "own_scale": own})
    return np.stack(frames), {"background": background, "cells": notes, "scale": round(s_all, 3),
                              "palette": f"{len(pal)} colours, {which}"}


def main(argv):
    if not argv or "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0 if argv else 2
    valued = {"--ref", "--grid", "--colours", "--cover", "--out", "--name"}
    try:
        src, got, i = None, {}, 0
        while i < len(argv):
            if argv[i] in valued:
                if i + 1 >= len(argv):
                    raise ValueError(f"{argv[i]} needs a value")
                got[argv[i]] = argv[i + 1]
                i += 2
            elif argv[i].startswith("--") or src is not None:
                raise ValueError(f"unknown argument {argv[i]!r}")
            else:
                src = argv[i]
                i += 1
        if src is None or not os.path.isfile(src):
            raise ValueError(f"no such sheet: {src}")
        if "--ref" not in got or not os.path.isfile(got["--ref"]):
            raise ValueError("--ref needs the approved drawing at game size")
        grid = None
        if "--grid" in got:
            c, _, r = got["--grid"].lower().partition("x")
            if not (c.isdigit() and r.isdigit() and int(c) > 0 and int(r) > 0):
                raise ValueError(f"--grid takes CxR, such as 4x4, not {got['--grid']!r}")
            grid = (int(c), int(r))
        colours = int(got.get("--colours", 32))
        cover = float(got.get("--cover", 0.42))
        if not 2 <= colours <= 256 or not 0 < cover <= 1:
            raise ValueError("--colours is 2 to 256 and --cover over 0 and at most 1")
        name = got.get("--name", os.path.splitext(os.path.basename(src))[0])
        folder = got.get("--out", ".")
        os.makedirs(folder, exist_ok=True)
        targets = [os.path.join(folder, f"{name}_{tail}") for tail in ("strip.png", "prepare.json")]
        for t in targets:
            if any(os.path.exists(t) and os.path.samefile(t, s) for s in (src, got["--ref"])):
                raise ValueError(f"would write over an input: {t}")
        with Image.open(src) as im:
            sheet = np.array(im.convert("RGBA"))
        with Image.open(got["--ref"]) as im:
            ref = np.array(im.convert("RGBA"))
        frames, log = prepare(sheet, ref, grid, colours, cover)
    except (ValueError, OSError) as e:
        print(f"error: {e}  (--help lists the options)", file=sys.stderr)
        return 2
    n, h, w = frames.shape[:3]
    Image.fromarray(np.concatenate(list(frames), 1), "RGBA").save(targets[0])
    with open(targets[1], "w", encoding="utf-8", newline="\n") as fh:
        json.dump(log, fh, indent=1)
        fh.write("\n")
    print(f"{name}: {n} frames of {w}x{h} from the sheet ({log['background']}; scale {log['scale']} sheet px a game "
          f"px; palette {log['palette']})")
    for k, c in enumerate(log["cells"]):
        if c["own_scale"]:
            off = c["scale"] / log["scale"] - 1
            print(f"  frame {k}: drawn {off:+.0%} off the others' size, kept at its own scale")
    print("strip:", targets[0], " log:", targets[1])
    print(f"next: python -I {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pixel_anim_check.py')} "
          f"--loop idle={targets[0]} --frame {w} --style redrawn --fps N --out {folder} --name {name}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            import prepare_sheet_selftest
        except ImportError:
            print("error: --selftest needs prepare_sheet_selftest.py beside this file", file=sys.stderr)
            sys.exit(2)
        sys.exit(0 if prepare_sheet_selftest.run() else 1)
    sys.exit(main(sys.argv[1:]))
