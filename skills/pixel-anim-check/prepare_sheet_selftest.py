"""prepare_sheet.py's own test: a 10-frame idle drawn at game size is blown up 6 times onto a 5x2 sheet on a green
key, each pose at its own place in its cell, the way an image model lays one out. Brought back, the frames match the
game-size originals; a pose drawn bigger keeps its own scale and still comes back; a soft (resampled) sheet with a
green fringe comes back nearly whole; a spark alone in a gap makes no cell of its own.

    python prepare_sheet_selftest.py        (or: python prepare_sheet.py --selftest)
"""
import contextlib
import io
import json
import os
import random
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pixel_anim_check as pac  # noqa: E402
import pixel_anim_selftest as st  # noqa: E402
import prepare_sheet as ps  # noqa: E402

N, Z, KEY = 10, 6, (2, 201, 90)
CELL_W, CELL_H = 300, 360


def _rgba(frame):
    a = np.zeros((len(frame), len(frame[0]), 4), np.uint8)
    for y, r in enumerate(frame):
        for x, v in enumerate(r):
            if v is not None:
                a[y, x] = pac.hexrgb(v) + (255,)
    return a


def _sheet(frames, big=(), soft=False, spark=False):
    """frames laid out 5 by 2 at Z times, each at a random place in its cell; poses in big drawn 15 % larger."""
    rnd = random.Random(7)
    sheet = Image.new("RGB", (5 * CELL_W, 2 * CELL_H), KEY)
    for k, f in enumerate(frames):
        im = Image.fromarray(_rgba(f), "RGBA")
        z = Z * (1.15 if k in big else 1)
        im = im.resize((round(im.width * z), round(im.height * z)), Image.BILINEAR if soft else Image.NEAREST)
        x = (k % 5) * CELL_W + rnd.randrange(10, CELL_W - im.width - 10)
        y = (k // 5) * CELL_H + rnd.randrange(10, CELL_H - im.height - 10)
        sheet.paste(im, (x, y), im)
    if spark:                                             # a spark in the gap between the first two cells
        sheet.paste((255, 244, 160), (CELL_W - 4, 150, CELL_W + 2, 156))
    return np.array(sheet.convert("RGBA"))


def _same(a, b):
    """The share of pixels two frame stacks agree on (air with air, or the same colour)."""
    ga, gb = a[..., 3] > 0, b[..., 3] > 0
    agree = (ga == gb) & (~ga | (a[..., :3] == b[..., :3]).all(-1))
    return float(agree.mean())


def run():
    ok = True

    def case(name, cond, got=""):
        nonlocal ok
        print(f"prepare  {name:58s} {'ok' if cond else 'WRONG'}" + ("" if cond else f"  ({got})"))
        ok &= bool(cond)

    frames = [st.face_frame(k, N) for k in range(N)]
    truth = np.stack([_rgba(f) for f in frames])
    ref = _rgba(frames[0])
    air, _ = ps._air(_sheet(frames))
    case("the grid is found: 10 cells, row by row", len(ps.cells(air)) == 10 and ps.cells(air)[1][1] > ps.cells(
        air)[0][1] and ps.cells(air)[5][0] > ps.cells(air)[0][0], ps.cells(air))
    out, log = ps.prepare(_sheet(frames), ref)
    case("a crisp sheet comes back pixel for pixel", _same(out, truth) == 1.0, _same(out, truth))
    case("its palette is the drawing's own colours", "drawing's own" in log["palette"], log["palette"])
    out, log = ps.prepare(_sheet(frames, big={3}), ref)
    own = [k for k, c in enumerate(log["cells"]) if c["own_scale"]]
    case("a pose drawn 15 % larger keeps its own scale", own == [3], own)
    case("and still comes back mostly whole (90 %)", _same(out[3:4], truth[3:4]) >= 0.90, _same(out[3:4], truth[3:4]))
    out, _ = ps.prepare(_sheet(frames, soft=True), ref)
    case("a soft sheet with a green fringe comes back nearly whole (95 %)", _same(out, truth) >= 0.95,
         _same(out, truth))
    air, _ = ps._air(_sheet(frames, spark=True))
    case("a spark alone in a gap makes no cell of its own", len(ps.cells(air)) == 10, len(ps.cells(air)))

    with tempfile.TemporaryDirectory() as d:
        sheet, drawing = os.path.join(d, "sheet.png"), os.path.join(d, "face.png")
        Image.fromarray(_sheet(frames)[..., :3], "RGB").save(sheet)
        Image.fromarray(ref, "RGBA").save(drawing)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = ps.main([sheet, "--ref", drawing, "--grid", "5x2", "--out", d, "--name", "face"])
            no_ref = ps.main([sheet, "--out", d])
        strip = pac.load(os.path.join(d, "face_strip.png"), frame=ref.shape[1])
        with open(os.path.join(d, "face_prepare.json"), encoding="utf-8") as fh:
            logged = json.load(fh)
        case("--grid 5x2 on the command line writes the strip and the log", code == 0 and strip == frames
             and len(logged["cells"]) == 10, code)
        case("no --ref is a usage error", no_ref == 2, no_ref)
    print("selftest:", "all hold" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
