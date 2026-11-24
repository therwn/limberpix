"""Build the gallery pictures in docs/img/gallery from the examples, with the repo's own tools.

    python examples/showcase/make_gallery.py            # writes docs/img/gallery/*
    python examples/showcase/make_gallery.py --out DIR  # writes them to DIR instead

  <creature>_<loop>.gif   each showcase creature's idle, move and attack on its own, 30 fps, 2x
  walker_*.gif, flier_*.gif, broken_move.gif   the selftest's two creatures and the broken walk, 4x
  pipeline.png   the beast's drawing, rig at rest, one posed part frame and its matching finished frame
  workflow.gif   that pipeline in motion, followed by a walk with a shifted frame and the check's result after repair
  faults.png     four things pixel_anim_check catches, each made by breaking the beast's own frames and run through
                 the real check: the line under each tile is what it printed

Every word in the pictures is pixfont.py. Run a creature's animate.py first if its strips changed. The pictures are
not checked by CI: rebuild them after changing a creature or a fault's wording."""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "skills", "pixel-anim-check"))
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


# ---- pipeline.png and workflow.gif --------------------------------------------------------------------------------
DEMO_WIDTH, DEMO_HEIGHT = 456, 170
DEMO_MARGIN = 12
DEMO_TILE_HEIGHT = 58


def demo_card(title, subtitle):
    im = st.card(DEMO_WIDTH, DEMO_HEIGHT, radius=10)
    st.put(im, DEMO_MARGIN, 12, title, st.TEXT, 2)
    st.put(im, DEMO_MARGIN, 34, subtitle, st.MUTED, 1)
    return im


def pipeline_card(drawing, rest, parts, frame):
    im = demo_card("pixel-animate", "Pose the parts from one drawing to build every frame.")
    tile_width, gap, top = 102, 8, 58
    steps = (("1 Drawing", drawing), ("2 Rig at rest", rest),
             ("3 Posed parts", parts), ("4 Final frame", frame))
    for i, (label, sprite) in enumerate(steps):
        x = DEMO_MARGIN + i * (tile_width + gap)
        im.alpha_composite(rounded(tile(sprite, size=(tile_width, DEMO_TILE_HEIGHT)), radius=4), (x, top))
        st.put(im, x + tile_width // 2, 126, label, st.TEXT, 1, centre=True)
        if i < len(steps) - 1:
            st.put(im, x + tile_width + gap // 2, top + DEMO_TILE_HEIGHT // 2, ">", st.MUTED, 1, centre=True)
    st.put(im, DEMO_MARGIN, 147, "Same part colours", st.TEXT, 1)
    st.put(im, 146, 147, "Green: near hind leg, from hip to paw", (80, 208, 96), 1)
    return im


def check_card(broken, fixed, fault_count, diagnostic, at_fault):
    im = demo_card("pixel-anim-check", "Shift one walk frame 4 px sideways, then put it back.")
    tile_width, top = 208, 61
    panels = (("Shifted walk", broken, st.RED), ("Restored walk", fixed, st.GREEN))
    for i, (label, sprite, colour) in enumerate(panels):
        x = DEMO_MARGIN + i * (tile_width + 16)
        st.put(im, x, 48, label, colour, 1)
        im.alpha_composite(rounded(tile(sprite, size=(tile_width, DEMO_TILE_HEIGHT)), radius=4), (x, top))
        if at_fault:
            ImageDraw.Draw(im).rounded_rectangle((x, top, x + tile_width - 1, top + DEMO_TILE_HEIGHT - 1),
                                                 radius=4, outline=colour, width=2)
        count = fault_count if i == 0 else 0
        lines = [[(f"beast: {count} fault(s)", st.TEXT), (f">exit {int(bool(count))}", colour)]]
        if i == 0:
            lines += [[(line, colour)] for line in wrap(diagnostic, (tile_width - 12) // pixfont.CELL_W)]
        im.alpha_composite(st.terminal(lines, tile_width, scale=1, pad=6, pitch=10), (x, 126))
    return im


def workflow_images(out, clean, spec):
    """The part-strip colours and sprite frames come from the same rig and share one frame box."""
    drawing = ms.rgba(spec.ref)
    rest = ms.rgba(spec.parts["idle"][0])
    walk = [ms.rgba(f) for f in clean["move"]]
    parts = [ms.rgba(f) for f in spec.parts["move"]]
    if len(parts) != len(walk) or any(not np.array_equal(p[..., 3], f[..., 3]) for p, f in zip(parts, walk)):
        sys.exit("workflow: the wolf's part strip and walk do not match")

    still = pipeline_card(drawing, rest, parts[10], walk[10])
    still_path = os.path.join(out, "pipeline.png")
    still = Image.fromarray(ms.up(np.asarray(still), 2))
    still.save(still_path, optimize=True)

    modified = _copy(clean)
    loop, fault_frame = knock(modified, ms.CREATURES["beast"])
    faults = pac.check(modified, spec)
    diagnostic = next((line for line in faults if line.startswith(f"jump: {loop}[{fault_frame}] ")), None)
    if diagnostic is None:
        sys.exit(f"workflow: the shifted frame did not give the expected jump fault: {faults}")

    matte = Image.new("RGBA", (DEMO_WIDTH, DEMO_HEIGHT), ms.OUTSIDE)
    frames = []
    for part_frame, sprite in zip(parts, walk):
        panel = pipeline_card(drawing, rest, part_frame, sprite)
        frames.extend([np.asarray(Image.alpha_composite(matte, panel).convert("RGB"))] * 3)
    for i, sprite in enumerate(walk):
        at_fault = i == fault_frame
        broken = ms.rgba(modified[loop][i]) if at_fault else sprite
        panel = check_card(broken, sprite, len(faults), diagnostic, at_fault)
        frames.extend([np.asarray(Image.alpha_composite(matte, panel).convert("RGB"))] * (27 if at_fault else 3))
    gif = ms.write_gif(os.path.join(out, "workflow.gif"), frames, 2)
    return still.size, gif


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
    clean, spec = ms.loops("beast"), ms.spec("beast")
    for key in ms.CREATURES:                               # the same gate as make_showcase: every loop clean
        faults = pac.check(clean, spec) if key == "beast" else pac.check(ms.loops(key), ms.spec(key))
        if faults:
            sys.exit(f"{key}: {len(faults)} fault(s): {faults[0]}")
    for name, size, n, total in loop_gifs(args.out):
        print(f"{name:20s} {size[0]}x{size[1]}  {n} images  {total} ms")
    still_size, (size, n, total) = workflow_images(args.out, clean, spec)
    print("pipeline.png", still_size)
    print(f"{'workflow.gif':20s} {size[0]}x{size[1]}  {n} images  {total} ms")
    size, cases = faults_png(os.path.join(args.out, "faults.png"))
    print("faults.png", size)
    for title, kind, lines in cases:
        print(f"  {title}: {kind}: {' '.join(lines)}")


if __name__ == "__main__":
    main(sys.argv[1:])
