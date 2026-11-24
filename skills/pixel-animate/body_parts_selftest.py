"""body_parts checked on drawings whose true parts are known: each part is drawn in its own colour with a dark ink
outline, the way pixel art is, and parts touch where the silhouette alone cannot split them (a staff in a hand, a
cape behind a body, an arm across the chest). The bones given are rough on purpose (off centre, short, a point off
the figure) as eye-placed ones are; a part seen in two pieces (the cape either side of the legs) has a bone in
each, as the method asks. Every part must come out matching its true pixels (IoU >= 0.8, measured off the ink:
which side an outline goes to is a matter of taste). And a cape marked on one side only must be flagged."""
import contextlib
import hashlib
from pathlib import Path
import shutil
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
    "leg_a": {"kind": "leg", "parent": "torso", "bone": [[262, 482], [268, 740]]},   # a joint end at its joint:
    "leg_b": {"kind": "leg", "parent": "torso", "bone": [[338, 482], [332, 740]]},   # the hip, the shoulder
    "arm":   {"kind": "arm", "parent": "torso", "bone": [[272, 234], [420, 320]]},
    "hand":  {"kind": "hand", "parent": "arm", "bone": [[462, 342]]},
    "staff": {"kind": "prop", "parent": "hand", "bone": [[461, 80], [458, 290], None, [462, 400], [470, 770]]},
    "string": {"kind": "prop", "parent": "staff", "bone": [[480, 95], [550, 275]]},
}}


# ---- creatures drawn the pixel-art way ----------------------------------------------------------------------------
# One fur ramp shaded by height runs across every part (no edge where a leg meets the body, bands of shading that
# cross the parts), ink only round the silhouette and between near and far limbs, a gap of background between the
# tail and the thigh, a head and neck of one fur, thin fingers side by side. Each figure: (image, truth, marks).
FIG_INK = (22, 18, 32)
FUR = [(214, 218, 236), (188, 194, 220), (160, 168, 200), (134, 144, 182), (110, 120, 162), (88, 98, 140),
       (70, 78, 118), (54, 60, 96), (42, 46, 78), (34, 36, 62)]
SKIN = [(250, 214, 180), (236, 192, 156), (214, 168, 134), (190, 144, 114), (164, 120, 96), (138, 98, 80),
        (112, 78, 64)]


def compose(W, H, layers, ramp, band, top, ink_pairs=()):
    """layers: (name, draw_fn, tone_shift) back to front; each pixel takes the ramp tone of its height (band px a
    step from top), shifted darker for far parts. Ink round the silhouette and where an ink pair meets."""
    owner = np.full((H, W), -1)
    shift = []
    for i, (name, fn, sh) in enumerate(layers):
        m = Image.new("L", (W, H), 0)
        fn(ImageDraw.Draw(m))
        owner[np.asarray(m) > 0] = i
        shift.append(sh)
    names = [l[0] for l in layers]
    rgba = np.zeros((H, W, 4), np.uint8)
    yy = np.mgrid[0:H, 0:W][0]
    for i in range(len(layers)):
        sel = owner == i
        idx = np.clip((yy - top) // band + shift[i], 0, len(ramp) - 1)
        col = np.array(ramp)[idx]
        rgba[sel, :3] = col[sel]
        rgba[sel, 3] = 255
    fig = owner >= 0
    pad = np.pad(fig, 1)
    edge = fig & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    pairs = [(names.index(a), names.index(b)) for a, b in ink_pairs]
    po = np.pad(owner, 1, constant_values=-1)
    for a, b in pairs:                                    # the front one's edge against the back one: inked
        nb_b = (po[:-2, 1:-1] == b) | (po[2:, 1:-1] == b) | (po[1:-1, :-2] == b) | (po[1:-1, 2:] == b)
        edge |= (owner == a) & nb_b
    rgba[edge, :3] = FIG_INK
    truth = {n: owner == i for i, n in enumerate(names)}
    return Image.fromarray(rgba, "RGBA"), truth


def beast():
    """A side-on wolf-like beast, 768x432 (a 96x54 sprite at 8x): one fur from back to paw."""
    def poly(pts):
        return lambda d: d.polygon(pts, fill=255)

    def ell(box):
        return lambda d: d.ellipse(box, fill=255)

    def both(*fns):
        return lambda d: [f(d) for f in fns]
    layers = [
        ("ear_far", poly([(478, 96), (488, 44), (504, 92)]), 2),
        ("hind_far", poly([(222, 290), (282, 290), (286, 334), (262, 364), (272, 410), (250, 414), (236, 364),
                           (224, 332)]), 2),
        ("front_far", poly([(356, 290), (394, 290), (392, 352), (398, 410), (376, 414), (372, 352), (358, 320)]), 2),
        ("tail", poly([(168, 178), (140, 172), (104, 196), (78, 258), (82, 330), (100, 348), (118, 334), (112, 266),
                       (126, 216), (160, 200)]), 0),
        ("torso", ell((146, 168, 432, 302)), 0),
        ("neck", poly([(384, 184), (432, 168), (478, 118), (512, 136), (500, 190), (468, 236), (422, 272)]), 0),
        ("hind_near", poly([(174, 286), (238, 286), (244, 330), (218, 362), (230, 406), (206, 414), (190, 362),
                            (178, 330)]), 0),
        ("front_near", poly([(392, 286), (434, 286), (430, 350), (438, 408), (414, 414), (408, 352), (394, 322)]), 0),
        ("head", both(ell((466, 78, 562, 154)),
                      poly([(540, 104), (612, 114), (612, 134), (544, 140)])), 0),
        ("jaw", poly([(546, 140), (606, 134), (600, 152), (552, 154)]), 1),
        ("ear_near", poly([(500, 92), (516, 36), (532, 90)]), 0),
    ]
    im, truth = compose(768, 432, layers, FUR, 34, 70,
                        ink_pairs=[("hind_near", "hind_far"), ("front_near", "front_far")])
    px = np.asarray(im).copy()                            # the rump's back edge in shadow, down the gap by the tail
    torso = truth["torso"]
    for y in range(206, 292):
        xs = np.nonzero(torso[y])[0]
        if len(xs):
            x0 = xs.min() + 2
            px[y, x0:x0 + 14, :3] = FUR[8]
    im = Image.fromarray(px, "RGBA")
    marks = {"parts": {
        "torso": {"kind": "torso", "bone": [[176, 232], [290, 236], [400, 230]]},
        "tail": {"kind": "tail", "parent": "torso", "bone": [[150, 190], [112, 214], [94, 270], [98, 330]]},
        "neck": {"kind": "neck", "parent": "torso", "bone": [[410, 210], [470, 150]]},
        "head": {"kind": "head", "parent": "neck", "bone": [[484, 116], [530, 114], [596, 122]]},
        "jaw": {"kind": "jaw", "parent": "head", "bone": [[556, 145], [598, 143]]},
        "ear_far": {"kind": "ear", "parent": "head", "bone": [[490, 88], [489, 58]]},
        "ear_near": {"kind": "ear", "parent": "head", "bone": [[516, 86], [516, 50]]},
        "hind_near": {"kind": "leg", "parent": "torso", "bone": [[206, 290], [214, 330], [204, 362], [216, 404]]},
        "hind_far": {"kind": "leg", "parent": "torso", "bone": [[256, 294], [262, 334], [250, 364], [260, 404]]},
        "front_near": {"kind": "leg", "parent": "torso", "bone": [[412, 290], [414, 340], [424, 404]]},
        "front_far": {"kind": "leg", "parent": "torso", "bone": [[376, 294], [380, 350], [386, 404]]},
    }, "points": {"eye": [530, 108]}}
    return im, truth, marks


def hand():
    """A hand, 400x400, palm and four thin fingers and a thumb of one skin ramp; two fingers touch along their sides
    with only an ink line between them."""
    def poly(pts):
        return lambda d: d.polygon(pts, fill=255)
    layers = [
        ("palm", poly([(120, 220), (290, 220), (300, 330), (130, 340)]), 0),
        ("thumb", poly([(122, 250), (80, 210), (62, 168), (76, 160), (100, 196), (136, 228)]), 0),
        ("index", poly([(132, 222), (136, 90), (152, 88), (156, 222)]), 0),
        ("middle", poly([(170, 222), (172, 60), (190, 58), (194, 222)]), 0),
        ("ring", poly([(194, 222), (198, 76), (216, 76), (218, 222)]), 1),
        ("little", poly([(240, 222), (248, 118), (262, 118), (264, 222)]), 0),
    ]
    im, truth = compose(400, 400, layers, SKIN, 50, 40, ink_pairs=[("ring", "middle")])
    marks = {"parts": {
        "palm": {"kind": "hand", "bone": [[150, 280], [270, 280]]},
        "thumb": {"kind": "finger", "parent": "palm", "bone": [[118, 236], [84, 196], [72, 170]]},
        "index": {"kind": "finger", "parent": "palm", "bone": [[144, 220], [144, 100]]},
        "middle": {"kind": "finger", "parent": "palm", "bone": [[182, 220], [181, 70]]},
        "ring": {"kind": "finger", "parent": "palm", "bone": [[207, 220], [207, 86]]},
        "little": {"kind": "finger", "parent": "palm", "bone": [[252, 220], [255, 128]]},
    }}
    return im, truth, marks


def rough(marks, d=10, seed=1):
    """The same marks moved by up to d px, as a careless eye would place them."""
    rng = np.random.default_rng(seed)
    out = {"parts": {}, "points": marks.get("points", {})}
    for n, spec in marks["parts"].items():
        bone = [None if p is None else [p[0] + int(rng.integers(-d, d + 1)), p[1] + int(rng.integers(-d, d + 1))]
                for p in spec["bone"]]
        out["parts"][n] = dict(spec, bone=bone)
    return out


THIN = {"index", "middle", "ring", "little", "thumb", "ear_far", "ear_near", "jaw"}


def creatures():
    """Each creature cut from its marks as placed and from the same marks moved by a careless eye: every part must
    match its true pixels (off the ink) by IoU 0.8, a thin part 0.6, and the neck 0.7 (where a neck drawn over the
    chest in the same fur ends is a matter of taste). A leg must not take the hip, a tail the rump's edge."""
    ok = True
    for fig in (beast, hand):
        im, truth, marks = fig()
        for how, mk in (("as placed", marks), ("rough", rough(marks, 8 if fig is beast else 4))):
            res, aux = bp.analyse(im, mk)
            H, W = next(iter(truth.values())).shape
            full = bp.full_labels(aux, (W, H))
            a = np.asarray(im.convert("RGBA")).astype(int)
            off_ink = (np.abs(a[..., :3] - np.array(FIG_INK)).sum(2) > 30) & (a[..., 3] > 0)
            bad = []
            for i, n in enumerate(aux["names"]):
                t, g = truth[n] & off_ink, (full == i) & off_ink
                iou = (t & g).sum() / max(1, (t | g).sum())
                need = 0.6 if n in THIN else 0.7 if n == "neck" else 0.8
                if iou < need:
                    bad.append(f"{n} {iou:.2f} < {need}")
            print(f"{fig.__name__:7s} {how:9s} {'ok' if not bad else 'WRONG: ' + ', '.join(bad)}")
            ok &= not bad
    return ok


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
    detail = Image.new("RGBA", (1260, 100))
    d = ImageDraw.Draw(detail)
    d.rectangle((30, 30, 70, 70), fill="green")
    d.line((71, 50, 370, 50), fill="green")
    d.point((400, 50), fill="gold")
    detail_result, detail_aux = bp.analyse(detail, {"parts": {"body": {"bone": [[50, 50]]}}})
    all_pixels = np.array_equal(bp.full_labels(detail_aux, detail.size) == 0, np.asarray(detail.getchannel("A")) != 0)
    print("full-size mask keeps a thin tail and a detached spark:", "ok" if all_pixels else "WRONG")
    ok &= all_pixels
    part = detail_result["parts"][0]
    detail_ok = part["pieces"] == 2 and part["area_share"] == 1 and part["bbox"] == [30, 30, 401, 71]
    print("full-size part statistics include the detached spark:", "ok" if detail_ok else f"WRONG {part}")
    ok &= detail_ok
    small = Image.new("RGBA", (36, 20))
    pen = ImageDraw.Draw(small)
    pen.rectangle((3, 5, 17, 15), fill=(136, 98, 50, 255))
    pen.rectangle((17, 8, 31, 12), fill=(45, 150, 110, 255))
    hinge = {"parts": {"head": {"bone": [[6, 10], [15, 10]]},
                       "arm": {"parent": "head", "bone": [[17, 10], [29, 10]]}}, "points": {"eye": [8, 8]}}
    forward, forward_aux = bp.analyse(small, hinge)
    hinge["parts"]["arm"]["bone"].reverse()
    reverse, reverse_aux = bp.analyse(small, hinge)
    same = (forward["parts"][1]["pivot"] == reverse["parts"][1]["pivot"] == [17, 10]
            and np.array_equal(forward_aux["labels_full"], reverse_aux["labels_full"]))
    print("reversed arm keeps the shoulder pivot and labels:", "ok" if same else f"WRONG {reverse['parts'][1]['pivot']}")
    ok &= same
    eyes = not any("eye" in w for w in forward["warnings"])
    for eye in ([0, 0], [-1, 8]):
        hinge["points"]["eye"] = eye
        eyes &= any("eye" in w for w in bp.analyse(small, hinge)[0]["warnings"])
    print("eye ownership uses default head kind and visible pixels:", "ok" if eyes else "WRONG")
    ok &= eyes
    empty = Image.new("RGBA", (16, 16))
    ImageDraw.Draw(empty).rectangle((4, 4, 11, 11), fill=(255, 155, 40, 0))
    _, hidden_aux = bp.analyse(empty, {"parts": {"body": {"bone": [[6, 8], [9, 8]]}}})
    hidden = int((hidden_aux["labels_full"] >= 0).sum())
    print("fully transparent RGB has no visible labels:", "ok" if not hidden else f"WRONG {hidden}")
    ok &= hidden == 0
    ok &= creatures()
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
        root = Path(tmp)
        drawing, marks = root / "small.png", root / "cycle.json"
        Image.new("RGBA", (10, 10), (100, 50, 80, 255)).save(drawing)
        marks.write_text(json.dumps({"parts": {"a": {"bone": [[2, 2]], "parent": "b"},
                                                "b": {"bone": [[7, 7]], "parent": "a"}}}), encoding="utf-8")
        code, report = run_main([str(drawing), str(marks)])
        case("parent cycles are usage errors", code == 2 and "cycle" in report and "a" in report and "b" in report,
             (code, report))
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        examples = Path(__file__).resolve().parents[2] / "examples"
        drawing, marks = root / "figure.png", root / "figure_parts.json"
        shutil.copyfile(examples / "figure.png", drawing)
        shutil.copyfile(examples / "marks.json", marks)
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
        code, report = run_main([str(drawing), str(marks)])
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
        case("source marks cannot be overwritten", code == 2 and marks.name in report and before == after,
             (code, before[marks.name] == after[marks.name], sorted(after)))
        shutil.copyfile(examples / "marks.json", marks)
        code, report = run_main([str(drawing), str(marks), "--out", str(root / "cut")])
        case("the same sources cut into a separate folder", code == 0, report)
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
        with open(os.path.join(tmp, "cut", "full_parts.json"), encoding="utf-8") as fh:
            parts = json.load(fh)["parts"]
            labels = {p["name"]: p["label"] for p in parts}
        with Image.open(os.path.join(tmp, "cut", "full_labels.png")) as mask:
            pixels = np.asarray(mask)
            for part in parts:
                ys, xs = np.nonzero(pixels == part["label"])
                bounds = [xs.min(), ys.min(), xs.max() + 1, ys.max() + 1]
                case(f"{part['name']} bbox encloses its full-size label", part["bbox"] == bounds, part["bbox"])
            for part, visible, covered in (("cape", [(205, 645), (300, 645), (400, 645)], (265, 645)),
                                           ("staff", [(461, 110), (461, 600)], (462, 342))):
                case(f"{part} cut keeps every visible section and its gap",
                     all(mask.getpixel(p) == labels[part] for p in visible) and mask.getpixel(covered) != labels[part])
        code, text = run_main([full, stray, "--out", os.path.join(tmp, "cut")])
        case("a cut with CHECK lines exits 1", code == 1 and "CHECK" in text, text[-300:])
        child = next(n for n, p in MARKS["parts"].items() if p.get("parent"))
        broken = {                                        # each must be a usage error naming the fault, no traceback
            "no bone": {child: {"kind": "head"}},
            "an empty bone": {child: dict(MARKS["parts"][child], bone=[])},
            "a bone of nulls": {child: dict(MARKS["parts"][child], bone=[None, None])},
            "a point not two numbers": {child: dict(MARKS["parts"][child], bone=[["a", 3], [4, 5]])},
            "a point of true and false": {child: dict(MARKS["parts"][child], bone=[[True, 3], [4, 5]])},
            "a point of three numbers": {child: dict(MARKS["parts"][child], bone=[[1, 2, 3]])},
            "a part not an object": {child: [1, 2]},
            "a parent misspelt": {child: dict(MARKS["parts"][child], parent="torsoo")},
            "a parent that is itself": {child: dict(MARKS["parts"][child], parent=child)},
            "a kind that is not text": {child: dict(MARKS["parts"][child], kind=5)},
        }
        files = {k: {"parts": dict(MARKS["parts"], **v)} for k, v in broken.items()}
        files["an eye of one number"] = dict(MARKS, points={"eye": [1]})
        files["points not an object"] = dict(MARKS, points=[1, 2])
        for what, marks in files.items():
            path = os.path.join(tmp, "broken.json")
            with open(path, "w") as fh:
                json.dump(marks, fh)
            try:
                code, text = run_main([full, path, "--out", os.path.join(tmp, "cut")])
            except Exception as e:                        # a traceback: the check let it through
                code, text = None, repr(e)
            named = repr(child) in text if what in broken else '"points"' in text   # the error names the part
            case(f"a landmarks file with {what} exits 2", code == 2 and "error:" in text and named, text[-200:])
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
