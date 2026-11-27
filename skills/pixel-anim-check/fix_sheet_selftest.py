"""fix_sheet.py's own test, the case the tools are for: an image model's 10-pose idle sheet (6 times the game size,
on a green key) whose mouth is missing in poses 2 and 9. --features lists the face's eyes and mouth; one run with
the confirmed list brings the sheet onto the drawing's grid, draws the mouth back in frames 2 and 9, and checks
clean: the fixed strip is the game-size idle, pixel for pixel.

    python fix_sheet_selftest.py        (or: python fix_sheet.py --selftest)
"""
import contextlib
import io
import json
import os
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fix_sheet as fs  # noqa: E402
import pixel_anim_check as pac  # noqa: E402
import pixel_anim_selftest as st  # noqa: E402
import prepare_sheet_selftest as pst  # noqa: E402

N = 10


def run():
    ok = True

    def case(name, cond, got=""):
        nonlocal ok
        print(f"fix      {name:58s} {'ok' if cond else 'WRONG'}" + ("" if cond else f"  ({got})"))
        ok &= bool(cond)

    truth = [st.face_frame(k, N) for k in range(N)]
    broken = [st.face_frame(k, N, mouth=k not in (2, 9)) for k in range(N)]
    with tempfile.TemporaryDirectory() as d:
        sheet, drawing = os.path.join(d, "sheet.png"), os.path.join(d, "face.png")
        Image.fromarray(pst._sheet(broken)[..., :3], "RGB").save(sheet)
        Image.fromarray(pst._rgba(truth[0]), "RGBA").save(drawing)
        base = [sheet, "--ref", drawing, "--out", d, "--name", "face", "--fps", "10", "--eye", st.EYE]
        quiet = contextlib.redirect_stdout(io.StringIO())
        with quiet, contextlib.redirect_stderr(io.StringIO()):
            listed = fs.main(base + ["--features"])
        with open(os.path.join(d, "face_features.json"), encoding="utf-8") as fh:
            found = json.load(fh)
        kinds = sorted((f["kind"], f["blink"]) for f in found["features"])
        case("--features lists two eyes and the mouth", listed == 0 and kinds == [("mark", False)]
             + [("mark", True)] * 2, (listed, kinds))
        for f in found["features"]:
            f["name"] = "eye" if f["blink"] else "mouth"
        keep = os.path.join(d, "keep.json")
        with open(keep, "w", encoding="utf-8") as fh:
            json.dump(found, fh)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = fs.main(base + ["--keep", keep])
        fixed = pac.load(os.path.join(d, "face_fixed.png"), frame=32)
        with open(os.path.join(d, "face_repair.json"), encoding="utf-8") as fh:
            log = json.load(fh)
        case("the run draws the mouth back in frames 2 and 9", sorted(r["frame"] for r in log["repairs"]) == [2, 9],
             log["repairs"])
        case("the fixed strip is the game-size idle, pixel for pixel", fixed == truth,
             [k for k in range(N) if fixed[k] != truth[k]])
        case("and it checks clean (exit 0)", code == 0 and "face: 0 fault(s)" in out.getvalue(), out.getvalue()[-400:])
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            both = fs.main(base + ["--features", "--keep", keep])
        case("--features with --keep is a usage error", both == 2, both)
    print("selftest:", "all hold" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
