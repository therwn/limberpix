"""One command for a sheet an image model drew: bring it onto the approved drawing's grid, draw back the marks some
frames dropped, and check the result, with a contact sheet and a GIF to look at.

    python fix_sheet.py SHEET.png --ref DRAWING.png --features [--grid CxR] [--out DIR] [--name NAME]
    python fix_sheet.py SHEET.png --ref DRAWING.png [--keep LIST.json] [--gaps] [--grid CxR] [--fps N] [--eye "#rrggbb"]
                        [--ink C,...] [--effects C,...] [--shadow C,...] [--out DIR] [--name NAME]
    python fix_sheet.py --selftest

1. prepare_sheet.py: the poses keyed out, split, scaled, anchored and voted onto the drawing's grid.
   -> <name>_strip.png
2. With --features: the keep list's candidates (pixel_anim_check.py --features), read off the drawing when it is
   pixel art (64 colours or fewer), else off the first frame -> <name>_features.png and .json. Nothing else runs:
   show the picture to the user, name what must stay, mark what comes and goes ("transient"), and run again with
   --keep.
3. repair_sheet.py: each mark keep (with --keep) or lostmark finds missing drawn back from its nearest frame, and
   with --gaps the outline's short gaps closed on every frame.
   -> <name>_fixed.png, <name>_repair.json, <name>_repair.png
4. pixel_anim_check.py on the fixed strip, --style redrawn: its faults and warnings, a contact sheet and a GIF.
Exit code: the check's (0 no fault, 1 faults), 2 a usage error.
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pixel_anim_check as pac  # noqa: E402
import prepare_sheet as ps  # noqa: E402
import repair_sheet as rs  # noqa: E402


def main(argv):
    if not argv or "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0 if argv else 2
    valued = {"--ref", "--grid", "--keep", "--fps", "--eye", "--ink", "--effects", "--shadow", "--out", "--name"}
    try:
        src, got, flags, i = None, {}, set(), 0
        while i < len(argv):
            if argv[i] in valued:
                if i + 1 >= len(argv):
                    raise ValueError(f"{argv[i]} needs a value")
                got[argv[i]] = argv[i + 1]
                i += 2
            elif argv[i] in ("--features", "--gaps"):
                flags.add(argv[i])
                i += 1
            elif argv[i].startswith("--") or src is not None:
                raise ValueError(f"unknown argument {argv[i]!r}")
            else:
                src = argv[i]
                i += 1
        if src is None or not os.path.isfile(src):
            raise ValueError(f"no such sheet: {src}")
        if "--ref" not in got or not os.path.isfile(got["--ref"]):
            raise ValueError("--ref needs the approved drawing at game size")
        if "--features" in flags and "--keep" in got:
            raise ValueError("--features writes the keep list; --keep reads it: run them one after the other")
        name = got.get("--name", os.path.splitext(os.path.basename(src))[0])
        folder = got.get("--out", ".")
        args = [src, "--ref", got["--ref"], "--out", folder, "--name", name]
        if "--grid" in got:
            args += ["--grid", got["--grid"]]
    except ValueError as e:
        print(f"error: {e}  (--help lists the options)", file=sys.stderr)
        return 2
    print("1. prepare")
    code = ps.main(args)
    if code:
        return code
    strip = os.path.join(folder, f"{name}_strip.png")
    with Image.open(got["--ref"]) as im:
        ref = np.array(im.convert("RGBA"))
    width = ref.shape[1]
    common = []
    for opt in ("--eye", "--ink", "--effects", "--shadow", "--fps"):
        if opt in got:
            common += [opt, got[opt]]
    if "--features" in flags:
        print("2. the keep list's candidates")
        pixel_art = len(np.unique(ref[ref[..., 3] >= 128][:, :3], axis=0)) <= ps.REF_COLOURS
        return pac.main(["--loop", f"idle={strip}", "--frame", str(width), "--style", "redrawn", "--features",
                         "--out", folder, "--name", name] + (["--ref", got["--ref"]] if pixel_art else []) + common)
    print("2. repair")
    rargs = [strip, "--frame", str(width), "--out", folder, "--name", name] + common
    if "--keep" in got:
        rargs += ["--keep", got["--keep"]]
    if "--gaps" in flags:
        rargs.append("--gaps")
    code = rs.main(rargs)
    if code == 2:
        return code
    fixed = os.path.join(folder, f"{name}_fixed.png")
    os.replace(os.path.join(folder, f"{name}_repaired.png"), fixed)
    print("3. check the fixed strip")
    cargs = ["--loop", f"idle={fixed}", "--frame", str(width), "--style", "redrawn", "--out", folder,
             "--name", name] + common
    if "--keep" in got:
        cargs += ["--keep", got["--keep"]]
    return pac.main(cargs)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        try:
            import fix_sheet_selftest
        except ImportError:
            print("error: --selftest needs fix_sheet_selftest.py beside this file", file=sys.stderr)
            sys.exit(2)
        sys.exit(0 if fix_sheet_selftest.run() else 1)
    sys.exit(main(sys.argv[1:]))
