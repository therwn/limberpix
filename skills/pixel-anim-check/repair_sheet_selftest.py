"""repair_sheet.py's own test: a generated-looking idle whose mouth is missing in frames 2 and 9 comes back with
the mouth on every frame, pixel for pixel where it was drawn, and every other frame untouched; by lostmark's vote
and by a keep list alike. A mark that moved within its patch is not drawn twice, and the command line writes
its three files.

    python repair_sheet_selftest.py        (or: python repair_sheet.py --selftest)
"""
import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pixel_anim_check as pac  # noqa: E402
import pixel_anim_selftest as st  # noqa: E402
import repair_sheet as rs  # noqa: E402

N = 10


def run():
    ok = True

    def case(name, cond, got=""):
        nonlocal ok
        print(f"repair   {name:58s} {'ok' if cond else 'WRONG'}" + ("" if cond else f"  ({got})"))
        ok &= bool(cond)

    truth = [st.face_frame(k, N) for k in range(N)]
    broken = [st.face_frame(k, N, mouth=k not in (2, 9)) for k in range(N)]
    spec = pac.Spec(eye=st.EYE, fps=10, style="redrawn")
    out, log = rs.repair(broken, spec)
    case("lostmark's mouth, frames 2 and 9, drawn back as it was", out == truth,
         [k for k in range(N) if out[k] != truth[k]])
    case("the other frames untouched", all(out[k] == broken[k] for k in range(N) if k not in (2, 9)))
    case("the log names frames 2 and 9, and nothing is left", sorted(r["frame"] for r in log["repairs"]) == [2, 9]
         and not [f for f in log["after"] if f["rule"] in rs.REPAIRED], log["after"])

    keep = pac.features(truth[0], spec)
    out, log = rs.repair(broken, pac.Spec(eye=st.EYE, fps=10, style="redrawn", keep=keep))
    case("a keep list's mouth drawn back the same way", out == truth, [k for k in range(N) if out[k] != truth[k]])

    mostly = [st.face_frame(k, N, mouth=k in (0, 5, 8, 9)) for k in range(N)]
    out, log = rs.repair(mostly, pac.Spec(eye=st.EYE, fps=10, style="redrawn", keep=keep))
    case("kept, the mouth missing in 6 of 10 frames comes back on all", out == truth,
         [k for k in range(N) if out[k] != truth[k]])

    moved = [st.face_frame(k, N) for k in range(N)]
    for k in (2, 9):                                      # the mouth drawn 2 rows low in frames 2 and 9
        rows = [y for y, r in enumerate(moved[k]) if st.MOUTH in r]
        for y in sorted(rows, reverse=True):
            for x, v in enumerate(moved[k][y]):
                if v == st.MOUTH:
                    moved[k][y][x], moved[k][y + 2][x] = st.SKIN, st.MOUTH
    out, log = rs.repair(moved, spec)
    case("a mouth drawn 2 px low, still in the face, is not drawn twice", out == moved and any(
        "not lost" in s["why"] for s in log["skipped"]), log)

    clean, log = rs.repair(truth, spec)
    case("a sound loop is left as it is", clean == truth and not log["repairs"], log["repairs"])

    with tempfile.TemporaryDirectory() as d:
        strip = os.path.join(d, "idle.png")
        st._strip(broken, strip)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = rs.main([strip, "--frame", "32", "--fps", "10", "--eye", st.EYE, "--out", d, "--name", "face"])
            usage = rs.main([strip, "--frame", "32", "--out", d, "--name", "idle", "--repaired-name"])
        files = [os.path.join(d, f"face_{t}") for t in ("repaired.png", "repair.json", "repair.png")]
        with open(files[1], encoding="utf-8") as fh:
            logged = json.load(fh)
        again = pac.load(files[0], frame=32)
        case("the command line writes the strip, the log and the picture", code == 0 and all(
            os.path.isfile(f) for f in files) and again == truth and len(logged["repairs"]) == 2, code)
        case("an unknown option is a usage error", usage == 2, usage)
    print("selftest:", "all hold" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
