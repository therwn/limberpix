"""Known losses on real generated frames: in a strip prepared from an image model's sheet (prepare_sheet.py), a mark
of frame 0 is erased (painted over with the colour around it) in chosen frames where the keep check finds it. The
check must name exactly those frames, and the repair must put the mark back where it was. The sheet's own model
noise stays real; only the loss is made, so the answer is known.

    python tests/known_losses.py STRIP.png FRAME_W [FPS]

For each mark of frame 0 the keep check finds in most frames, and each drop pattern:
  vote   lostmark alone (no keep list): frames named for that mark against the frames erased
  keep   a keep list holding that mark alone: frames named against the frames erased
  repair repair_sheet with that keep list: the erased frames the keep check finds the mark in again, the overlap
         of the drawn pixels with the erased ones, and whether the other frames stayed as they were
Frames where the keep check already misses the mark are left out of the counts.
"""
import copy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "skills", "pixel-anim-check")
sys.path.insert(0, SKILL)
import pixel_anim_check as pac  # noqa: E402
import repair_sheet as rs  # noqa: E402

PATTERNS = [(2,), (2, 5), (1, 4, 6), (0,), (3, 4)]


def frame_marks(frame, spec):
    keys = {}
    (a,), ink = pac._arrays([frame], spec, keys)
    ink |= {c for col, c in keys.items() if spec.is_ink(col)}
    rgbs = {c: spec.rgb(col) for col, c in keys.items()}
    return pac._pose_marks(a, ink, rgbs, set(), None), a


def locate(frame, feature, anchor, spec):
    """The frame's mark standing for feature (as kept() finds it), or None."""
    marks, a = frame_marks(frame, spec)
    rows = [y for y, r in enumerate(a) if r.any()]
    reach = max(2.0, pac.KEEP_REACH * (rows[-1] - rows[0] + 1))
    pr, pc = pac._anchor(a)
    t, l, b, r = feature["box"]
    want = ((t + b) / 2 + pr - anchor[0], (l + r) / 2 + pc - anchor[1])
    near = [m for m in marks if math.dist(m["centre"], want) <= reach
            and feature["px"] / 3 <= m["px"] <= 3 * feature["px"]]
    return min(near, key=lambda m: math.dist(m["centre"], want)) if near else None


def erase(frame, mark):
    """Paint the mark's pixels with the commonest colour of the pixels around it."""
    own = set(mark["pixels"])
    ring = [frame[y + dy][x + dx] for y, x in mark["pixels"] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
            if (y + dy, x + dx) not in own and 0 <= y + dy < len(frame) and 0 <= x + dx < len(frame[0])
            and frame[y + dy][x + dx] is not None]
    fill = max(set(ring), key=ring.count)
    for y, x in mark["pixels"]:
        frame[y][x] = fill


def named(faults, rule, near=None):
    out = set()
    for f in faults:
        if f["rule"] != rule:
            continue
        if near is not None and f.get("row") is not None and math.dist((f["row"], f["column"]), near) > 6:
            continue
        out |= set(f["frames"])
    return out


def main():
    strip, fw = sys.argv[1], int(sys.argv[2])
    fps = float(sys.argv[3]) if len(sys.argv) > 3 else 8
    frames = pac.load(strip, frame=fw)
    spec = pac.Spec(fps=fps, style="redrawn")
    cand = pac.features(frames[0], spec)
    anchor = cand["anchor"]
    rows = []
    for f in cand["features"]:
        if f["kind"] != "mark":
            continue
        f = dict(f, keep=True, name=f"mark {f['id']}")
        keep = dict(cand, features=[f], transient=[])
        kspec = pac.Spec(fps=fps, style="redrawn", keep=keep)
        where = [locate(fr, f, anchor, spec) for fr in frames]
        base_keep = named(pac.findings({"idle": frames}, kspec)["faults"], "keep")
        base_vote = named(pac.findings({"idle": frames}, spec)["faults"], "lostmark", tuple(f["box"][:2]))
        base = base_keep | {k for k, m in enumerate(where) if m is None}
        if len(base) > len(frames) // 2:                  # not a feature the frames hold
            continue
        for pattern in PATTERNS:
            if max(pattern) >= len(frames) or set(pattern) & base:
                continue
            broken = copy.deepcopy(frames)
            for k in pattern:
                erase(broken[k], where[k])
            truth = set(pattern)
            vote = named(pac.findings({"idle": broken}, spec)["faults"], "lostmark", tuple(f["box"][:2]))
            keepf = named(pac.findings({"idle": broken}, kspec)["faults"], "keep")
            out, log = rs.repair(broken, kspec)
            still = named(pac.findings({"idle": out}, kspec)["faults"], "keep") & set(pattern)
            back = []
            for k in pattern:                             # where the drawing went, against the erased mark
                drawn = {tuple(p) for r in log["repairs"] if r["frame"] == k for p in r["pixels"]}
                was = set(map(tuple, where[k]["pixels"]))
                back.append(len(drawn & was) / len(drawn | was) if drawn | was else 0.0)
            others = all(out[k] == broken[k] for k in range(len(frames)) if k not in truth | base)
            rows.append((f["id"], f["px"], pattern, sorted(vote - base_vote), sorted(keepf - base_keep),
                         round(sum(back) / len(back), 2), others, sorted(base), sorted(still)))
    name = os.path.basename(strip)
    print(f"{name}: {len(rows)} cases from {len({r[0] for r in rows})} marks (frames already missing a mark left out)")
    hit = {"vote": [0, 0, 0], "keep": [0, 0, 0]}
    for mid, px, pattern, vote, keepf, back, others, base, still in rows:
        for key, got in (("vote", set(vote)), ("keep", set(keepf))):
            hit[key][0] += len(got & set(pattern))
            hit[key][1] += len(got - set(pattern))
            hit[key][2] += len(set(pattern) - got)
        print(f"  mark {mid} ({px} px, already missing {base}) erased {list(pattern)}: vote {vote} keep {keepf} "
              f"repaired: overlap {back:.0%}, still missing {still}"
              f"{'' if others else ' OTHER FRAMES CHANGED'}")
    for key, (tp, fp, fn) in hit.items():
        print(f"  {key}: {tp} found, {fp} extra, {fn} missed")
    reps = [r[5] for r in rows]
    if reps:
        erased = sum(len(r[2]) for r in rows)
        left = sum(len(r[8]) for r in rows)
        print(f"  repair: {erased - left} of {erased} erased frames hold the mark again by the keep check; "
              f"drawn where it was: mean overlap {sum(reps) / len(reps):.0%}; other frames untouched: "
              f"{all(r[6] for r in rows)}")


if __name__ == "__main__":
    main()
