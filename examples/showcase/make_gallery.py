"""Build the gallery pictures in docs/img/gallery from the examples, with the repo's own tools.

    python examples/showcase/make_gallery.py            # writes docs/img/gallery/*
    python examples/showcase/make_gallery.py --out DIR  # writes them to DIR instead

  <creature>_<loop>.gif   each showcase creature's idle, move and attack on its own, 30 fps, 2x
  walker_*.gif, flier_*.gif, broken_move.gif   the selftest's two creatures and the broken walk, 4x
  pipeline.png   pixel-animate in four steps on the beast: the drawing, body_parts.py's cut, one pose as flat parts
                 (the part strip), the same pose as the finished frame
  faults.png     four things pixel_anim_check catches, each made by breaking the beast's own frames and run through
                 the real check: the line under each tile is what it printed

Every word in the pictures is pixfont.py. Run a creature's animate.py first if its strips changed. The pictures are
not checked by CI: rebuild them after changing a creature or a fault's wording."""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "skills", "pixel-anim-check"))
sys.path.insert(0, os.path.join(ROOT, "skills", "pixel-animate"))
import body_parts as bp                                   # noqa: E402
import make_showcase as ms                                # noqa: E402
import pixel_anim_check as pac                            # noqa: E402
import pixfont                                            # noqa: E402
import showcase_stills as st                              # noqa: E402

GROUND = (54, 48, 70)


def tile(frame_rgba, pad=3, ground=True, size=None):
    """A frame on the gallery's tile ground, as an RGB array at game px. With size=(w, h) the tile is that size
    (pad included), the frame centred across it and standing on its bottom edge, so loops of creatures of different
    sizes come out as tiles of one size."""
    h, w = frame_rgba.shape[:2]
    tw, th = size if size else (w + 2 * pad, h + 2 * pad)
    t = np.zeros((th, tw, 3), np.uint8)
    t[:] = st.TILE
    x, y = (tw - w) // 2, th - pad - h
    if ground:
        t[y + h:] = GROUND
    ms.paste(t, frame_rgba, x, y)
    return t


def common(sizes, pad=3):
    """One tile size (w, h) holding every frame size given, with pad round the biggest."""
    return max(w for w, _ in sizes) + 2 * pad, max(h for _, h in sizes) + 2 * pad


def rounded(img_rgb, radius=14):
    """An RGB array as an RGBA image with rounded corners."""
    t = Image.fromarray(img_rgb).convert("RGBA")
    mask = Image.new("L", t.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, t.width - 1, t.height - 1), radius, fill=255)
    t.putalpha(mask)
    return t


# ---- loop GIFs ----------------------------------------------------------------------------------------------------
def loop_gifs(out):
    """Every showcase loop on one tile size, and every selftest loop on another: the GIFs sit in tables, where
    tiles of different sizes read as untidy. Each creature keeps its own scale (2x, 4x): a pixel-art frame is only
    ever scaled by whole numbers, so the tiles are padded, not stretched."""
    done = []
    show = {k: ms.loops(k) for k in ms.CREATURES}
    size = common([(len(L["idle"][0][0]), len(L["idle"][0])) for L in show.values()])
    for key, c in ms.CREATURES.items():
        for a in ms.LOOPS:
            frames = [tile(ms.rgba(f), ground=not c.get("flier", False), size=size) for f in show[key][a]]
            px, n, ms_total = ms.write_gif(os.path.join(out, f"{key}_{a}.gif"), frames, 2)
            done.append((f"{key}_{a}.gif", px, n, ms_total))
    small = [(name, fw, flier, pac.load(os.path.join(ROOT, "examples", f"{name}.png"), frame=fw))
             for name, fw, flier in (("walker_idle", 34, False), ("walker_move", 34, False),
                                     ("broken_move", 34, False), ("flier_idle", 30, True), ("flier_move", 30, True))]
    size = common([(len(fr[0][0]), len(fr[0])) for _, _, _, fr in small])
    for name, fw, flier, fr in small:
        frames = [tile(ms.rgba(f), ground=not flier, size=size) for f in fr]
        px, n, ms_total = ms.write_gif(os.path.join(out, f"{name}.gif"), frames, 4)
        done.append((f"{name}.gif", px, n, ms_total))
    return done


# ---- pipeline.png -------------------------------------------------------------------------------------------------
POSE = 10                                                 # the beast's move frame shown as parts and as a frame


def part_tint():
    """The beast's drawing at game px, and the same pixels tinted by the part body_parts.py gave each to."""
    src = os.path.join(HERE, "beast", "beast_art_8x.png")
    with open(os.path.join(HERE, "beast", "marks.json"), encoding="utf-8") as fh:
        marks = json.load(fh)
    drawing = Image.open(src)
    res, aux = bp.analyse(drawing, marks)
    if res["warnings"]:
        sys.exit(f"pipeline: body_parts printed CHECK lines: {res['warnings']}")
    k = 8
    lab8 = bp.full_labels(aux, drawing.size)
    art = np.asarray(drawing.convert("RGBA"))[k // 2::k, k // 2::k]
    h, w = art.shape[:2]
    names = aux["names"]
    inside = {p["name"]: p.get("inside") for p in res["parts"]}
    tint = np.zeros((h, w, 4), np.uint8)
    grey = art[..., :3].astype(float).mean(-1) / 255.0
    for y in range(h):
        for x in range(w):
            if art[y, x, 3]:
                b = lab8[y * k:(y + 1) * k, x * k:(x + 1) * k].ravel()
                b = b[b >= 0]
                if not len(b):
                    continue
                n = names[int(np.bincount(b).argmax())]
                col = np.array(st.PART_COLOURS[inside[n] or n], float) * (0.34 + 1.1 * grey[y, x])
                tint[y, x] = tuple(np.clip(col, 0, 255).astype(np.uint8)) + (255,)
    return art, tint, len(names)


def pipeline_png(path, S=4):
    key, c = "beast", ms.CREATURES["beast"]
    L = ms.loops(key)
    art, tint, n_parts = part_tint()
    parts = pac.load(ms.path(key, f"check/{key}_move_parts.png"), frame=c["frame"])
    flat, frame = ms.rgba(parts[POSE]), ms.rgba(L["move"][POSE])
    def box(arr):                                         # each picture cut to its own figure, then set on one
        ys, xs = np.nonzero(arr[..., 3])                  # canvas, feet on one line (the drawing's canvas is not
        return arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]   # the loops')

    cut = [box(v) for v in (art, tint, flat, frame)]
    bh, bw = max(v.shape[0] for v in cut), max(v.shape[1] for v in cut)

    def seat(arr):
        out = np.zeros((bh, bw, 4), np.uint8)
        h, w = arr.shape[:2]
        out[bh - h:, (bw - w) // 2:(bw - w) // 2 + w] = arr
        return out

    art, tint, flat, frame = (seat(v) for v in cut)
    x0, x1, y0, y1 = 0, bw, 0, bh
    steps = [("1", "the drawing", "one approved drawing", art),
             ("2", "the cut", f"body_parts.py: {n_parts} parts", tint),
             ("3", "a pose, as parts", "each part moved whole px", flat),
             ("4", "the frame", "the drawing's own pixels", frame)]
    tw, th = (x1 - x0 + 6) * S, (y1 - y0 + 6) * S
    M, gap = 48, 56
    W = 2 * M + len(steps) * tw + (len(steps) - 1) * gap
    H = st.TOP + th + 110
    im = st.card(W, H)
    st.heading(im, "pixel-animate", "One drawing, cut once, posed for every frame. Nothing is redrawn.")
    d = ImageDraw.Draw(im)
    x = M
    for i, (num, title, sub, arr) in enumerate(steps):
        t = rounded(ms.up(tile(arr[y0:y1, x0:x1]), S))
        im.alpha_composite(t, (x, st.TOP))
        st.put(im, x + tw / 2, st.TOP + th + 30, f"{num}  {title}", st.TEXT, 3, centre=True)
        st.put(im, x + tw / 2, st.TOP + th + 66, sub, st.MUTED, 2, centre=True)
        if i < len(steps) - 1:
            ax0, ax1, ay = x + tw + 12, x + tw + gap - 12, st.TOP + th // 2
            d.line((ax0, ay, ax1 - 4, ay), fill=st.MUTED, width=3)
            d.polygon([(ax1, ay), (ax1 - 12, ay - 8), (ax1 - 12, ay + 8)], fill=st.MUTED)
        x += tw + gap
    im.save(path, optimize=True)
    return im.size


# ---- faults.png ---------------------------------------------------------------------------------------------------
def _copy(L):
    return {a: [[list(r) for r in f] for f in fr] for a, fr in L.items()}


def knock(L, c):
    """One walk pose moved 4 px sideways."""
    k = 9
    f = L["move"][k]
    L["move"][k] = [[None] * 4 + r[:-4] for r in f]
    return "move", k


def speck(L, c):
    """Three loose pixels beside the figure on one idle pose."""
    k = 6
    f = L["idle"][k]
    fur = next(v for r in f for v in r if v is not None and v not in c["ink"])
    ys = [y for y, r in enumerate(f) if any(v is not None for v in r)]
    y = ys[len(ys) // 3]
    x = max(i for i, v in enumerate(f[y]) if v is not None) + 5
    f[y][x] = f[y][x + 1] = f[y + 1][x] = fur
    return "idle", k


def off_palette(L, c):
    """A patch of one walk pose in a tone the drawing does not hold."""
    k = 12
    f = L["move"][k]
    ys = [y for y, r in enumerate(f) if any(v is not None for v in r)]
    y0 = ys[len(ys) // 2] - 2
    xs = [i for i, v in enumerate(f[y0]) if v is not None]
    xm = xs[len(xs) // 2]
    for y in range(y0, y0 + 4):
        for x in range(xm - 3, xm + 3):
            if f[y][x] is not None and f[y][x] not in c["ink"]:
                f[y][x] = "#d05a96"
    return "move", k


def lifted(L, c):
    """One idle pose lifted 2 px off the ground."""
    k = 20
    f = L["idle"][k]
    L["idle"][k] = f[2:] + [[None] * len(f[0]) for _ in range(2)]
    return "idle", k


CASES = (("A POSE KNOCKED SIDEWAYS", "jump", knock), ("A STRAY SPECK", "apart", speck),
         ("A COLOUR OFF THE PALETTE", "palette", off_palette), ("FEET OFF THE GROUND", "ground", lifted))


def wrap(text, n):
    out, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > n and line:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    return out + [line]


def faults_png(path, S=3):
    key, c = "beast", ms.CREATURES["beast"]
    clean = ms.loops(key)
    sp = ms.spec(key)
    if pac.check(clean, sp):
        sys.exit("faults: the beast as drawn has a fault")
    alpha = np.any([ms.rgba(f)[..., 3] > 0 for a in ("idle", "move") for f in clean[a]], 0)
    ys, xs = np.nonzero(alpha)
    x0, x1, y0, y1 = max(0, xs.min() - 6), min(alpha.shape[1], xs.max() + 12), max(0, ys.min() - 3), ys.max() + 1
    pad = 3
    tw, th = (x1 - x0 + 2 * pad) * S, (y1 - y0 + 2 * pad) * S
    M, gap, col_gap = 48, 16, 48
    cw = 2 * tw + gap                                       # a case's width: the pose as drawn, the pose broken
    chars = (cw - 36) // (pixfont.CELL_W * 2)
    built = []
    for title, kind, breaker in CASES:
        L = _copy(clean)
        loop, k = breaker(L, c)
        faults = pac.check(L, sp)
        hit = [ln for ln in faults if ln.startswith(kind + ":")]
        if not hit:
            sys.exit(f"faults: {title} did not give {kind}: {faults[:3]}")
        text = hit[0].split(":", 1)[1].strip()
        first = wrap(text, chars - len(kind) - 4)[0]      # the first line shares its row with the fault's name
        rest = wrap(text[len(first):].strip(), chars - 4) if len(text) > len(first) else []
        lines = [first] + rest[:2]
        if len(rest) > 2:
            lines[-1] = lines[-1][:chars - 8].rstrip() + " ..."
        built.append((title, kind, loop, k, L, lines, len(faults)))
    term_h = max(st.terminal([[("x", st.TEXT)]] * (1 + len(b[5])), 10, scale=2, pad=18, pitch=24).height for b in built)
    row_h = 54 + th + 40 + term_h + 44
    W = 2 * M + 2 * cw + col_gap
    H = st.TOP + 2 * row_h
    im = st.card(W, H)
    st.heading(im, "pixel-anim-check", "Four of the faults it names. Each line is what the check printed.")
    d = ImageDraw.Draw(im)
    for i, (title, kind, loop, k, L, lines, n_faults) in enumerate(built):
        x, y = M + (i % 2) * (cw + col_gap), st.TOP + (i // 2) * row_h
        pw = pixfont.width(title, 2) + 28
        d.rounded_rectangle((x, y, x + pw, y + 34), 17, fill=st.RED)
        st.put(im, x + pw / 2, y + 17, title, st.BG, 2, centre=True)
        y += 54
        a, b = ms.rgba(clean[loop][k]), ms.rgba(L[loop][k])
        for j, (arr, label, colr) in enumerate(((a, f"{loop} {k}, as drawn", st.MUTED), (b, "broken", st.RED))):
            t = rounded(ms.up(tile(arr[y0:y1, x0:x1], pad), S))
            tx = x + j * (tw + gap)
            im.alpha_composite(t, (tx, y))
            st.put(im, tx + tw / 2, y + th + 20, label, colr, 2, centre=True)
            if j == 1:
                d.rounded_rectangle((tx - 5, y - 5, tx + tw + 4, y + th + 4), 18, outline=st.RED, width=3)
                ch = (a != b).any(-1)[y0:y1, x0:x1]
                cy, cx = np.nonzero(ch)
                if len(cy) and (cx.max() - cx.min()) < 14 and (cy.max() - cy.min()) < 14:   # a small fault: ring it
                    ex = tx + (pad + (cx.min() + cx.max() + 1) / 2) * S
                    ey = y + (pad + (cy.min() + cy.max() + 1) / 2) * S
                    r = (max(cx.max() - cx.min(), cy.max() - cy.min()) / 2 + 4) * S
                    d.ellipse((ex - r, ey - r, ex + r, ey + r), outline=st.RED, width=3)
        y += th + 40
        runs = [[(f"{key}: {n_faults} fault(s)", st.TEXT), (">exit 1", st.RED)], [("  " + kind + ":", st.RED)]]
        runs[1].append((" " + lines[0], st.TEXT))
        runs += [[("    " + ln, st.TEXT)] for ln in lines[1:]]
        term = st.terminal(runs, cw, scale=2, pad=18, pitch=24)
        im.alpha_composite(term, (x, y))
    im.save(path, optimize=True)
    return im.size, [(b[0], b[1], b[5]) for b in built]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "img", "gallery"),
                    help="where the pictures go (default: docs/img/gallery)")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    for key in ms.CREATURES:                               # the same gate as make_showcase: every loop clean
        faults = pac.check(ms.loops(key), ms.spec(key))
        if faults:
            sys.exit(f"{key}: {len(faults)} fault(s): {faults[0]}")
    for name, size, n, total in loop_gifs(args.out):
        print(f"{name:20s} {size[0]}x{size[1]}  {n} images  {total} ms")
    print("pipeline.png", pipeline_png(os.path.join(args.out, "pipeline.png")))
    size, cases = faults_png(os.path.join(args.out, "faults.png"))
    print("faults.png", size)
    for title, kind, lines in cases:
        print(f"  {title}: {kind}: {' '.join(lines)}")


if __name__ == "__main__":
    main(sys.argv[1:])
