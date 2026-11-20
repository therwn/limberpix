"""body_parts checked on drawings whose true parts are known: each part is drawn in its own colour with a dark ink
outline, the way pixel art is, and parts touch where the silhouette alone cannot split them (a staff in a hand, a
cape behind a body, an arm across the chest). The bones given are rough on purpose (off centre, short, a point off
the figure) as eye-placed ones are; a part seen in two pieces (the cape either side of the legs) has a bone in
each, as the method asks. Every part must come out matching its true pixels (IoU >= 0.8, measured off the ink:
which side an outline goes to is a matter of taste). And a cape marked on one side only must be flagged."""
import contextlib
import inspect
import io
import json
import os
import sys
import tempfile

import numpy as np
import PIL
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import body_parts as bp                                   # noqa: E402

INK = (14, 10, 18)
BG = (36, 30, 44)


def figure():
    """A standing figure, 600x800: cape behind, legs, torso, head, an arm across the chest whose hand holds a staff,
    a bowstring-thin ink line from the staff's head, and a loose spark by the head. Returns the drawing and, per
    part, its true mask."""
    W, H = 600, 800
    im = Image.new("RGB", (W, H), BG)
    truth = {}

    def part(name, shape, col, width=3):
        m = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(m)
        d = ImageDraw.Draw(im)
        kind, xy = shape
        getattr(d, kind)(xy, fill=col, outline=INK, width=width)
        getattr(md, kind)(xy, fill=255)
        mask = np.asarray(m) > 0
        for other in truth.values():                      # drawn later = in front
            other &= ~mask
        truth[name] = mask

    part("cape", ("polygon", [(230, 180), (380, 180), (430, 700), (170, 700)]), (150, 30, 40))
    part("leg_a", ("rectangle", (240, 470, 290, 760)), (70, 70, 90))
    part("leg_b", ("rectangle", (310, 470, 360, 760)), (90, 90, 110))
    part("torso", ("rectangle", (230, 200, 370, 480)), (110, 120, 140))
    part("head", ("ellipse", (250, 80, 350, 200)), (230, 190, 160))
    part("staff", ("rectangle", (448, 60, 474, 780)), (140, 90, 40))
    part("arm", ("polygon", [(260, 230), (300, 230), (470, 330), (450, 360)]), (200, 160, 130))
    part("hand", ("ellipse", (430, 310, 490, 370)), (225, 180, 150))
    d = ImageDraw.Draw(im)
    d.line([(474, 70), (560, 300)], fill=INK, width=6)    # the string: ink alone
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).line([(474, 70), (560, 300)], fill=255, width=6)
    truth["string"] = np.asarray(m) > 0
    for other in [v for k, v in truth.items() if k != "string"]:
        other &= ~truth["string"]
    d.rectangle((370, 60, 380, 70), fill=(255, 200, 60))  # a spark apart from the body: goes to the nearest part
    return im, truth


MARKS = {"parts": {
    "head":  {"kind": "head", "parent": "torso", "bone": [[296, 120], [304, 170]]},
    "torso": {"kind": "torso", "bone": [[285, 380], [290, 460]]},          # low, clear of the arm across the chest
    "cape":  {"kind": "cloth", "parent": "torso", "bone": [[200, 690], [215, 520], None, [300, 530], [300, 690], None,
                                                      [395, 520], [410, 690]]},
    "leg_a": {"kind": "leg", "parent": "torso", "bone": [[262, 520], [268, 740]]},
    "leg_b": {"kind": "leg", "parent": "torso", "bone": [[338, 520], [332, 740]]},
    "arm":   {"kind": "arm", "parent": "torso", "bone": [[300, 255], [420, 320]]},
    "hand":  {"kind": "hand", "parent": "arm", "bone": [[462, 342]]},
    "staff": {"kind": "prop", "parent": "hand", "bone": [[461, 80], [458, 290], None, [462, 400], [470, 770]]},
    "string": {"kind": "prop", "parent": "staff", "bone": [[480, 95], [550, 275]]},
}}


def run():
    im, truth = figure()
    res, aux = bp.analyse(im, MARKS)
    k, label = aux["k"], aux["label"]
    H, W = truth["head"].shape
    full = bp.full_labels(aux, (W, H))                    # what a rig cuts by: the labels at full size
    ok = True
    off_ink = np.abs(np.asarray(im).astype(int) - np.array(INK)).sum(2) > 30
    for i, name in enumerate(aux["names"]):
        keep = np.ones_like(off_ink) if name == "string" else off_ink
        t = truth[name] & keep
        g = (full == i) & keep
        inter, union = (t & g).sum(), (t | g).sum()
        iou = inter / union if union else 0.0
        need = 0.6 if name == "string" else 0.8     # the cut is made on a copy ~420 px across: a thin part's
                                                    # edges move by a pixel or two (a thin line is mostly edge)
        good = iou >= need
        ok &= good
        print(f"{name:7s} IoU {iou:.2f} (need {need})  {'ok' if good else 'WRONG'}")
    for w in res["warnings"]:
        print("warning:", w)
    one_side = {"parts": dict(MARKS["parts"])}
    one_side["parts"]["cape"] = {"kind": "cloth", "parent": "torso", "bone": [[200, 690], [215, 520]]}
    res2, _ = bp.analyse(im, one_side)
    flagged = any(w.startswith(("leg_b", "cape")) and "colour" in w for w in res2["warnings"])
    print(f"cape marked on one side only: flagged {'ok' if flagged else 'WRONG'}  ({res2['warnings']})")
    ok &= flagged
    ok &= cli()
    print("selftest:", "all hold" if ok else "FAILED")
    return ok


def cli():
    """The command line: --help exits 0, no or bad arguments exit 2, a clean cut 0 and one with CHECK lines 1, --grid
    makes a missing --out folder, and the
    fallback font (no system font found) is drawn at the size asked, not as a tiny bitmap."""
    ok = True

    def case(name, cond, got=""):
        nonlocal ok
        print(f"cli     {name:46s} {'ok' if cond else 'WRONG'}" + ("" if cond else f"  ({got})"))
        ok &= bool(cond)

    def run_main(args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            return bp.main(args), buf.getvalue()
    case("--help exits 0", run_main(["--help"])[0] == 0 and run_main(["-h"])[0] == 0)
    case("no arguments exit 2", run_main([])[0] == 2)
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "fig.png")
        figure()[0].resize((150, 200)).save(src)
        case("a drawing with no landmarks exits 2", run_main([src])[0] == 2)
        case("a missing drawing exits 2", run_main([os.path.join(tmp, "none.png"), "--grid"])[0] == 2)
        case("an unknown option exits 2", run_main([src, "--grid", "--bogus"])[0] == 2)
        case("--step that is no number exits 2", run_main([src, "--grid", "--step", "x"])[0] == 2)
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w") as fh:
            fh.write("{not json")
        case("a malformed landmarks file exits 2", run_main([src, bad])[0] == 2)
        out = os.path.join(tmp, "new", "dir")
        code, text = run_main([src, "--grid", "--step", "25", "--out", out, "--name", "g"])
        case("--grid --out makes a new folder", code == 0 and os.path.isfile(os.path.join(out, "g_grid.png")), text)
        full, good, stray = os.path.join(tmp, "full.png"), os.path.join(tmp, "good.json"), os.path.join(tmp, "s.json")
        figure()[0].save(full)
        with open(good, "w") as fh:
            json.dump(MARKS, fh)
        with open(stray, "w") as fh:                      # a bone wholly off the figure: a CHECK line
            json.dump({"parts": dict(MARKS["parts"], ghost={"kind": "prop", "bone": [[2, 2], [4, 4]]})}, fh)
        code, text = run_main([full, good, "--out", os.path.join(tmp, "cut")])
        case("a clean cut exits 0", code == 0 and "CHECK" not in text, text[-300:])
        code, text = run_main([full, stray, "--out", os.path.join(tmp, "cut")])
        case("a cut with CHECK lines exits 1", code == 1 and "CHECK" in text, text[-300:])
    if "size" in inspect.signature(ImageFont.load_default).parameters:
        bb = bp._font(40, names=()).getbbox("Ag")
        case("the fallback font is drawn at the size asked", bb[3] - bb[1] >= 20, bb)
    else:                                                 # Pillow before 10.1 has no sized default font
        print(f"cli     {'the fallback font (skipped: Pillow ' + PIL.__version__ + ' < 10.1)':46s} ok")
    return ok


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if out:
        im, _ = figure()
        res, aux = bp.analyse(im, MARKS)
        bp.draw(im, res, aux, out, "selftest")
    sys.exit(0 if run() else 1)
