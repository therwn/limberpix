"""Build the example inputs from the selftests' own creatures, so the examples and the tests can never drift apart.

    python examples/make_examples.py              # write the example files that differ from what is on disk
    python examples/make_examples.py --verify     # rebuild them in memory and compare with the files on disk (CI)
    python examples/make_examples.py --docs       # also refresh the plugin icon and the README's pictures (docs/img,
                                                  # drawn by showcase/make_showcase.py)
    python examples/make_examples.py --skills DIR # read the skills from DIR (default: ../skills)
    python examples/make_examples.py --help

A file is rewritten only when its pixels (or its JSON) differ from the one on disk, so another Pillow or zlib build
does not churn the tracked files. An unknown option is an error (exit 2).

Written here:
  walker_idle.png, walker_move.png   a clean four-legged walker, frames 34x22 (strips: --frame 34)
  flier_idle.png,  flier_move.png    a clean flier over its shadow row, frames 30x24 (--frame 30)
  broken_move.png                    the walker's move with one fault injected: frame 8 knocked 4 px sideways
                                     (pixel_anim_check reports `jump` and exits 1)
  figure.png, marks.json             a standing figure and the rough bones placed on it, for body_parts.py

The creatures are drawn by pixel_anim_selftest.py and body_parts_selftest.py; this script only writes them out.
Needs Python 3.11+, NumPy and Pillow."""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _options(argv):
    ap = argparse.ArgumentParser(prog="make_examples.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="compare with the files on disk; write nothing")
    mode.add_argument("--docs", action="store_true",
                      help="also refresh the plugin icon and docs/img (showcase/make_showcase.py)")
    ap.add_argument("--skills", default=os.path.join(ROOT, "skills"), metavar="DIR",
                    help="the folder holding the two skills (default: ../skills)")
    return ap.parse_args(argv)


OPTS = _options(sys.argv[1:])                             # --help and bad options exit here, before anything is built
SKILLS = os.path.abspath(OPTS.skills)
CHECK_DIR = os.path.join(SKILLS, "pixel-anim-check")
ANIMATE_DIR = os.path.join(SKILLS, "pixel-animate")
sys.path.insert(0, CHECK_DIR)
sys.path.insert(0, ANIMATE_DIR)
import body_parts_selftest as bst                         # noqa: E402
import pixel_anim_check as pac                            # noqa: E402
import pixel_anim_selftest as st                          # noqa: E402



def strip(frames):
    """Frames (rows of hex colours or None) side by side in one RGBA strip."""
    h, w = len(frames[0]), len(frames[0][0])
    im = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        for y, row in enumerate(f):
            for x, c in enumerate(row):
                if c:
                    im.putpixel((k * w + x, y), pac.hexrgb(c) + (255,))
    return im


def build():
    """Every example file as {name: PIL image or JSON-able object}."""
    walker, flier = st.creatures()
    out = {}
    for cname, loops in (("walker", walker), ("flier", flier)):
        for loop, frames in loops.items():
            out[f"{cname}_{loop}.png"] = strip(frames)
    out["broken_move.png"] = strip(st.broken_move(walker["move"]))
    figure, _ = bst.figure()
    out["figure.png"] = figure
    out["marks.json"] = bst.MARKS
    return out


def _same(path, obj):
    """The file on disk holds the same JSON, or the same pixels, as obj (compared by content, not by bytes: PNG
    compression differs between zlib builds)."""
    if not os.path.exists(path):
        return False
    if path.endswith(".json"):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh) == json.loads(json.dumps(obj))
    disk = np.asarray(Image.open(path).convert("RGBA"))
    mine = np.asarray(obj.convert("RGBA"))
    return disk.shape == mine.shape and bool((disk == mine).all())


def write(files):
    for name, obj in files.items():
        path = os.path.join(HERE, name)
        if _same(path, obj):
            print("same   ", name)
            continue
        if name.endswith(".json"):
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(obj, fh, indent=1)
                fh.write("\n")
        else:
            obj.save(path, optimize=True)
        print("wrote  ", os.path.relpath(path, ROOT))


def verify(files):
    """figure.png is drawn with Pillow's polygon and ellipse rasterisers, which have changed between Pillow releases,
    so a difference there is reported but does not fail."""
    ok = True
    for name, obj in files.items():
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            print("MISSING", name)
            ok = False
        elif _same(path, obj):
            print("same   ", name)
        elif name == "figure.png":
            print("differs", name, "(Pillow's rasteriser; not a failure)")
        else:
            print("DIFFERS", name)
            ok = False
    return ok


def icon(files, path, cells=40, zoom=16):
    """The plugin's icon: the clean walker's first idle frame on a dark square, 640 px a side."""
    walker = files["walker_idle.png"]
    fw = walker.width // 24                               # the idle strip holds 24 frames
    frame = walker.crop((0, 0, fw, walker.height))
    im = Image.new("RGBA", (cells, cells), (30, 26, 34, 255))
    im.alpha_composite(frame, ((cells - fw) // 2, (cells - walker.height) // 2))
    im = im.resize((cells * zoom, cells * zoom), Image.NEAREST).convert("RGB")
    if _same(path, im):
        print("same   ", os.path.relpath(path, ROOT))
        return
    im.save(path, optimize=True)
    print("wrote  ", os.path.relpath(path, ROOT))


def docs():
    """The README's pictures in docs/img: showcase/make_showcase.py draws them from the showcase creatures."""
    sys.path.insert(0, os.path.join(HERE, "showcase"))
    import make_showcase                                  # here, with this run's own Python and Pillow
    make_showcase.main([])


if __name__ == "__main__":
    files = build()
    if OPTS.verify:
        sys.exit(0 if verify(files) else 1)
    write(files)
    if OPTS.docs:
        icon(files, os.path.join(ROOT, ".claude-plugin", "icon.png"))
        docs()
