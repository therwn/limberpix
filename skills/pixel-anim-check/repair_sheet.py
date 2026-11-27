"""Put back what a generated sprite sheet loses: a mark (a mouth, an eye, a stud) that some frames drop is taken
from the nearest frame that has it and drawn into each frame that lacks it. Frames that lose nothing are left as
they are, pixel for pixel.

    python repair_sheet.py STRIP --frame W [--keep LIST.json] [--eye "#rrggbb"] [--ink C,...] [--effects C,...]
                           [--shadow C,...] [--key "#rrggbb"] [--fps N] [--out DIR] [--name NAME]
    python repair_sheet.py --selftest
    python repair_sheet.py --help

STRIP is the loop as a strip PNG (cut by --frame, one frame's width, or --frames, how many it holds), a folder of
PNGs or a GIF, read as pixel_anim_check reads it. The frames are checked first in --style redrawn: with --keep
(a keep list from pixel_anim_check.py --features, confirmed by the user) the features it keeps, otherwise the marks
lostmark finds by the vote of the frames. The other options are pixel_anim_check's.

For each lost mark and each frame without it:
1. The donor is the nearest frame (either way round the loop) where the mark is found near its place.
2. Where it goes: the donor's other marks beside it (the eyes beside a mouth), found again in the frame, give the
   shift; with none, the donor's pixels around the mark are matched against the frame's, the mark's own pixels
   left out, over every shift within reach of the whole figure's move between the two frames (colours under 40
   apart in every channel count as the same).
3. The mark's pixels are drawn there in the donor's colours, over the frame's own pixels but never over air or an
   outline (ink), so it stays inside its patch.
A frame with a like mark (half to twice its px, its colour) within 2.5 reaches of that place is not drawn on: the
mark moved there and was read as lost, and drawing it again would double it. Then the frames are checked again,
and a drawing the check still reads as lost in its frame is undone (it did not take, and may have doubled a mark
the check could not see).

Out, in --out: <name>_repaired.png (the frames side by side), <name>_repair.json (each repair: the mark, the frame,
its donor, the shift, the pixels drawn; each mark that found no donor; the faults before and after) and
<name>_repair.png (the frames before and after, a repaired frame framed in green). Their paths are printed.
A mark that moved onto its patch's edge is not read as a mark there, so it may be drawn a second time: look at
<name>_repair.png before using the strip.
Not repaired here (named in the JSON as skipped): a lost piece apart from the figure, an outline gap, a frame of
another size, a mark no frame shows near its place.
Exit code: 0 nothing left to repair, 1 a mark still missing after the repair, 2 a usage error.
"""
import copy
import json
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                                  # python -I leaves the script's own folder off the path
import pixel_anim_check as pac  # noqa: E402

MATCH = 40                                                # colours this close in every channel align as one
AROUND = 0.1                                              # the alignment window's reach past a mark, of the height
MOVED = 2.5                                               # a like mark this many reaches from the place: moved
REPAIRED = ("keep", "lostmark")


def _same(a, b, rgb):
    if a is None or b is None:
        return a is b
    return pac._contrast(rgb(a), rgb(b)) < MATCH


def _align(donor, target, pixels, guess, reach, rgb, height):
    """(dy, dx, share): where the donor's pixels around the mark (pixels) best match the target's, over every shift
    within reach of guess; share is the fraction of those pixels that match. The window reaches AROUND of the
    figure's height past the mark (4 px at least), so a mouth on plain skin is placed by the eyes and the chin."""
    H, W = len(donor), len(donor[0])
    own = set(pixels)
    ys, xs = [y for y, _ in pixels], [x for _, x in pixels]
    g = max(4, 2 * (max(ys) - min(ys) + 1), 2 * (max(xs) - min(xs) + 1), round(AROUND * height))
    window = [(y, x) for y in range(max(0, min(ys) - g), min(H, max(ys) + g + 1))
              for x in range(max(0, min(xs) - g), min(W, max(xs) + g + 1)) if (y, x) not in own]
    best = None
    for dy in range(guess[0] - reach, guess[0] + reach + 1):
        for dx in range(guess[1] - reach, guess[1] + reach + 1):
            hits = sum(1 for y, x in window if 0 <= y + dy < H and 0 <= x + dx < W
                       and _same(donor[y][x], target[y + dy][x + dx], rgb))
            key = (hits, -math.hypot(dy - guess[0], dx - guess[1]))
            if best is None or key > best[0]:
                best = (key, dy, dx)
    return best[1], best[2], best[0][0] / max(1, len(window))


def _landmarks(mark, marks_d, marks_t, guess, reach, rgbs, near):
    """((dy, dx), the frame's marks used) from the donor's other marks within near px of the lost one (the eyes
    beside a mouth) to the same marks in the frame being repaired (each the frame's closest mark within reach of
    where the move puts it, of a third to three times its px and its colour under KEEP_COLOUR), or (None, []) when
    none is found: a mouth goes where the face's eyes say, even when the model drew the face a pixel off."""
    shifts, used = [], []
    for m in marks_d:
        if m is mark or m["pixels"] == mark["pixels"] or math.dist(m["centre"], mark["centre"]) > near:
            continue
        want = (m["centre"][0] + guess[0], m["centre"][1] + guess[1])
        cand = [q for q in marks_t if math.dist(q["centre"], want) <= reach and m["px"] / 3 <= q["px"] <= 3 * m["px"]
                and (m["code"] == 0) == (q["code"] == 0)
                and (not m["code"] or pac._contrast(rgbs[m["code"]], rgbs[q["code"]]) < pac.KEEP_COLOUR)]
        if cand:
            q = min(cand, key=lambda q: math.dist(q["centre"], want))
            shifts.append((q["centre"][0] - m["centre"][0], q["centre"][1] - m["centre"][1]))
            used.append(q)
    if not shifts:
        return None, []
    return (round(sum(s[0] for s in shifts) / len(shifts)), round(sum(s[1] for s in shifts) / len(shifts))), used


def _key(fault):
    return (fault["rule"], fault.get("feature"), fault.get("row"), fault.get("column"))


def _near(fault, repair):
    """A lostmark fault after the repair naming the same mark (its place may be read on another frame now)."""
    key = repair["_key"]
    return (fault["rule"] == "lostmark" == key[0] and fault.get("row") is not None
            and math.dist((fault["row"], fault["column"]), key[2:]) <= 3)


def _place(fault, spec, arrs):
    """(centre, px, anchor): where a lost mark sits, on the drawing or the frame its place was read on."""
    if fault["rule"] == "keep":
        feature = next(f for f in spec.keep["features"] if f["id"] == fault["feature"])
        top, left, bottom, right = feature["box"]
        return ((top + bottom) / 2, (left + right) / 2), feature["px"], tuple(spec.keep["anchor"])
    shown = fault["frame"]
    return (fault["row"] + 0.5, fault["column"] + 0.5), fault["px"], pac._anchor(arrs[shown])


def repair(frames, spec, name="idle"):
    """(repaired frames, log): every lost mark keep or lostmark names in the loop drawn back from its nearest donor
    frame; log holds "repairs", "skipped", "before" and "after" (the faults, as rule and frames)."""
    loops = {name: frames}
    found = pac.findings(loops, spec)
    keys = {}
    arrs, ink = pac._arrays(frames, spec, keys)
    rgbs = {code: spec.rgb(colour) for colour, code in keys.items()}
    eye_codes = {keys[spec.eye]} if spec.eye in keys else set()
    n = len(frames)
    out = copy.deepcopy(frames)
    repairs, skipped = [], []
    for fault in found["faults"]:
        if fault["rule"] not in REPAIRED:
            continue
        label = fault.get("name") or f"{fault['rule']} at row {fault.get('row', fault.get('box', [0, 0])[0])}"
        if fault.get("kind", "mark") != "mark":
            skipped.append({"mark": label, "frames": fault["frames"], "why": "a piece apart from the figure"})
            continue
        centre, px, anchor = _place(fault, spec, arrs)
        missing = set(fault["frames"])
        for t in sorted(missing):
            donors = sorted((d for d in range(n) if d not in missing),
                            key=lambda d: (min((d - t) % n, (t - d) % n), d))
            got = None
            for d in donors:
                rows = [y for y, r in enumerate(arrs[d]) if r.any()]
                height = rows[-1] - rows[0] + 1 if rows else len(arrs[d])
                reach = max(2.0, pac.KEEP_REACH * height)
                da = pac._anchor(arrs[d])
                want = (centre[0] + da[0] - anchor[0], centre[1] + da[1] - anchor[1])
                marks = [m for m in pac._pose_marks(arrs[d], ink, rgbs, eye_codes)
                         if math.dist(m["centre"], want) <= reach and px / 3 <= m["px"] <= 3 * px]
                if marks:
                    got = (d, min(marks, key=lambda m: math.dist(m["centre"], want)), reach, height)
                    break
            if got is None:
                skipped.append({"mark": label, "frames": [t], "why": "no frame shows it near its place"})
                continue
            d, mark, reach, height = got
            ta, da = pac._anchor(arrs[t]), pac._anchor(arrs[d])
            guess = (round(ta[0] - da[0]), round(ta[1] - da[1]))
            marks_d = pac._pose_marks(arrs[d], ink, rgbs, eye_codes)
            marks_t = pac._pose_marks(pac._arrays([out[t]], spec, keys)[0][0], ink, rgbs, eye_codes)
            by, used = _landmarks(mark, marks_d, marks_t, guess, reach, rgbs, round(AROUND * height) + 4)
            placed = "by the marks beside it"
            if by is not None:
                dy, dx = by
                share = None
            else:
                placed = "by the pixels around it"
                dy, dx, share = _align(frames[d], out[t], mark["pixels"], guess, math.ceil(reach), spec.rgb, height)
            there = (mark["centre"][0] + dy, mark["centre"][1] + dx)
            moved = [q for q in marks_t if not any(q is u for u in used)
                     and math.dist(q["centre"], there) <= MOVED * reach and mark["px"] / 2 <= q["px"] <= 2 * mark["px"]
                     and (q["code"] == 0) == (mark["code"] == 0)
                     and (not q["code"] or pac._contrast(rgbs[q["code"]], rgbs[mark["code"]]) < pac.KEEP_COLOUR)]
            if moved:                                     # drawn a few px off, not lost: drawing it again doubles it
                q = min(moved, key=lambda q: math.dist(q["centre"], there))
                skipped.append({"mark": label, "frames": [t], "why": f"drawn {math.dist(q['centre'], there):.0f} px "
                                f"off its place at row {q['box'][0]}, column {q['box'][1]}, not lost"})
                continue
            drawn = []
            for y, x in mark["pixels"]:
                ty, tx = y + dy, x + dx
                if 0 <= ty < len(out[t]) and 0 <= tx < len(out[t][0]) and out[t][ty][tx] is not None \
                        and not spec.is_ink(out[t][ty][tx]):
                    out[t][ty][tx] = frames[d][y][x]
                    drawn.append([ty, tx])
            repairs.append({"mark": label, "rule": fault["rule"], "frame": t, "donor": d, "shift": [dy, dx],
                            "placed": placed, "match": None if share is None else round(share, 2), "pixels": drawn,
                            "_was": [frames[t][y][x] for y, x in drawn], "_key": _key(fault)})
    after = pac.findings({name: out}, spec)
    undone = [r for r in repairs if any(_key(f) == r["_key"] or _near(f, r) for f in after["faults"]
                                        if f["rule"] == r["rule"] and r["frame"] in f["frames"])]
    for r in undone:                                      # the check still reads it lost: the drawing did not take
        for (y, x), v in zip(r["pixels"], r["_was"]):
            out[r["frame"]][y][x] = v
        repairs.remove(r)
        skipped.append({"mark": r["mark"], "frames": [r["frame"]], "why": "drawn from frame "
                        f"{r['donor']}, the check still read it lost there, so the drawing was undone"})
    if undone:
        after = pac.findings({name: out}, spec)
    for r in repairs:
        del r["_was"], r["_key"]

    def brief(faults):
        return [{"rule": f["rule"], "frames": f["frames"], "text": f["text"]} for f in faults]
    return out, {"repairs": repairs, "skipped": skipped, "before": brief(found["faults"]),
                 "after": brief(after["faults"])}


def _strip_image(frames, rgb):
    h, w = len(frames[0]), len(frames[0][0])
    im = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        for y, r in enumerate(f):
            for x, v in enumerate(r):
                if v is not None:
                    im.putpixel((k * w + x, y), tuple(rgb(v)[:3]) + (255,))
    return im


def _before_after(before, after, repaired, rgb, path):
    h, w = len(before[0]), len(before[0][0])
    Z = max(2, min(8, 960 // max(1, w * min(len(before), 8))))
    per = min(len(before), 8)
    rows = math.ceil(len(before) / per)
    cell_w, cell_h = w * Z + 6, h * Z + 6
    im = Image.new("RGB", (per * cell_w, rows * 2 * cell_h), (74, 66, 84))
    d = ImageDraw.Draw(im)
    for k in range(len(before)):
        col, row = k % per, k // per
        for line, frames in ((0, before), (1, after)):
            x0, y0 = col * cell_w + 3, (row * 2 + line) * cell_h + 3
            im.paste(pac._img(frames[k], rgb, Z), (x0, y0))
            if line == 1 and k in repaired:
                d.rectangle([x0 - 3, y0 - 3, x0 + w * Z + 2, y0 + h * Z + 2], outline=(80, 230, 90), width=2)
    im.save(path)


def main(argv):
    if "--help" in argv or "-h" in argv or not argv:
        print(__doc__)
        return 0 if argv else 2
    valued = {"--frame", "--frames", "--keep", "--eye", "--ink", "--effects", "--shadow", "--key", "--fps", "--out",
              "--name"}
    try:
        src, got, i = None, {}, 0
        while i < len(argv):
            if argv[i] in valued:
                if i + 1 >= len(argv):
                    raise ValueError(f"{argv[i]} needs a value")
                got[argv[i]] = argv[i + 1]
                i += 2
            elif argv[i].startswith("--") or src is not None:
                raise ValueError(f"unknown argument {argv[i]!r}")
            else:
                src = argv[i]
                i += 1
        if src is None or not os.path.exists(src):
            raise ValueError(f"no such strip, folder or GIF: {src}")

        def count(opt):
            v = got.get(opt)
            if v is not None and (not v.isdigit() or int(v) <= 0):
                raise ValueError(f"{opt} must be a whole number over 0, not {v!r}")
            return int(v) if v else None

        def cols(opt):
            return {pac.hexcol(c) for c in got.get(opt, "").split(",") if c.strip()}
        frame, frames_n = count("--frame"), count("--frames")
        fps = float(got.get("--fps", 30))
        key = pac.hexcol(got["--key"]) if "--key" in got else None
        frames = pac._load(src, frame, frames_n, fps, key, pac._InputBudget())
        if len({pac._frame_size(f) for f in frames}) != 1:
            raise ValueError("the frames differ in size: repair needs one size")
        keep = None
        if "--keep" in got:
            with open(got["--keep"], encoding="utf-8") as fh:
                keep = pac.read_keep(json.load(fh))
        spec = pac.Spec(ink=cols("--ink") or None, effects=cols("--effects"), shadow=cols("--shadow"),
                        eye=pac.hexcol(got["--eye"]) if "--eye" in got else None, fps=fps, style="redrawn",
                        keep=keep)
        name = got.get("--name", os.path.splitext(os.path.basename(os.path.normpath(src)))[0])
        folder = got.get("--out", ".")
        os.makedirs(folder, exist_ok=True)
        targets = [os.path.join(folder, f"{name}_{tail}") for tail in ("repaired.png", "repair.json", "repair.png")]
        inputs = [src] + ([got["--keep"]] if "--keep" in got else [])
        for t in targets:
            if any(os.path.exists(t) and os.path.exists(s) and os.path.samefile(t, s) for s in inputs):
                raise ValueError(f"would write over an input: {t}")
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as e:
        print(f"error: {e}  (--help lists the options)", file=sys.stderr)
        return 2
    out, log = repair(frames, spec)
    _strip_image(out, spec.rgb).save(targets[0])
    with open(targets[1], "w", encoding="utf-8", newline="\n") as fh:
        json.dump(log, fh, indent=1)
        fh.write("\n")
    _before_after(frames, out, {r["frame"] for r in log["repairs"]}, spec.rgb, targets[2])
    print(f"{name}: {len(log['repairs'])} repair(s), {len(log['skipped'])} skipped")
    for r in log["repairs"]:
        how = r["placed"] + ("" if r["match"] is None else f", {r['match']:.0%} of them matching")
        print(f"  {r['mark']}: frame {r['frame']} from frame {r['donor']}, shift {r['shift']}, "
              f"{len(r['pixels'])} px drawn, placed {how}")
    for s in log["skipped"]:
        print(f"  skipped {s['mark']} in frames {s['frames']}: {s['why']}")
    left = [f for f in log["after"] if f["rule"] in REPAIRED]
    for f in log["after"]:
        print(f"  after: {f['text']}")
    print("repaired:", targets[0], " log:", targets[1], " before and after:", targets[2])
    return 1 if left else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        try:
            import repair_sheet_selftest
        except ImportError:
            print("error: --selftest needs repair_sheet_selftest.py beside this file", file=sys.stderr)
            sys.exit(2)
        sys.exit(0 if repair_sheet_selftest.run() else 1)
    sys.exit(main(sys.argv[1:]))
