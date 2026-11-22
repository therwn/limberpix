"""Animate the lizard from its one drawing (creature.py) by posing its parts, the pixel-animate way.

    python animate.py            # writes lizard_idle.png, lizard_move.png, lizard_attack.png (strips, one row, frames
                                 # of one size, printed) and lizard_art_8x.png; in check/ the part strips and the
                                 # rest pose at 1x
    python animate.py --poses    # also prints each loop's pose per clock tick and flags a tick equal to the one before

All three loops play at 30 fps on one clock: a new pose every 2 frames (15/s; the strike alone on ones), so switching
loops never stalls. Every move is whole pixels and nothing is redrawn: each part is the drawing's own pixels, placed
by lizard_rig.py. The legs are posed by two-bone inverse kinematics and turned, not sheared (lizard_legs.py), so a
bent leg keeps its closed outline. The only pixels added are outline where a pose opens an edge (lit ink on the lit
side), the open mouth and the hit spark.

Two rules hold in every loop. The torso is one piece: it moves whole (in the idle's breath too, the legs taking the
move), so its topline and belly line never show a step and no seam opens where the neck lies over it. The head rides
the neck and the neck the back on the same pose: at 1-px steps a head whose bands take a rise a pose apart (the jaw,
the eye band, the casque) reads as clicks, not one motion. The follow-through goes to the tail's coil, a free end.

The far legs are the near ones a value step darker, set 3 px ahead of them (creature.FAR_SHIFT): at rest each stands
behind its near twin, and the walk carries it out from behind half a stride later, so the lizard reads as four legs,
two a side, not four in a row.

  idle    60 frames: one breath of 8 poses three times, the Pixelblog 52 idle, held 3 frames over the rise and the top
          and 2 on the drop. The whole torso rises a pixel, holds, comes back and sinks a pixel below rest, the neck
          and the head with it and the legs stretching and bending under it, the feet planted; the coil loosens after
          the rise and curls back in after the fall, a link a pose from the root (the whorl moving whole, so its shape
          holds), so every pose moves the back or a link of the coil. Once a loop the turret looks about (its rings
          and lit cap turn inside its rim, the pupil leading a pixel further; the pupil never steps more than a pixel)
          and the throat's pouch swells (1, 2, 2, 1 px). Pose 0 is the drawing exactly. The feet never move.
  move    32 frames (16 poses, one stride) over a road scrolling ROAD_SPEED game px a frame. A lateral-sequence
          walk with lateral couplets: the near hind, the near front 2 poses later, then the far hind and the far
          front half a stride after them. A planted foot goes back exactly 1 px a pose (ROAD_SPEED x 2 frames) for
          10 poses, never stopping or catching up; a swinging foot lifts and reaches forward on an eased path over
          6 poses, the leg folding at the knee or elbow as the foot rises. The far feet lift less. The torso rises a
          whole pixel twice a stride (the second rise held a pose longer, so the two steps are not mirror twins),
          whole, with the neck and the head on it; the tail's coil takes it a pose late; the pupil glances back.
  attack  34 frames, a tongue strike. Anticipation (7 small poses, one part moving at a time, none changing over about
          30 % of the figure): the turret locks forward on the prey and the tail's curl swings back; the head draws
          back, then the body rocks back a pixel under it; the head lowers to aim, then the body follows; the head
          draws back and down again, then the throat swells, loaded: the head 3 px back and 2 px down (an arc), the
          body 2 px back over its planted feet, the coil 4 px back and down, root first, each swing of the tail on a
          head pose. Strike (2 frames on ones): the body lunges home and the head 5 px forward, the mandible turns
          down about its hinge (behind and below the eye) as one solid piece, the open mouth solid dark red from the
          hinge to the lip, and the tongue shoots out stretched (a 1-frame smear), then straight to full reach with a
          flash at the club. Held key (7 frames, a moving hold): sparks fly from the club and the tail whips up and
          forward past rest, the body held (a back settling alone would split the torso from the neck over it; settled
          whole, it was a recovery step half the strike's). Recovery (5 poses, steps growing, then shrinking): the
          tongue reels in over three poses and the jaw closes over four; the head comes home a pixel a pose, and the
          turret rolls once as it settles. The feet never leave their pixels.

ROAD_SPEED = 0.5 game px a frame (1 px a pose): show the move over a ground scrolling that fast.

Check (from this folder; 0 faults, 0 warnings):
  python ../../../skills/pixel-anim-check/pixel_anim_check.py --loop idle=lizard_idle.png --loop move=lizard_move.png
         --loop attack=lizard_attack.png --frame 113 --eye "#ffaf2e" --ink "#140f1e,#2f5634"
         --effects "#5e1830,#8e2347,#d84a68,#ff8f97,#fff4e8,#ffc0b0" --action attack:strike:right --speed 0.5
         --parts idle=check/lizard_idle_parts.png --parts move=check/lizard_move_parts.png
         --parts attack=check/lizard_attack_parts.png --squash "#208040,#909020" --palette check/lizard_art.png
         --ref check/lizard_art.png --out check --name lizard
(113 is the frame width, also printed by this script. --ink names both outline colours, the lit one being lighter
than the check's default; --effects names the mouth, the tongue (an effect-like part drawn in its own colours and
without an outline, left out of the part strips) and the hit spark. In the part strips the throat's pouch is its own
part, under 40 px, as it inflates on purpose; the neck is the body's (it lies over the torso's front); the tail is
cut into the root, the coil and the inner whorl. --squash names the two far legs' part colours: their visible area
changes on purpose as they pass behind the near legs once a stride, which is occlusion, not a cut or a pivot gone
wrong. The lizard is not a flier, so --flier does not apply.)
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creature as C  # noqa: E402
import lizard_rig as R  # noqa: E402

KEY = C.KEY
HOLD = 2                                  # one clock: every pose is held 2 frames
ROAD_SPEED = 0.5                          # game px a frame the road scrolls under the move (1 px a pose)
MOVE_POSES = 16
TAIL_LINKS = len(R.SPINE) - 1
STILL = {leg: (0, 0, 0) for leg in R.LEGS}


def rest(**kw):
    pose = dict(body=(0, 0), breath=0, neck=(0, 0), head=(0, 0), lift=(0, 0, 0), turret=(0, 0), roll=(0, 0),
                pupil=(0, 0), throat=0, jaw=0, tongue=None, spark=None, tail=[(0, 0)] * TAIL_LINKS, legs=STILL)
    pose.update(kw)
    return pose


def tail_of(moves):
    """A tail pose from {link: (dx, dy)}; links not named stay."""
    return [moves.get(i, (0, 0)) for i in range(TAIL_LINKS)]


def chain(level, t, lags):
    """The head carried on the neck: (neck dy, (low, eye, cap)) from the torso's level per pose (level(t), 0 or -1
    px), each link taking it lags[link] poses late."""
    neck, low, eye, cap = (level(t - lag) for lag in lags)
    return neck, (low, eye, cap)


# ---- idle -----------------------------------------------------------------------------------------------------------
# One breath of 8 poses, three a loop, timed slow over the rise and the top (3 frames a pose) and quick on the drop (2
# frames): the Pixelblog 52 idle. The whole torso rises a pixel and sinks a pixel below rest, the legs stretching and
# bending under it with the feet planted, and the neck and the head go with it on the same pose: one piece, so no seam
# opens where the neck lies over the torso's front (a back lifted alone over a still belly, with the neck and head
# carried whole, split the torso there) and the head never steps on its own. The follow-through is the tail's, a free
# end: its coil loosens after the back rises and curls back in after it falls, a link a pose, root first, so every
# pose moves the back or a link of the coil. Once a loop the turret looks about and the throat's pouch swells.
BREATH = [0, 1, 1, 1, 0, -1, -1, -1]                        # the torso's height per pose: up 1, rest, down 1
IDLE_HOLDS = [3, 3, 3, 3, 2, 2, 2, 2]                       # frames each pose is held
BREATHS = 3
COIL_OUT = {4: (-1, 0), 5: (-1, 1), 6: (0, 1), 7: (1, 0), 8: (1, 0), 9: (1, 0)}   # each coiled link a pixel out,
COIL_LAG = {4: 1, 5: 2, 6: 3, 7: 4, 8: 4, 9: 4}            # poses behind the back: root first, the whorl whole
IDLE_N = len(BREATH) * BREATHS                              # 24 poses
THROAT = [0] * 14 + [1, 2, 2, 1] + [0] * 6                  # the gular pouch swells once
#            roll       pupil: the turret's shading turns, the pupil leading a pixel further; a pixel a step at most
LOOK = {0: ((0, 0), (0, 0)), 2: ((-1, 0), (-1, 0)), 4: ((-1, 0), (-2, 0)), 7: ((-1, -1), (-1, -1)),
        8: ((0, -1), (0, -1)), 10: ((0, 0), (0, 0)), 14: ((0, 1), (0, 1)), 18: ((1, 0), (1, 0)),
        20: ((0, 0), (0, 0))}
# (pose 0 is the drawing exactly: the back at rest, the coil in, the eye ahead, the pouch flat)


def _at(table, t):
    return table[max(k for k in table if k <= t)]


def coil(t):
    """The coil loosening on the breath as a wave from its root: each link a pixel out while the back was up its lag
    poses ago, so neighbours never differ by more than a pixel and the seams stay closed."""
    out = {i: BREATH[(t - COIL_LAG[i]) % len(BREATH)] > 0 for i in COIL_OUT}
    return tail_of({i: (dx * out[i], dy * out[i]) for i, (dx, dy) in COIL_OUT.items()})


def idle_pose(t):
    t %= IDLE_N
    b = BREATH[t % len(BREATH)]
    roll, pupil = _at(LOOK, t)
    return rest(body=(0, -b), neck=(0, -b), head=(0, -b), roll=roll, pupil=pupil, throat=THROAT[t], tail=coil(t))


# ---- move -----------------------------------------------------------------------------------------------------------
PLANT = 10                                            # poses a foot stays planted (going back 1 px each)
SWING_X = [-3, -1, 1, 3, 4, 5]                        # the swinging foot's eased path forward
SWING_LIFT = {True: [1, 2, 3, 3, 2, 1], False: [1, 1, 2, 2, 1, 1]}     # near feet lift higher than far ones
# a lateral-sequence walk, a foot set down about every quarter stride: the near hind, the near front, the far hind,
# the far front; so the two far legs never hide behind the near ones at once, nor meet under the belly at once
LEG_OFFSET = {"near_hind": 0, "near_front": 2, "far_hind": 8, "far_front": 10}
LEG_SHIFT = {"far_front": 1, "near_front": -1}       # px a stride sits ahead of (or behind) the foot's drawn place
BOB = [0, 0, 0, 0, -1, -1, -1, 0, 0, 0, 0, -1, -1, -1, -1, -1]        # up a whole pixel twice a stride
MOVE_LAGS = (0, 0, 0, 0)       # the neck and the whole head ride the shoulders: no band steps on its own
TAIL_DELAY = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]           # poses each link takes the body's rise after the rump: the
                                                      # coil a pose late, a pixel off it at most
MOVE_PUPIL = [(0, 0)] * 6 + [(-1, 0)] * 6 + [(0, 0)] * 4     # a glance back during the second step


def move_level(t):
    return BOB[t % MOVE_POSES]


def move_pose(P):
    bob = BOB[P]
    neck, lift = chain(move_level, P, MOVE_LAGS)
    tail = [(0, BOB[(P - d) % MOVE_POSES] - bob) for d in TAIL_DELAY]      # against the body, which the tail rides
    return rest(body=(0, bob), neck=(0, neck), lift=lift, pupil=MOVE_PUPIL[P], tail=tail,
                legs={leg: leg_at(leg, P) for leg in R.LEGS})


def leg_at(leg, P):
    near = R.LEGS[leg][2]
    k = (P - LEG_OFFSET[leg]) % MOVE_POSES
    shift = LEG_SHIFT.get(leg, 0)
    if k < PLANT:
        return (PLANT // 2 - k + shift, 0, 0)
    s = k - PLANT
    return (SWING_X[s] + shift, SWING_LIFT[near][s], 0)


# ---- attack ---------------------------------------------------------------------------------------------------------
COILED = (4, 5, 6, 7, 8, 9)


def curl(body, shoulder, coil):
    """The tail in the anticipation, given on the page: the root's three links ride the body (under the rump), the
    curl's shoulder (link 3) and the coil (links 4-9, moving whole, so its whorl keeps its shape) are placed where
    given, so they swing back on poses of their own, not with the body's steps."""
    rel = lambda p: (p[0] - body[0], p[1] - body[1])          # noqa: E731
    return tail_of({3: rel(shoulder), **{i: rel(coil) for i in COILED}})


# the flick after the strike (against the body), lagging it a frame: the coil whips up and forward past rest,
# then settles
FLICK = [tail_of({3: (0, 1), **{i: (-1, 1) for i in COILED}}),
         tail_of({3: (0, 0), **{i: (0, 0) for i in COILED}}),
         tail_of({3: (1, 0), **{i: (1, -1) for i in COILED}}),
         tail_of({3: (1, 0), **{i: (2, -1) for i in COILED}}),
         tail_of({3: (0, 0), **{i: (1, -1) for i in COILED}}),
         tail_of({i: (1, 0) for i in COILED})]
LOCK = dict(turret=(1, 0), roll=(1, 0))                        # the turret locked forward on the prey


def _a(**kw):
    """An anticipation pose: the turret locked, the tail given on the page as (shoulder, coil)."""
    body = kw.get("body", (0, 0))
    shoulder, coil = kw.pop("curl")
    return dict(LOCK, tail=curl(body, shoulder, coil), **kw)


# (frames, pose); the head and the neck are given on the page. One part moves a pose: the head leads, the body
# follows a pose later, the tail swings back with the head's poses, the neck between the body and the head.
ATTACK = [(2, dict()),
          (2, _a(curl=((-1, 0), (0, 0)))),                                         # the eye locks on
          (2, _a(head=(-1, 0), neck=(-1, 0), curl=((-1, 0), (-1, 1)))),            # the head draws back ...
          (2, _a(head=(-1, 0), neck=(-1, 0), body=(-1, 0), curl=((-1, 0), (-1, 1)))),     # ... the body rocks back
          (2, _a(head=(-2, 1), neck=(-1, 1), body=(-1, 0), curl=((-1, 1), (-2, 1)))),     # the head lowers ...
          (2, _a(head=(-2, 1), neck=(-2, 1), body=(-2, 0), curl=((-2, 1), (-2, 1)))),     # ... the body follows
          (2, _a(head=(-3, 2), neck=(-2, 1), body=(-2, 0), throat=1, curl=((-2, 1), (-3, 1)))),   # aimed (an arc)
          (2, _a(head=(-3, 2), neck=(-2, 1), body=(-2, 0), throat=2, curl=((-2, 1), (-4, 1)))),   # loaded
          (1, dict(LOCK, head=(0, 1), neck=(0, 1), jaw=3, tongue=(86, 5), tail=curl((0, 0), (0, 1), (-1, 1)))),
          # strike: a smear ...
          (1, dict(LOCK, head=(2, 0), neck=(1, 0), jaw=4, tongue=(102, 0), spark=1, tail=FLICK[0])),   # contact
          (2, dict(LOCK, head=(2, 0), neck=(1, 0), jaw=4, tongue=(102, 0), spark=2, tail=FLICK[1])),   # held key:
          (2, dict(LOCK, head=(2, 0), neck=(1, 0), jaw=4, tongue=(102, 0), tail=FLICK[2])),  # the tail whips on
          (2, dict(LOCK, head=(2, 0), neck=(1, 0), jaw=4, tongue=(102, 0), tail=FLICK[3])),  # through the hold,
          (2, dict(LOCK, head=(2, 0), neck=(1, 0), jaw=3, tongue=(88, 0), tail=FLICK[4])),   # reel in,
          (2, dict(head=(2, 0), neck=(1, 0), jaw=2, tongue=(76, 0), tail=FLICK[5])),         # the turret unlocks,
          (2, dict(head=(1, 0), neck=(0, 0), jaw=1)),                                        # the head comes back,
          (2, dict(jaw=0)),                                                                # home, the jaw shut
          (2, dict(roll=(0, -1)))]


def attack_poses():
    return [(n, rest(**kw)) for n, kw in ATTACK]


# ---- frames, strips -------------------------------------------------------------------------------------------------
def loops():
    """{loop: [(rendered pose, frames held)]} for every loop."""
    return {"idle": [(R.render(idle_pose(P)), IDLE_HOLDS[P % len(BREATH)]) for P in range(IDLE_N)],
            "move": [(R.render(move_pose(P)), HOLD) for P in range(MOVE_POSES)],
            "attack": [(R.render(p), n) for n, p in attack_poses()]}


def frame_box(all_loops):
    """One fixed box for every frame of every loop: the union of all poses, with a pixel of air round it."""
    pts = [p for poses in all_loops.values() for fr, _ in poses for p in fr]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs) - 1, min(ys) - 1, max(xs) + 2, max(ys) + 2


def image(fr, box, parts=False):
    x0, y0, x1, y1 = box
    im = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    for (x, y), (ch, part) in fr.items():
        if parts and part in R.EFFECT_PARTS:
            continue                                  # an effect, not a rig part: left out of the part strip
        h = R.PART_RGB[part] if parts else R.RGB[ch]
        im.putpixel((x - x0, y - y0), tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    return im


def strip(poses, box, parts=False):
    frames = [image(fr, box, parts) for fr, n in poses for _ in range(n)]
    im = Image.new("RGBA", (frames[0].width * len(frames), frames[0].height), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        im.paste(f, (k * f.width, 0))
    return im


def print_poses():
    """The check before rendering: each tick's pose, and no tick equal to the one before (a lost update)."""
    for name, poses in (("idle", [idle_pose(t) for t in range(IDLE_N)]),
                        ("move", [move_pose(t) for t in range(MOVE_POSES)]),
                        ("attack", [p for _, p in attack_poses()])):
        frames = [R.render(p) for p in poses]
        print(f"{name}:")
        for t, p in enumerate(poses):
            same = "  SAME AS BEFORE" if frames[t] == frames[t - 1] else ""
            legs = " ".join(f"{k[:1]}{k.split('_')[1][:1]}{v[:2]}" for k, v in p["legs"].items())
            print(f"  {t:2d} body {p['body']} breath {p['breath']} neck {p['neck']} head {p['head']} "
                  f"lift {p['lift']} turret {p['turret']} roll {p['roll']} pupil {p['pupil']} throat {p['throat']} "
                  f"jaw {p['jaw']} tongue {p['tongue']} spark {p['spark']} tail {p['tail'][2:]} {legs}{same}")


def main():
    all_loops = loops()
    box = frame_box(all_loops)
    os.makedirs(os.path.join(HERE, "check"), exist_ok=True)
    for name, poses in all_loops.items():
        strip(poses, box).save(os.path.join(HERE, f"{KEY}_{name}.png"))
        strip(poses, box, parts=True).save(os.path.join(HERE, "check", f"{KEY}_{name}_parts.png"))
    image(R.render(rest()), box).save(os.path.join(HERE, "check", f"{KEY}_art.png"))
    C.to_image(C.crop(C.ART), 8).save(os.path.join(HERE, f"{KEY}_art_8x.png"))
    if "--poses" in sys.argv:
        print_poses()
    counts = ", ".join(f"{k} {sum(n for _, n in v)}" for k, v in all_loops.items())
    print(f"wrote {KEY}_idle/move/attack.png (frames: {counts}), FRAME_W {box[2] - box[0]} "
          f"(frames {box[2] - box[0]}x{box[3] - box[1]}); ROAD_SPEED {ROAD_SPEED} px a frame")


if __name__ == "__main__":
    main()
