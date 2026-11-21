"""The map checked on ten clean test shapes (no shading, no ink, nothing held): it draws each with a known eye and
body plan and checks the map reads it: the plan, the legs and how many, the wings, the parts named only where they
can be (ears on the head, legs under the trunk), the head at the eye's end, the facing, the ground line. A small
pixel walker, scaled 1x, 4x and 8x, is only checked to run without a crash: its plan comes out wrong.
What it does not prove: the fish is only checked to read as a floating body with its fins found. Its plan comes out
"flier" (the fins read as wings), so the "swimmer" plan is never told from a flier here. And clean shapes are not
real art: on real drawings the map is a first look only (see creature_map's help)."""
import contextlib
import io
import json
import math
import os
import sys
import tempfile

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import creature_map as cm                                 # noqa: E402

BG, BODY, EYE = (30, 24, 36), (200, 150, 110), (255, 200, 40)
EYEHEX = "#ffc828"


def canvas():
    im = Image.new("RGB", (640, 400), BG)
    return im, ImageDraw.Draw(im)


def quadruped(facing="right"):
    im, d = canvas()
    d.ellipse((150, 140, 470, 260), fill=BODY)
    for x in (180, 250, 370, 430):
        d.rectangle((x, 220, x + 26, 360), fill=BODY)
    d.ellipse((440, 90, 560, 190), fill=BODY)
    d.polygon([(470, 100), (490, 40), (505, 100)], fill=BODY)
    d.polygon([(520, 100), (540, 45), (550, 105)], fill=BODY)
    d.line([(160, 190), (90, 150), (50, 90)], fill=BODY, width=18)
    d.ellipse((520, 125, 534, 139), fill=EYE)
    return im if facing == "right" else im.transpose(Image.FLIP_LEFT_RIGHT)


def biped():
    im, d = canvas()
    d.rectangle((285, 140, 355, 262), fill=BODY)                     # torso
    d.ellipse((282, 62, 358, 138), fill=BODY)                        # head
    d.rectangle((292, 255, 316, 360), fill=BODY)                     # legs
    d.rectangle((326, 255, 350, 360), fill=BODY)
    d.line([(288, 150), (245, 250)], fill=BODY, width=16)            # arms, hanging
    d.line([(352, 150), (395, 250)], fill=BODY, width=16)
    d.ellipse((330, 92, 342, 104), fill=EYE)
    return im


def bugs(n):
    """A six- or eight-legged walker seen from the side: a long body and n jointed legs, near and far side in turn,
    each bent out at the knee and down to the ground, none crossing another."""
    im, d = canvas()
    d.ellipse((170, 170, 420, 250), fill=BODY)
    d.ellipse((400, 165, 480, 235), fill=BODY)
    step = 200 / (n - 1)
    for i in range(n):
        x = 195 + i * step
        knee = (x - 12 if i % 2 else x + 8, 275)
        d.line([(x, 228), knee, (x - 4, 360)], fill=BODY, width=9)
    d.ellipse((455, 185, 467, 197), fill=EYE)
    return im


def dragon():
    im = quadruped()
    d = ImageDraw.Draw(im)
    d.polygon([(260, 150), (200, 20), (330, 60), (380, 150)], fill=BODY)   # a wing, raised over the back
    return im


def bird():
    im, d = canvas()
    d.ellipse((250, 180, 400, 250), fill=BODY)
    d.ellipse((380, 160, 450, 220), fill=BODY)
    d.polygon([(290, 200), (200, 40), (360, 190)], fill=BODY)
    d.polygon([(300, 215), (60, 120), (330, 235)], fill=BODY)
    d.polygon([(255, 225), (170, 270), (180, 240)], fill=BODY)
    d.ellipse((420, 178, 432, 190), fill=EYE)
    return im


def snake():
    im, d = canvas()
    pts = [(60 + i * 5, 300 - 50 * math.sin(i * 5 / 95)) for i in range(100)]
    pts = [(x, y + (360 - 17 - max(p[1] for p in pts))) for x, y in pts]
    d.line(pts, fill=BODY, width=34, joint="curve")
    hx, hy = pts[-1]
    d.ellipse((hx - 30, hy - 26, hx + 30, hy + 26), fill=BODY)
    d.ellipse((hx + 8, hy - 12, hx + 20, hy), fill=EYE)
    return im


def fish():
    im, d = canvas()
    d.ellipse((200, 150, 460, 230), fill=BODY)                       # body, off the ground
    d.polygon([(205, 190), (120, 130), (140, 190), (120, 250)], fill=BODY)   # tail fin
    d.polygon([(300, 155), (340, 95), (380, 158)], fill=BODY)        # dorsal fin
    d.ellipse((420, 172, 434, 186), fill=EYE)
    return im


def jellyfish():
    im, d = canvas()
    d.ellipse((240, 60, 400, 170), fill=BODY)                        # bell
    for i, x in enumerate((260, 295, 330, 365)):
        d.line([(x, 150), (x - 10 + 10 * (i % 2), 230), (x + 5, 300)], fill=BODY, width=10)
    d.ellipse((330, 100, 342, 112), fill=EYE)
    return im


def blob():
    im, d = canvas()
    d.ellipse((220, 200, 420, 360), fill=BODY)
    d.ellipse((350, 250, 362, 262), fill=EYE)
    return im


# A small pixel walker (34x22, one frame of pixel_anim_check's selftest walker). Scaled up, its skeleton falls apart
# into pieces, so the core's two ends lie in different ones: the map must still run.
WALKER = ["..................................", "..................................",
          "..................................", "..................................",
          "........................kkkk......", ".......................kffffk.....",
          "......................kffffffk....", "...kkk........kkkk...kfffffbffk...",
          "..kfffk...kkkkffffkkkkffffffffk...", "...kkffkkkffffffffffffkffffffk....",
          ".....kfffffffffffffffffkffffk.....", "......kkffffffffffffffffkkkk......",
          ".......keeeeeeeeeeeeeeeek.........", "........keeeeeeeeeeeeeek..........",
          ".........keeeeeeeeeeeeyk..........", ".........kyykyeeeeyykyyk..........",
          ".........kyykyykkkyykyyk..........", ".........kyykyyk.kyykyyk..........",
          ".........kyykyyk.kyykyyk..........", ".........kyykyyk.kyykyyk..........",
          "..........kk.kk...kk.kk...........", ".................................."]
WALKER_COLS = {"k": (26, 18, 22), "f": (200, 148, 106), "b": (255, 204, 51), "e": (227, 192, 154),
               "y": (168, 116, 78)}


def walker(scale=1):
    im = Image.new("RGBA", (len(WALKER[0]), len(WALKER)), (0, 0, 0, 0))
    for y, row in enumerate(WALKER):
        for x, c in enumerate(row):
            if c != ".":
                im.putpixel((x, y), WALKER_COLS[c] + (255,))
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def run():
    ok = True

    def case(name, cond, got):
        nonlocal ok
        print(f"{name:52s} {'ok' if cond else 'WRONG'}  ({got})")
        ok &= bool(cond)

    kinds = lambda res: sorted(p["name"] for p in res["parts"])   # noqa: E731
    for facing in ("right", "left"):
        res, _ = cm.analyse(quadruped(facing), EYEHEX)
        legs = [p for p in res["parts"] if p["kind"] == "leg"]
        case(f"quadruped ({facing}): a quadruped", res["plan"] == "quadruped", res["plan"])
        case(f"quadruped ({facing}): four legs", len(legs) == 4, kinds(res))
        case(f"quadruped ({facing}): faces {facing}", res["facing"] == facing, res["facing"])
        case(f"quadruped ({facing}): ground at the feet", abs(res["ground_y"] - 360) <= 6, res["ground_y"])
        ears = [p for p in res["parts"] if p["kind"].startswith("ear")]
        case(f"quadruped ({facing}): ears, and only on the head", ears and all(p["zone"] == "head" for p in ears),
             [(p["name"], p["zone"]) for p in ears])
        case(f"quadruped ({facing}): nothing on the neck called an ear",
             not any(p["kind"].startswith("ear") and p["zone"] != "head" for p in res["parts"]), kinds(res))
    res, _ = cm.analyse(biped(), EYEHEX)
    case("biped: upright biped", res["plan"].startswith("biped (upright"), res["plan"])
    case("biped: two legs", sum(p["kind"] == "leg" for p in res["parts"]) == 2, kinds(res))
    case("biped: two arms", sum(p["kind"].startswith("arm") for p in res["parts"]) == 2, kinds(res))
    for n, word in ((6, "hexapod"), (8, "octopod")):
        res, _ = cm.analyse(bugs(n), EYEHEX)
        case(f"{n} legs: {word}", res["plan"].startswith(word), (res["plan"], kinds(res)))
    res, _ = cm.analyse(dragon(), EYEHEX)
    case("dragon: winged quadruped", res["plan"].startswith("winged quadruped"), (res["plan"], kinds(res)))
    res, _ = cm.analyse(bird(), EYEHEX, floating=True)
    case("bird: a flier with two wings", res["plan"].startswith("flier")
         and sum(p["kind"].startswith("wing") for p in res["parts"]) == 2, (res["plan"], kinds(res)))
    res, _ = cm.analyse(snake(), EYEHEX)
    case("snake: serpent", res["plan"].startswith("serpent"), (res["plan"], kinds(res)))
    case("snake: faces right", res["facing"] == "right", res["facing"])
    res, _ = cm.analyse(fish(), EYEHEX, floating=True)
    case("fish: a floating body (swimmer or flier), fins found", res["plan"].startswith(("swimmer", "flier", "floater"))
         and len(res["parts"]) >= 1, (res["plan"], kinds(res)))
    res, _ = cm.analyse(jellyfish(), EYEHEX, floating=True)
    case("jellyfish: floater with tentacles", res["plan"].startswith("floater with tentacles"),
         (res["plan"], kinds(res)))
    res, _ = cm.analyse(blob(), EYEHEX)
    case("blob: a blob", res["plan"].startswith("blob"), (res["plan"], kinds(res)))
    for scale in (1, 4, 8):                              # a pixel sprite, scaled: no crash, a plan of some kind
        try:
            res, _ = cm.analyse(walker(scale), "#ffcc33")
            case(f"pixel walker x{scale}: runs (its plan is not judged)", bool(res["plan"]), res["plan"])
        except Exception as e:                            # noqa: BLE001 (any crash is the failure)
            case(f"pixel walker x{scale}: runs (its plan is not judged)", False, repr(e))
    cli(case)
    print("selftest:", "all hold" if ok else "FAILED")
    return ok


def cli(case):
    """The command line: --help exits 0, no or bad arguments exit 2, --eye in any case and without '#' is read like
    '#rrggbb'."""
    def run_main(args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            return cm.main(args), buf.getvalue()
    for name, cond in (("cli: --help exits 0", run_main(["--help"])[0] == 0 and run_main(["-h"])[0] == 0),
                       ("cli: no arguments exit 2", run_main([])[0] == 2)):
        case(name, cond, "")
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "q.png")
        quadruped().save(src)
        out = os.path.join(tmp, "out")
        bad = [run_main([src, "--eye", "#ffc82"])[0], run_main([src, "--eye-at", "3"])[0],
               run_main([src, "--bogus"])[0], run_main([os.path.join(tmp, "none.png")])[0]]
        case("cli: bad --eye, --eye-at, option, file exit 2", bad == [2, 2, 2, 2], bad)
        lo = run_main([src, "--eye", EYEHEX, "--out", out, "--name", "lo"])
        up = run_main([src, "--eye", EYEHEX.upper().lstrip("#"), "--out", out, "--name", "lo"])
        same = lo[0] == up[0] == 0 and lo[1] == up[1]
        case("cli: --eye FFC828 read as #ffc828", same, (lo[0], up[0]))
        slim = snake()
        x0, y0, x1, y1 = ImageChops.difference(slim, Image.new("RGB", slim.size, BG)).getbbox()
        slim = slim.crop((x0 - 2, y0 - 2, x1 + 2, y1 + 2))
        slim.save(src)
        code, msg = run_main([src, "--eye", EYEHEX, "--out", out])
        case("cli: a single wide snake keeps its ground plan",
             code == 0 and "serpent or worm" in msg and "facing right" in msg, msg)
        round_body = Image.new("RGBA", (32, 32))
        d = ImageDraw.Draw(round_body)
        d.ellipse((8, 8, 24, 24), fill=BODY)
        d.point((20, 13), fill=(0, 0, 0, 255))
        round_body.save(src)
        code, msg = run_main([src, "--eye", "000000", "--out", out, "--name", "round"])
        case("cli: a round body with a black eye faces right", code == 0 and "blob" in msg and "facing right" in msg, msg)
        if code == 0:
            with open(os.path.join(out, "round_map.json"), encoding="utf-8") as fh:
                res = json.load(fh)
            case("cli: round body's centre and ground are mapped", res["ground_y"] == 24 and len(res["spine"]) == 1, res)
        Image.new("RGBA", (32, 32)).save(src)
        case("cli: an empty silhouette still exits 1", run_main([src, "--out", out])[0] == 1, "")
        strip = os.path.join(tmp, "strip.png")
        frame = walker()
        sheet = Image.new("RGBA", (frame.width * 8, frame.height))
        for k in range(8):
            sheet.paste(frame, (k * frame.width, 0))
        sheet.save(strip)
        code = run_main([strip, "--out", out])[0]
        case("cli: a strip of frames is a usage error (exit 2)", code == 2, code)


SHAPES = {"quadruped": quadruped, "biped": biped, "insect": lambda: bugs(6), "spider": lambda: bugs(8),
          "dragon": dragon, "bird": bird, "snake": snake, "fish": fish, "jellyfish": jellyfish, "blob": blob}

if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--sheets") + 1] if "--sheets" in sys.argv else None
    if out:
        for name, fn in SHAPES.items():
            im = fn()
            res, aux = cm.analyse(im, EYEHEX, floating=name in ("bird", "fish", "jellyfish"))
            cm.overlay(im, res, aux, os.path.join(out, f"test_{name}_map.png"))
    sys.exit(0 if run() else 1)
