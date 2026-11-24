"""shrink.py's tests: python shrink_selftest.py (or python shrink.py --selftest). Needs shrink.py beside it.

A small creature is drawn at game size, blown up as a reference would be, and brought back; each rule of the shrink
is then checked on a case made for it, and the command line on files in a temporary folder."""
import contextlib
import io
import os
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shrink as sh                                       # noqa: E402

INK, FUR, BELLY, LIGHT, EYE, HORN = (18, 15, 25), (168, 116, 78), (216, 176, 136), (240, 216, 176), (255, 204, 51), \
    (90, 106, 138)
W, H = 24, 16


def creature():
    """A four-legged creature 24 x 16 with a one-pixel near-black outline: (rgba, palette, palette indices)."""
    g = [[None] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if ((x - 10.5) / 7.5) ** 2 + ((y - 7.5) / 3.6) ** 2 <= 1:
                g[y][x] = BELLY if y > 8 else FUR
            if ((x - 18.5) / 3.2) ** 2 + ((y - 5.0) / 2.8) ** 2 <= 1:
                g[y][x] = FUR
    for x0 in (5, 8, 13, 16):                             # legs
        for y in range(10, 14):
            g[y][x0] = g[y][x0 + 1] = FUR
    for k in range(4):                                    # tail, a horn, a light on the back, the eye
        g[6 - k][3 - min(k, 2)] = FUR
    g[2][19] = g[1][20] = HORN
    g[5][9] = g[5][10] = g[5][11] = LIGHT
    g[5][20] = EYE
    out = [r[:] for r in g]
    for y in range(H):                                    # the outline: air beside the figure
        for x in range(W):
            if g[y][x] is None and any(0 <= x + a < W and 0 <= y + b < H and g[y + b][x + a] is not None
                                       for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = INK
    rgba = np.zeros((H, W, 4), np.uint8)
    for y in range(H):
        for x in range(W):
            if out[y][x] is not None:
                rgba[y, x] = out[y][x] + (255,)
    pal = sh.ordered(rgba[..., :3][rgba[..., 3] > 0])
    idx = np.where(rgba[..., 3] > 0, sh.snap(rgba[..., :3], pal), -1)
    return rgba, pal, idx


def blown(rgba, size, flt):
    """rgba resized to size (w, h) with a Pillow filter, colour premultiplied so air does not bleed into it."""
    pm = rgba.astype(float)
    pm[..., :3] *= pm[..., 3:4] / 255
    big = np.asarray(Image.fromarray(pm.round().astype(np.uint8)).resize(size, flt)).astype(float)
    big[..., :3] = np.clip(big[..., :3] / (np.maximum(big[..., 3:4], 1) / 255), 0, 255)
    return big.round().astype(np.uint8)


def mean_then_snap(ref, pal, size):
    """The obvious wrong way, for comparison: average each cell, then snap the average to the palette."""
    w, h = size
    s = ref.shape[1] // w
    f = ref.astype(float)
    al = f[..., 3:4] / 255
    am = al.reshape(h, s, w, s).mean((1, 3))
    rgb = (f[..., :3] * al).reshape(h, s, w, s, 3).mean((1, 3)) / np.maximum(am[..., None], 1e-6)
    return np.where(am >= sh.COVER, sh.snap(rgb.round().astype(np.uint8), pal), -1)


def block(cols, w=8, h=8):
    """A reference of solid w x h cells from rows of colours (None: air)."""
    out = np.zeros((len(cols) * h, len(cols[0]) * w, 4), np.uint8)
    for y, row in enumerate(cols):
        for x, c in enumerate(row):
            if c is not None:
                out[y * h:(y + 1) * h, x * w:(x + 1) * w] = tuple(c) + (255,)
    return out


def run():
    ok = True

    def case(name, cond, got=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"shrink  {name:62s} {'ok' if cond else 'WRONG'}" + ("" if cond else f"  ({got})"))

    rgba, pal, truth = creature()

    # the round trip: a drawing blown up in solid cells comes back the same, whole and fractional cells alike
    for cell in (8, 7.5, 3):
        size = (round(W * cell), round(H * cell))
        got = sh.shrink(blown(rgba, size, Image.NEAREST), pal, (W, H))
        case(f"a drawing blown up {cell:g} times in solid cells comes back the same", (got == truth).all(),
             int((got != truth).sum()))
    big = blown(rgba, (W * 8, H * 8), Image.NEAREST)
    got = sh.shrink(big, pal, (W, H))
    img = np.asarray(sh.to_image(got, pal))
    cols = {tuple(c) for c in img[..., :3][img[..., 3] > 0]}
    case("the shrunk frame holds palette colours only", cols <= {tuple(c) for c in pal}, cols)

    # a soft reference (the drawing blown up with a smoothing filter) still comes back
    soft = blown(rgba, (W * 8, H * 8), Image.LANCZOS)
    drawn = int((truth >= 0).sum())
    wrong = int((sh.shrink(soft, pal, (W, H)) != truth).sum()) / drawn
    case("a drawing blown up 8 times with a smoothing filter comes back the same", wrong == 0, f"{wrong:.1%} wrong")

    # the vote against the average: a cell three fifths light, two fifths dark, a mid tone in the palette
    light, mid_tone, dark_tone = (240, 216, 176), (168, 138, 110), (90, 60, 50)
    ref = np.zeros((10, 10, 4), np.uint8)
    ref[..., 3] = 255
    ref[:, :6, :3] = light
    ref[:, 6:, :3] = dark_tone
    p3t = sh.ordered([light, mid_tone, dark_tone])
    voted = tuple(p3t[sh.shrink(ref, p3t, (1, 1))[0, 0]])
    averaged = tuple(p3t[mean_then_snap(ref, p3t, (1, 1))[0, 0]])
    case("a cell of two tones takes the commoner one", voted == light, voted)
    case("where its average would snap to a third tone the cell does not hold", averaged == mid_tone, averaged)

    # coverage first
    ref = np.zeros((10, 20, 4), np.uint8)
    ref[:4, :10] = FUR + (255,)                           # the left cell 40 % covered, the right one empty
    p2 = sh.ordered([FUR, BELLY])
    case("a cell 40 % covered is air at the default cover (0.42)", sh.shrink(ref, p2, (2, 1))[0, 0] == -1)
    case("and is drawn with --cover 0.3", sh.shrink(ref, p2, (2, 1), cover=0.3)[0, 0] == 0)
    ref = np.zeros((3, 7, 4), np.uint8)
    ref[:, 0] = FUR + (255,)
    left = sh.shrink(ref, p2, (3, 3))
    right = sh.shrink(ref[:, ::-1], p2, (3, 3))
    bottom = sh.shrink(ref.transpose(1, 0, 2)[::-1], p2, (3, 3))
    case("fractional cells preserve opposite edge columns and rows",
         (left >= 0).sum() == 3 and np.array_equal(right, left[:, ::-1]) and np.array_equal(bottom, left.T[::-1]),
         (left.tolist(), right.tolist(), bottom.tolist()))

    # the contour read apart: a dark line 3 px wide over fur, across two 8-px cells, 6 game px long
    ref = block([[FUR] * 4] * 6)
    ref[:, 14:17, :3] = INK                               # 2 px of it in cell 1, 1 px in cell 2
    p3 = sh.ordered([INK, FUR])
    with_line = sh.shrink(ref, p3, (4, 6))
    case("a line thinner than a cell is kept whole, one pixel wide", (with_line == 0).sum(1).tolist() == [1] * 6
         and len(set(np.argmax(with_line == 0, 1).tolist())) == 1, with_line.tolist())
    case("and is lost without the contour rule (--no-contour)", not (sh.shrink(ref, p3, (4, 6), contour=0) == 0).any())
    ref = block([[FUR] * 4] * 6)
    ref[:, 12:20, :3] = INK                               # a line one cell wide, half in cell 1 and half in cell 2
    wide = sh.shrink(ref, p3, (4, 6))
    case("a line a whole cell wide across two cells does not vanish", (wide == 0).sum(1).min() >= 1, wide.tolist())
    ref = np.empty((11, 44, 4), np.uint8)
    widths = []
    for start, width in ((17, 10), (18, 10), (11, 11), (11, 22)):
        ref[:] = FUR + (255,)
        ref[:, start:start + width] = INK + (255,)
        widths.append(int((sh.shrink(ref, p3, (4, 1)) == 0).sum()))
    case("thin contour stays one pixel thick when shifted", widths == [1, 1, 1, 2], widths)
    dark2 = (24, 20, 21)
    tones = sh.ordered([INK, dark2])
    ref[:, :22] = tuple(tones[0]) + (255,)
    ref[:, 22:] = tuple(tones[1]) + (255,)
    case("a contour tie uses the matching rest tone", sh.shrink(ref, tones, (1, 1), rest=np.array([[1]])).item() == 1)

    # a tie: the left half of the cell one colour, the right half another
    ref = np.zeros((8, 8, 4), np.uint8)
    ref[:, :4] = BELLY + (255,)
    ref[:, 4:] = FUR + (255,)
    first = sh.shrink(ref, p2, (1, 1))[0, 0]
    case("a tie goes to the first of the tied in the palette's order", first == 0 and (p2[0] == FUR).all(), first)
    case("and to the rest frame's colour when that is one of them",
         sh.shrink(ref, p2, (1, 1), rest=np.array([[1]]))[0, 0] == 1)
    case("the same reference gives the same frame every time",
         all((sh.shrink(soft, pal, (W, H)) == sh.shrink(soft, pal, (W, H))).all() for _ in range(2)))

    # a palette made from the reference
    made = sh.make_palette(soft, 6)
    in_ref = {tuple(c) for c in soft[..., :3][soft[..., 3] >= 128]}
    case("--colours N gives at most N colours, each one the reference holds",
         len(made) <= 6 and {tuple(c) for c in made} <= in_ref, len(made))
    case("one of them is the contour's", int(made[0].astype(int).sum()) < sh.CONTOUR, made[0].tolist())
    case("and the same reference gives the same palette", (made == sh.make_palette(soft, 6)).all())
    few = sh.make_palette(big, 40)
    case("a reference of few colours keeps its own", {tuple(c) for c in few} == {tuple(c) for c in pal}, len(few))

    for what, call in (("a game size larger than the reference", lambda: sh.shrink(big, pal, (W * 9, H))),
                       ("a rest frame of another size", lambda: sh.shrink(big, pal, (W, H), rest=np.zeros((3, 3), int)))):
        try:
            call()
            raised = False
        except ValueError:
            raised = True
        case(f"{what} is refused", raised)
    ok = cli(rgba, pal, truth, big) and ok
    print("selftest:", "all hold" if ok else "FAILED")
    return ok


def cli(rgba, pal, truth, big):
    ok = True

    def case(name, cond, got=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"cli     {name:62s} {'ok' if cond else 'WRONG'}" + ("" if cond else f"  ({got})"))

    def run_main(args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sh.main(args)
        return code, out.getvalue() + err.getvalue()

    def same(path):
        a = np.asarray(Image.open(path).convert("RGBA"))
        return a.shape == rgba.shape and (a == rgba).all()

    with tempfile.TemporaryDirectory() as tmp:
        ref, rest, out = (os.path.join(tmp, n) for n in ("ref.png", "rest.png", "out"))
        Image.fromarray(big).save(ref)
        Image.fromarray(rgba).save(rest)
        code, text = run_main([ref, "--size", f"{W},{H}", "--palette", rest, "--rest", rest, "--out", out, "--name", "a"])
        case("--size with --palette and --rest brings the drawing back", code == 0
             and same(os.path.join(out, "a_shrunk.png")), (code, text[-200:]))
        code, text = run_main([ref, "--scale", "8", "--palette", rest, "--out", out, "--name", "b"])
        case("--scale 8 gives the same frame", code == 0 and same(os.path.join(out, "b_shrunk.png")), (code, text[-200:]))
        code, text = run_main([ref, "--scale", "8", "--colours", "5", "--out", out, "--name", "c"])
        sw = os.path.join(out, "c_palette.png")
        case("--colours writes the frame and its palette", code == 0 and os.path.isfile(sw)
             and Image.open(sw).size[0] <= 5 and os.path.isfile(os.path.join(out, "c_shrunk.png")), (code, text[-200:]))
        code, text = run_main([ref, "--scale", "8", "--palette", sw, "--out", out, "--name", "d"])
        case("that palette file is taken by --palette", code == 0, (code, text[-200:]))
        solid = os.path.join(tmp, "solid.png")
        flat = big.copy()
        flat[flat[..., 3] == 0] = (255, 0, 255, 255)
        Image.fromarray(flat).convert("RGB").save(solid)
        code, text = run_main([solid, "--scale", "8", "--palette", rest, "--out", out])
        case("a reference with no transparency is a usage error naming --key", code == 2 and "--key" in text, (code, text))
        code, text = run_main([solid, "--scale", "8", "--palette", rest, "--key", "#FF00FF", "--out", out, "--name", "e"])
        case("--key reads that colour as air", code == 0 and same(os.path.join(out, "e_shrunk.png")), (code, text[-200:]))
        wrong = os.path.join(tmp, "wrong.png")
        Image.fromarray(rgba[:5, :5]).save(wrong)
        for name, args in (("neither --size nor --scale", [ref, "--palette", rest]),
                           ("--size and --scale together", [ref, "--size", "24,16", "--scale", "8", "--palette", rest]),
                           ("neither --palette nor --colours", [ref, "--scale", "8"]),
                           ("--palette and --colours together", [ref, "--scale", "8", "--palette", rest, "--colours", "5"]),
                           ("a missing reference", [os.path.join(tmp, "none.png"), "--scale", "8", "--colours", "5"]),
                           ("a missing palette", [ref, "--scale", "8", "--palette", os.path.join(tmp, "none.png")]),
                           ("a --size that is not W,H", [ref, "--size", "24", "--colours", "5"]),
                           ("a --size larger than the reference", [ref, "--size", "999,999", "--colours", "5"]),
                           ("a --cover that is no share", [ref, "--scale", "8", "--colours", "5", "--cover", "2"]),
                           ("a --colours that is no whole number", [ref, "--scale", "8", "--colours", "5.5"]),
                           ("a --key that is no colour", [ref, "--scale", "8", "--colours", "5", "--key", "pink"]),
                           ("a rest frame of another size", [ref, "--scale", "8", "--palette", rest, "--rest", wrong]),
                           ("--contour with --no-contour", [ref, "--scale", "8", "--colours", "5", "--contour", "70",
                                                           "--no-contour"]),
                           ("an unknown option", [ref, "--scale", "8", "--colours", "5", "--sharpen"]),
                           ("two references", [ref, ref, "--scale", "8", "--colours", "5"])):
            code, text = run_main(args + ["--out", out])
            case(f"{name} is a usage error (exit 2)", code == 2 and text.startswith("error:"), (code, text[:160]))
        code, text = run_main(["--help"])
        case("--help prints the help and exits 0", code == 0 and "--size" in text and "--colours" in text)
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
