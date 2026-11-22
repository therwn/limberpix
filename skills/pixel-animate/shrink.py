"""Bring one frame posed at the reference's resolution down to game size: each game pixel reads its own cell of
reference pixels.

    python shrink.py REF.png --size W,H --palette REST.png [--rest REST.png] [--cover 0.42] [--contour 70]
                     [--key "#rrggbb"] [--out DIR] [--name NAME]
    python shrink.py REF.png --size W,H --colours N [...]     # the rest frame: no palette yet, make one of N tones
    python shrink.py REF.png --scale S ...                    # S reference px to a game px, in place of --size
    python shrink.py --selftest
    python shrink.py --help

REF is one frame at the reference's resolution, cropped to the box every pose of every loop fits in: the grid is laid
over the whole image, so one box and one size for every frame keep the still parts on the same game pixels.
Transparency is air (--key names an opaque background colour instead). --size is the game size of that box; with
--scale S the size is the box divided by S, rounded (S need not be whole: a cell of 24.3 reference px is fine).
A game pixel is made from its cell in this order:
1. Coverage. It is drawn when at least --cover of its cell is figure (default 0.42), air otherwise. Lower it (0.3)
   for a creature with thin parts, a narrow wing or a tail joint, that would otherwise break.
2. The contour is read apart from the fill. Contour pixels are the reference's near-black ones (red + green + blue
   under --contour, default 70). A cell is contour when they fill 0.45 of its figure, or 0.12 of it and the cell
   is the line's crest: across the line (the way the contour falls off on both sides) it holds more than the cell
   before it and no less than the one after. So a line thinner than a cell is kept whole and one pixel wide, and
   it does not double where it straddles two cells. --no-contour turns this off.
3. The fill is voted. Every other reference pixel is first snapped to the palette (the nearest colour in CIE Lab);
   the cell takes the colour most of them took. Colours are never averaged: the mean of a cell is a tone the drawing
   does not hold, and it changes with every small move.
4. A tie goes to the colour the rest frame has at that game pixel (--rest), when it is one of the tied; otherwise to
   the first of them in the palette's order (dark to light), so a tie falls the same way on every frame.
The palette is every opaque colour of --palette (the rest frame already shrunk, or the approved drawing at game
size), or with --colours N it is made from REF: N - 1 tones of the fill (k-means in Lab, started from the fill's
lightness steps) and one for the contour. One image gives one palette every time. Shrink the rest frame once with
--colours, then pass its <name>_shrunk.png as --palette and --rest for every other frame: one palette for every loop.
Fewer tones (10-12) for a busy texture, 16-18 for a plain one.

Not done here (pixel-animate's step 5 does them after it): putting back the eye and the small marks the shrink
loses, dropping a lone pixel a turned part's edge leaves, and the one-pixel outline, drawn last on every frame.

Out: <name>_shrunk.png (game size, palette colours only) and, with --colours, <name>_palette.png (one pixel a
colour, dark to light). --out defaults to REF's folder, --name to REF's file name.
Exit code: 0 done, 2 a usage error (a bad option, a missing file, an image with no transparency and no --key, a rest
frame of another size).

Why these rules (REFERENCES.md has the numbers): on six painted reference drawings brought down 24 to 36 times,
18 tones each, this left 18 % of the figure as lone pixels and changed 34 % of it when the drawing moved a fifth
of a cell; averaging each cell left 42 % and 67 %, one sample at the cell's centre 41 % and 65 %. Reading the
contour apart kept it on 25 % of the figure; the same vote without it kept 9 %, and the outlines broke."""
import os
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError as e:                                  # python -I does not see a pip install --user
    raise type(e)(f"{e}: {os.path.basename(__file__)} needs numpy and Pillow. python -I (isolated mode) does "
                  "not see packages installed with pip install --user: install them in a virtual "
                  "environment or for the whole system, or run without -I", name=e.name) from None

COVER = 0.42                                              # a game pixel is drawn when this share of its cell is figure
CONTOUR = 70                                              # red + green + blue under this is the drawing's contour
LINE_SOLID, LINE_LOW = 0.45, 0.12                         # a cell this much contour is a line; this much, when no
                                                          # less than the cells either side of it
KMEANS_ROUNDS, KMEANS_SAMPLE = 16, 40000                  # --colours: k-means rounds, and the most pixels it reads


# ---- colour ------------------------------------------------------------------------------------------------------
def to_lab(rgb):
    """sRGB (0-255, any shape ending in 3) to CIE Lab (D65)."""
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    xyz = xyz / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def ordered(colours):
    """Distinct RGB colours as an N x 3 uint8 array in one fixed order: dark to light, then by red, green, blue."""
    cs = sorted({tuple(int(v) for v in c) for c in colours},
                key=lambda c: (round(float(to_lab(np.array(c))[0]), 6), c))
    return np.array(cs, np.uint8).reshape(-1, 3)


def snap(rgb, pal, rows=64):
    """The index of the palette colour nearest each pixel in Lab; the first in the palette's order on a tie."""
    plab = to_lab(pal)
    out = np.empty(rgb.shape[:2], np.int32)
    for y in range(0, rgb.shape[0], rows):                # in bands of rows, to keep the distance table small
        d = ((to_lab(rgb[y:y + rows])[:, :, None, :] - plab[None, None]) ** 2).sum(-1)
        out[y:y + rows] = d.argmin(-1)
    return out


def _tones(px, n):
    """n colours the pixels px (m x 3) hold: k-means in Lab, started from their lightness steps, on at most
    KMEANS_SAMPLE of them taken at an even stride; each tone is the pixel nearest its cluster's centre. Nothing
    random. Fewer than n come back when px holds fewer colours."""
    px = px[::max(1, len(px) // KMEANS_SAMPLE)]
    uniq = np.unique(px, axis=0)
    if len(uniq) <= n:
        return [tuple(c) for c in uniq]
    lab = to_lab(px)
    order = np.argsort(lab[:, 0], kind="stable")
    cent = lab[order[((np.arange(n) + 0.5) * len(px) / n).astype(int)]].copy()
    near = None
    for _ in range(KMEANS_ROUNDS + 1):
        near = ((lab[:, None, :] - cent[None]) ** 2).sum(-1).argmin(1)
        for i in range(n):
            if (near == i).any():
                cent[i] = lab[near == i].mean(0)
    return [tuple(px[np.nonzero(near == i)[0][((lab[near == i] - cent[i]) ** 2).sum(1).argmin()]])
            for i in range(n) if (near == i).any()]


def make_palette(ref, n, contour=CONTOUR):
    """A palette of at most n colours from a reference (H x W x 4): n - 1 tones of its fill and one of its contour
    (the pixels with red + green + blue under contour; None or 0: no contour, n tones of the whole figure)."""
    fig = ref[..., 3] >= 128
    if not fig.any():
        raise ValueError("nothing drawn in the reference")
    rgb = ref[..., :3]
    dark = fig & (rgb.astype(int).sum(-1) < contour) if contour else np.zeros(fig.shape, bool)
    if dark.any() and (fig & ~dark).any():
        return ordered(_tones(rgb[dark], 1) + _tones(rgb[fig & ~dark], max(1, n - 1)))
    return ordered(_tones(rgb[fig], n))


# ---- the shrink --------------------------------------------------------------------------------------------------
def shrink(ref, pal, size, rest=None, cover=COVER, contour=CONTOUR):
    """ref: H x W x 4 uint8 (RGBA), the whole grid's box. pal: N x 3 uint8 in its fixed order (ordered()).
    size: (w, h), the game size of that box. rest: the rest frame as h x w palette indices (-1 air), or None.
    contour: red + green + blue under this is contour (None or 0: none read). Returns h x w palette indices, -1
    for air. See the module's help for the rules."""
    H, W = ref.shape[:2]
    w, h = size
    if not (1 <= w <= W and 1 <= h <= H):
        raise ValueError(f"the game size {w}x{h} does not fit a {W}x{H} reference")
    if rest is not None and rest.shape != (h, w):
        raise ValueError(f"the rest frame is {rest.shape[1]}x{rest.shape[0]}, the shrunk frame {w}x{h}")
    fig = ref[..., 3] >= 128
    rgb = ref[..., :3]
    dark = fig & (rgb.astype(int).sum(-1) < contour) if contour else np.zeros(fig.shape, bool)
    idx = snap(rgb, pal)
    n = len(pal)
    xs = [int(x * W / w) for x in range(w)] + [W]         # a cell's columns run from xs[x] to xs[x + 1], rows alike
    ys = [int(y * H / h) for y in range(h)] + [H]
    covered = np.zeros((h, w))
    share = np.zeros((h, w))                              # the contour's share of the cell's figure
    fill = np.full((h, w), -1)
    line = np.full((h, w), -1)                            # the contour's own colour there
    for y in range(h):
        for x in range(w):
            sl = (slice(ys[y], max(ys[y] + 1, ys[y + 1])), slice(xs[x], max(xs[x] + 1, xs[x + 1])))
            f, d, i = fig[sl], dark[sl], idx[sl]
            m = int(f.sum())
            covered[y, x] = m / f.size
            if not m:
                continue
            k = int(d.sum())
            share[y, x] = k / m
            if k:
                line[y, x] = np.bincount(i[d], minlength=n).argmax()
            if m > k:
                cnt = np.bincount(i[f & ~d], minlength=n)
                top = cnt.max()
                fill[y, x] = cnt.argmax()                 # the first of the tied, in the palette's order
                if rest is not None and rest[y, x] >= 0 and cnt[rest[y, x]] == top:
                    fill[y, x] = rest[y, x]
    # a line's crest, read across the line. Along a line the cells hold the same contour; across it the contour
    # falls away on both sides. So the pair of neighbours with the larger fall (how much less they hold than the
    # cell, summed; at the frame's edge the cell stands in for its missing neighbour) lies across the line, and
    # on that pair the cell is the crest when it holds more than the one before and no less than the one after:
    # of two cells a line straddles evenly, the first takes it. With the falls equal (a dot, or the end of a
    # thick line's spill into the next cell) it must be the crest both ways.
    e, z = np.pad(share, 1, mode="edge"), np.pad(share, 1)
    mid = z[1:-1, 1:-1]
    fall_h = np.maximum(mid - e[1:-1, :-2], 0) + np.maximum(mid - e[1:-1, 2:], 0)
    fall_v = np.maximum(mid - e[:-2, 1:-1], 0) + np.maximum(mid - e[2:, 1:-1], 0)
    crest_h = (mid > z[1:-1, :-2]) & (mid >= z[1:-1, 2:])
    crest_v = (mid > z[:-2, 1:-1]) & (mid >= z[2:, 1:-1])
    ridge = np.where(fall_h > fall_v, crest_h, np.where(fall_v > fall_h, crest_v, crest_h & crest_v))
    is_line = (line >= 0) & ((share >= LINE_SOLID) | ((share >= LINE_LOW) & ridge) | (fill < 0))
    return np.where(covered >= cover, np.where(is_line, line, fill), -1)


def to_image(idx, pal):
    """Palette indices (-1 air) as an RGBA image."""
    rgba = np.zeros(idx.shape + (4,), np.uint8)
    rgba[idx >= 0, :3] = pal[idx[idx >= 0]]
    rgba[idx >= 0, 3] = 255
    return Image.fromarray(rgba)


def read(path, key=None):
    """An image as H x W x 4 uint8; key (r, g, b), if given, is read as air."""
    a = np.asarray(Image.open(path).convert("RGBA")).copy()
    if key is not None:
        a[(a[..., :3] == np.array(key, np.uint8)).all(-1), 3] = 0
    return a


def hexrgb(v):
    """'#rrggbb' (any case, the # optional) to (r, g, b). ValueError when it is not six hex digits."""
    t = v.strip().lower().lstrip("#")
    if len(t) != 6 or any(c not in "0123456789abcdef" for c in t):
        raise ValueError(f"not a colour (#rrggbb): {v!r}")
    return int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16)


# ---- the command line --------------------------------------------------------------------------------------------
def main(argv):
    """The command line (see the module's help). Returns the exit code: 0 done, 2 a usage error."""
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    valued = {"--size", "--scale", "--palette", "--colours", "--rest", "--cover", "--contour", "--key", "--out",
              "--name"}
    flags = {"--no-contour"}
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
            raise ValueError("give one reference image" if not pos else f"one reference image only, not {pos}")
        for p in [pos[0]] + [opts[o] for o in ("--palette", "--rest") if o in opts]:
            if not os.path.isfile(p):
                raise ValueError(f"no such file: {p}")

        def number(name, lo, hi, what):
            try:
                v = float(opts[name])
            except ValueError:
                v = float("nan")
            if not lo <= v <= hi:                         # a NaN fails this too
                raise ValueError(f"{name} must be {what}, not {opts[name]!r}")
            return v
        if ("--size" in opts) == ("--scale" in opts):
            raise ValueError("give --size W,H (the game size of the image) or --scale S (reference px to a game "
                             "px), one of the two")
        if ("--palette" in opts) == ("--colours" in opts):
            raise ValueError("give --palette IMAGE (the rest frame's colours) or --colours N, one of the two")
        if "--contour" in opts and "--no-contour" in opts:
            raise ValueError("give --contour or --no-contour, not both")
        n = int(number("--colours", 2, 256, "a whole number from 2 to 256")) if "--colours" in opts else None
        if n is not None and not opts["--colours"].strip().isdigit():
            raise ValueError(f"--colours must be a whole number from 2 to 256, not {opts['--colours']!r}")
        cover = number("--cover", 0.01, 1.0, "a share from 0.01 to 1") if "--cover" in opts else COVER
        contour = 0 if "--no-contour" in opts else (
            number("--contour", 1, 765, "a number from 1 to 765") if "--contour" in opts else CONTOUR)
        key = hexrgb(opts["--key"]) if "--key" in opts else None
        ref = read(pos[0], key)
        fig = ref[..., 3] >= 128
        if not fig.any():
            raise ValueError(f"{pos[0]} has nothing drawn")
        if fig.all():
            raise ValueError(f"{pos[0]} has no transparent pixel: transparency is read as air. Export it with a "
                             f"transparent background, or name the background colour with --key #rrggbb")
        H, W = ref.shape[:2]
        if "--size" in opts:
            parts = opts["--size"].lower().replace("x", ",").split(",")
            if len(parts) != 2 or not all(p.strip().isdigit() and int(p) > 0 for p in parts):
                raise ValueError(f"--size takes W,H in game px, not {opts['--size']!r}")
            size = (int(parts[0]), int(parts[1]))
        else:
            s = number("--scale", 1.0, float(max(W, H)), "1 or more reference px to a game px")
            size = (max(1, round(W / s)), max(1, round(H / s)))
        if size[0] > W or size[1] > H:
            raise ValueError(f"the game size {size[0]}x{size[1]} is larger than the {W}x{H} reference")
        if n is not None:
            pal = make_palette(ref, n, contour)
        else:
            src = read(opts["--palette"], key)
            pal = ordered(src[..., :3][src[..., 3] >= 128])
            if not len(pal):
                raise ValueError(f"{opts['--palette']} has nothing drawn")
            if len(pal) > 256:
                raise ValueError(f"{opts['--palette']} holds {len(pal)} colours: a palette is the rest frame at "
                                 f"game size, or a swatch (256 colours at most)")
        rest = None
        if "--rest" in opts:
            r = read(opts["--rest"], key)
            if r.shape[:2] != (size[1], size[0]):
                raise ValueError(f"{opts['--rest']} is {r.shape[1]}x{r.shape[0]}; the shrunk frame is "
                                 f"{size[0]}x{size[1]}")
            rest = np.where(r[..., 3] >= 128, snap(r[..., :3], pal), -1)
        out = shrink(ref, pal, size, rest, cover, contour)
    except ValueError as e:
        print(f"error: {e}  (--help lists the options)", file=sys.stderr)
        return 2
    name = opts.get("--name", os.path.splitext(os.path.basename(pos[0]))[0])
    folder = opts.get("--out", os.path.dirname(os.path.abspath(pos[0])))
    os.makedirs(folder, exist_ok=True)
    target = os.path.join(folder, f"{name}_shrunk.png")
    to_image(out, pal).save(target)
    print(f"{name}: {out.shape[1]}x{out.shape[0]} px, {int((out >= 0).sum())} drawn, "
          f"{len(np.unique(out[out >= 0]))} of {len(pal)} palette colours used")
    if n is not None:
        swatch = os.path.join(folder, f"{name}_palette.png")
        Image.fromarray(np.concatenate([pal, np.full((len(pal), 1), 255, np.uint8)], 1)[None]).save(swatch)
        print("palette:", swatch)
    print("shrunk:", target)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            import shrink_selftest
        except ImportError:
            print("error: --selftest needs shrink_selftest.py beside this file", file=sys.stderr)
            sys.exit(2)
        sys.exit(0 if shrink_selftest.run() else 1)
    sys.exit(main(sys.argv[1:]))
