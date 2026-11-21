"""Animate the beast from its one drawing (creature.py) by posing its parts, the pixel-animate way.

    python animate.py            # writes beast_idle.png, beast_move.png (strips, frames 52x36) and beast_art_8x.png
    python animate.py --poses    # also prints each loop's pose per clock tick and flags a tick equal to the one before

Both loops run on one clock: a new pose every 2 frames at 30 fps (15/s), so the idle and the walk share a rate.
  idle  36 frames (18 poses): a 1-px breath from the belly up; the head's 1-px rise and its small bow, the ears a
        pose behind the head; one flick of the near ear; the tail a chain of four links, each swinging a pose after
        the one before and a little further, so it bends along its length. Every pose differs from the one before.
  move  16 frames (8 poses, one stride): a lateral-sequence walk (near hind, near front, far hind, far front, a
        quarter stride apart). Every leg takes a new hand-drawn pose on every tick, so every step changes about as
        much as the next. The hips rise as a hind leg passes under them and the shoulders a pose later, so the
        back rocks; the head nods a pose after the shoulders, the ears a pose after the head, and the tail's links
        take the hips' rise one after another.
Every move is whole pixels. Nothing is redrawn: each part is the drawing's own pixels, and the only pixels added are
outline, where a pose opens an edge (the outline is drawn last).

Check:  python ../../../skills/pixel-anim-check/pixel_anim_check.py --loop idle=beast_idle.png --loop move=beast_move.png
          --frame 52 --eye "#3ad3a0" --ink "#2a1a2c,#6b3343" --out check --name beast
(--ink names both outline colours: the lit outline is lighter than the check's default ink threshold.)
"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature as C  # noqa: E402

KEY = C.KEY
HOLD = 2                                 # one clock: every pose is held 2 frames
IDLE_POSES, MOVE_POSES = 18, 8
BREATH_SPLIT = 21                        # body rows above this rise with the breath; this row stretches
REAR, FRONT = 23, 28                     # body columns: x < REAR ride the hips, x >= FRONT the shoulders
EAR_BASE = 6                             # the near ear's flick shears it above this row
TAIL_ROOT, TAIL_TIP = (17, 18), (8, 5)   # the tail's axis, to cut it into links across its length
TAIL_LINKS = (0.28, 0.52, 0.76)          # where the links meet, as a share of the axis from the root


def step(v):
    """A whole-pixel round that never lands on -0 and rounds halves away from zero (stable both ways)."""
    return int(math.floor(abs(v) + 0.5)) * (1 if v >= 0 else -1)


def tail_link(x, y):
    (rx, ry), (tx, ty) = TAIL_ROOT, TAIL_TIP
    ax, ay = tx - rx, ty - ry
    s = ((x - rx) * ax + (y - ry) * ay) / (ax * ax + ay * ay)
    return sum(s >= t for t in TAIL_LINKS)


TAIL = C.layer_pixels("T")
TAIL_OF = {k: tail_link(*k) for k in TAIL}


def place_tail(sway, lift):
    """The tail as a chain of four links cut across its length (root, two middles, the white tip). sway[i] and
    lift[i] are link i's own offsets; each link adds its parent's, so a bend travels from the root to the tip. Each
    link is drawn at its parent's place too, under itself, so a joint never opens a gap. The root is drawn last."""
    dx, dy, ox, oy = [], [], 0, 0
    for i in range(4):
        ox, oy = ox + sway[i], oy + lift[i]
        dx.append(ox)
        dy.append(oy)
    out = {}
    for link in (3, 2, 1, 0):
        for at in ((link - 1, link) if link else (0,)):
            for (x, y), ch in TAIL.items():
                if TAIL_OF[(x, y)] == link:
                    out[(x + dx[at], y - dy[at])] = ch
    return out


def place_body(hip, shoulder, breath):
    """The torso in three column bands: the rear rides the hips, the front the shoulders, the middle whichever is up,
    so the back rocks without a step anywhere but where the bands meet. The breath lifts the rows above the belly."""
    mid = max(hip, shoulder)
    out = {}
    for (x, y), ch in C.layer_pixels("B").items():
        up = hip if x < REAR else shoulder if x >= FRONT else mid
        if breath and y <= BREATH_SPLIT:
            out[(x, y - up - breath)] = ch
            if y == BREATH_SPLIT:
                out.setdefault((x, y - up), ch)
        else:
            out[(x, y - up)] = ch
    return out


def place_ear(part, dy, flick):
    """An ear moved with the head; the near ear flicks by shearing back above its base, the base row staying on.
    Returns the ear and a 2-row strip of its base continued downward, to be drawn under the head, so an ear a
    pixel above or below the head never comes off it."""
    out, strip = {}, {}
    px = C.layer_pixels(part)
    base = max(y for _, y in px)
    for (x, y), ch in px.items():
        h = max(0.0, (EAR_BASE - y) / EAR_BASE)
        out[(x - step(flick * h), y + dy)] = ch
        if y == base:
            for k in (1, 2):
                strip[(x, y + dy + k)] = ch
    return out, strip


def render(pose):
    """One frame (a list of rows of chars) from a pose dict."""
    sh = pose["shoulder"]
    far, far_strip = place_ear("F", pose["ears"], 0)
    near, near_strip = place_ear("N", pose["ears"], pose["flick"])
    body = [place_tail(pose["tail_sway"], pose["tail_lift"]),
            place_body(pose["hip"], sh, pose["breath"]),
            far_strip, far,
            C.layer_pixels("K", 0, -sh - pose["breath"]),
            near_strip,
            C.layer_pixels("H", 0, pose["head"]),
            near]
    legs = {p: C.leg_pixels(p, pose["legs"][p]) for p in C.HIPS}
    return C.compose(body, [legs["1"], legs["2"]], [legs["3"], legs["4"]])


STAND = {p: C.STAND for p in C.HIPS}

# The idle, one row per pose (each held 2 frames). The head's 1-px move is staged: the head, then the ears a pose
# later, both on the rise and on the bow. The breath lifts the body from the belly up; the tail takes it a link at a
# time. Head and ears: negative is up.
#        breath head ears flick
IDLE = [(0, 0, 0, 0),     # 0
        (0, 0, 0, 0),     # 1  (the tail moves)
        (1, 0, 0, 0),     # 2  breath in
        (1, -1, 0, 0),    # 3  the head rises
        (1, -1, -1, 0),   # 4  the ears follow
        (1, -1, -1, 0),   # 5
        (1, -1, -1, 0),   # 6
        (0, -1, -1, 0),   # 7  breath out
        (0, 0, -1, 0),    # 8  the head settles
        (0, 0, 0, 0),     # 9  the ears
        (0, 0, 0, 1),     # 10 the near ear flicks
        (0, 0, 0, 2),     # 11
        (0, 0, 0, 1),     # 12
        (0, 1, 0, 0),     # 13 a small bow
        (0, 1, 1, 0),     # 14 the ears follow
        (0, 1, 1, 0),     # 15
        (0, 0, 1, 0),     # 16 the head comes up first
        (0, 0, 0, 0)]     # 17
TAIL_IDLE_PHASE = 0.0
TAIL_AMP = (0.0, 0.55, 0.7, 0.8)         # each link's own swing (px); they add up toward the tip
TAIL_LAG = 0.9                           # rad between one link's swing and the next


def tail_sway(theta, amp=TAIL_AMP, lag=TAIL_LAG):
    return tuple(step(a * math.sin(theta - i * lag)) for i, a in enumerate(amp))


def idle_pose(P):
    breath, head, ears, flick = IDLE[P]
    prev = [IDLE[(P - k) % IDLE_POSES][0] for k in range(4)]            # the breath reaches the links one by one
    lift = (prev[0], prev[1] - prev[0], prev[2] - prev[1], prev[3] - prev[2])
    theta = 2 * math.pi * P / IDLE_POSES + TAIL_IDLE_PHASE
    return {"legs": STAND, "hip": 0, "shoulder": 0, "breath": breath, "head": head, "ears": ears, "flick": flick,
            "tail_sway": tail_sway(theta), "tail_lift": lift}


# The walk. Leg phase offsets in poses (lateral sequence); the hips are up while a hind paw is under them (pose 2
# of a hind leg), the shoulders a pose later.
LEG_OFFSET = {"3": 0, "4": 2, "1": 4, "2": 6}
HIP = [0, 1, 1, 0, 0, 1, 1, 0]
SHOULDER = [1, 1, 0, 0, 1, 1, 0, 0]


def move_pose(k):
    legs = {p: (k - off) % MOVE_POSES for p, off in LEG_OFFSET.items()}
    hip, sh = HIP[k], SHOULDER[k]
    head = -SHOULDER[(k - 1) % MOVE_POSES]                               # the head a pose after the shoulders
    ears = -SHOULDER[(k - 2) % MOVE_POSES]                               # the ears a pose after the head
    hips = [HIP[(k - i) % MOVE_POSES] for i in range(4)]                 # the tail takes the hips' rise link by link
    lift = (hips[0], hips[1] - hips[0], hips[2] - hips[1], hips[3] - hips[2])
    theta = 2 * math.pi * k / MOVE_POSES
    return {"legs": legs, "hip": hip, "shoulder": sh, "breath": 0, "head": head, "ears": ears, "flick": 0,
            "tail_sway": tail_sway(theta, (0.0, 0.0, 0.55, 0.7)), "tail_lift": lift}


def strip(frames):
    im = Image.new("RGBA", (C.W * len(frames), C.H), (0, 0, 0, 0))
    for k, fr in enumerate(frames):
        im.paste(C.to_image(fr), (k * C.W, 0))
    return im


def loops():
    idle = [render(idle_pose(P)) for P in range(IDLE_POSES) for _ in range(HOLD)]
    move = [render(move_pose(k)) for k in range(MOVE_POSES) for _ in range(HOLD)]
    return idle, move


def print_poses():
    """The check before rendering: each tick's pose, and no two ticks alike (a lost update)."""
    for name, n, fn in (("idle", IDLE_POSES, idle_pose), ("move", MOVE_POSES, move_pose)):
        frames = [render(fn(t)) for t in range(n)]
        print(f"{name}:")
        for t in range(n):
            p = fn(t)
            legs = " ".join(f"{k}:{v}" for k, v in sorted(p["legs"].items()))
            same = " SAME AS BEFORE" if frames[t] == frames[t - 1] else ""
            print(f"  {t:2d} hip {p['hip']} shoulder {p['shoulder']} breath {p['breath']} head {p['head']:+d} "
                  f"ears {p['ears']:+d} flick {p['flick']} tail {p['tail_sway']} lift {p['tail_lift']} "
                  f"legs {legs}{same}")


def main():
    idle, move = loops()
    strip(idle).save(os.path.join(HERE, f"{KEY}_idle.png"))
    strip(move).save(os.path.join(HERE, f"{KEY}_move.png"))
    C.to_image(C.ART, 8).save(os.path.join(HERE, f"{KEY}_art_8x.png"))
    if "--poses" in sys.argv:
        print_poses()
    print(f"wrote {KEY}_idle.png ({len(idle)} frames), {KEY}_move.png ({len(move)} frames), {KEY}_art_8x.png; "
          f"frame {C.W}x{C.H}")


if __name__ == "__main__":
    main()
