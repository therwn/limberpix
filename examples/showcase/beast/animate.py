"""Animate the beast from its one drawing (creature.py) by posing its parts, the pixel-animate way.

    python animate.py            # writes beast_idle.png, beast_move.png, beast_attack.png (strips, one row) and
                                 # beast_art_8x.png, plus in check/ the part strips, the drawing at 1x and its palette
    python animate.py --poses    # also prints each loop's pose per clock tick and flags a tick equal to the one before

The loops play at 30 fps. The move runs on ones (a new pose every frame, so a planted paw keeps pace with a road
scrolling a pixel a frame); the idle's poses are held 3 frames over the rise and the top and 2 on the drop; the
attack's on twos, its strike on ones. Every move is whole pixels and nothing is redrawn: each part is the drawing's
own pixels, placed by beast_rig.py (the legs, the neck and the tail bent row by row between their joints, the trunk
moved whole or stretched in whole-pixel column steps, the ears laid back by sliding their rows, a forepaw and the
jaw turned whole about their joints by three shears, which keep every pixel); the only pixels added are the open
mouth's dark inside, the far leg's shadow in a pocket of air two crossing legs close, and the outline, drawn last
where a pose opens an edge (the lit line where the air is above or to the left, the ink elsewhere).

Two rules hold in every loop. The torso is one piece: the trunk is one layer, and every pose change moves it whole
(the paws stay where they are and the legs take the move) or, in the strike alone, stretches it; it is never tilted
by a lone pixel, so its topline and its belly line never show a step. In the idle and the move the trunk, the neck,
the head and the ears are one piece too: at 1-px steps a head moved a pixel off its body opens a seam at the neck,
and a chain that takes a rise a pose at a time (the trunk, then the neck, then the muzzle, then the ears) reads as
four clicks, not one motion. The follow-through goes to the tail, a free end, and never pulls its tip more than a
pixel off the rump (further, the tail's rows stretch).

  idle    60 frames: one breath of 8 poses three times (0.67 s each), the Pixelblog 52 idle. The trunk, with the
          neck, the head and the ears, rises a pixel, holds over the top, comes back, sinks a pixel below rest and
          holds, the legs stretching and bending under it with the paws planted; the poses are held 3 frames over
          the rise and the top and 2 on the drop, slow at the top and quick going down. The tail's tip trails the
          rump by a pose and swings a pixel out over the bottom of the breath, so every pose moves the body or the
          tip. Pose 0 is the drawing exactly.
  move    32 frames (one stride, on ones) over a road scrolling ROAD_SPEED game px a frame. A lateral-sequence
          walk: near hind, near fore, far hind, far fore, a quarter stride (8 frames) apart. A planted paw goes back
          exactly 1 px a frame (ROAD_SPEED) for 20 frames, never stopping or catching up, so it stays on its pixel
          of road; while it is planted its hock stays a set step behind it (behind at contact and passing, opening
          as the leg pushes off), so the hind leg keeps its drawn angle. A swinging paw lifts and reaches forward
          on an eased path over 12 frames (keys every 2 frames, the frame between at the mid place): a hind paw
          4 px, the hock flexing back; a forepaw 3 px, the elbow drawing back and the paw turned back about the
          wrist (40, 65, then 90 degrees, its sole facing back, under the forearm's end; a turn held 2 frames),
          then opening (60, 15) and snapping forward flat. The far legs lift and fold less. The trunk, the neck, the
          head and the ears rise a whole pixel together as a hind leg passes under them, twice a stride (each level
          held 8 frames); the tail sways once a step, its wave stepping on twos.
  attack  40 frames, a lunge and a bite, timed 5:1:7 (anticipation : strike : recovery, in poses).
          Anticipation (5 poses, 14 frames): the head dips and the ears start back; the trunk sinks 2 px and rocks
          back, the elbows fold back; the head draws back and the ears lie flat; the trunk goes back again,
          crouched low on the folded hind legs (the elbows bent, the tail tucked); wound up 4 frames, the trunk
          sinking a pixel more (4 px down and 3 back) and the head with it. The head and the trunk take turns, the
          head a pose ahead, so each step is a pixel or two against the strike's seven. Wherever the head is
          carried off its rest place the neck goes with it whole, over its own fur at rest (beast_rig.neck_fur), so
          no seam or stripe opens at the shoulder.
          Strike (2 frames on ones): the trunk lunges 5 px on one line from the planted hind paws, stretched a
          pixel, the forepaws lift with the push (to come down braced), the jaw opens, the head is dragged a beat
          behind, the ears dragged back and the tail left behind (its tip stays where it was, 6 px behind the
          rump's travel); then the rump catches up and the head and neck shoot the last pixels forward, the jaw
          wide (turned down about its hinge, its fur side and tip under the open mouth, the fangs bared), and the
          tail's root whips up and back while the tip still hangs; speed lines behind the rump and a puff of dust
          off the heels (pale, then shorter and darker).
          Held key (10 frames, a moving hold): the jaws snap shut with a star of light at the teeth, then its sparks
          thrown out; the head tugs back a pixel, the trunk sinks a pixel whole and the head follows it a pose
          later, then, still biting, the trunk pulls back a pixel whole. The tail's tip follows its root up and back
          (4 px over rest, swung out behind), then the tail comes down through the hold, the root first and the tip
          a pose behind. The ears stay flat.
          Recovery (7 poses): the trunk comes back a pixel whole, rises a pixel whole (the neck and the back of the
          head with it), then comes home; the head follows a pose behind, the muzzle rising a pixel past rest for
          two poses, the ears a pose after it; then the neck leads the head down and the ears come with it. The
          tail swings on past rest under the haunch, the tip a pose late. The last pose is the rest pose (the
          drawing) but for the tail's tip, still a pixel forward, so the idle follows on without a pop. The hind
          paws never leave their pixels.

ROAD_SPEED = 1.0 game px a frame (2 px a pose; 30 px/s at 30 fps): show the move over a ground scrolling that fast.

Check (from this folder; 0 faults, 0 warnings):
  python ../../../skills/pixel-anim-check/pixel_anim_check.py --loop idle=beast_idle.png --loop move=beast_move.png
         --loop attack=beast_attack.png --frame 93 --eye "#f2aa3c"
         --ink "#120f19,#191a2e,#242844,#323a5c,#404e78,#566594"
         --effects "#fff9e6,#ffd25e,#c3cdf0,#7d89b8" --action attack:strike:right --speed 1.0
         --parts idle=check/beast_idle_parts.png --parts move=check/beast_move_parts.png
         --parts attack=check/beast_attack_parts.png --squash "#8c8c8c,#208040,#909020"
         --palette check/beast_palette.png --ref check/beast_art.png --out check --name beast
(--frame is the width this script prints. --ink names the outline: the ink and the lit line, the fur ramp's darks
a..e on the top and left edges. --effects names the flash, the sparks, the speed lines and the dust. --squash names
three parts whose seen area changes on purpose: the neck, which stretches between the shoulders and the head, and
the two far legs, which pass behind the near legs in the walk. The palette image is the drawing with its mouth
layers laid out beside it, since the mouth's colours lie hidden under the head at rest.)
"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import beast_rig as R  # noqa: E402
import creature as C  # noqa: E402

KEY = C.KEY
HOLD = 2                                   # the attack's poses are held 2 frames unless the table says otherwise
ROAD_SPEED = 1.0                           # game px a frame the road scrolls under the move
STAND = R.stand


def sway(t, period, amps, lag, phase=0.0):
    """Each tail link's own sideways move (px) for one wave running down the tail: link i moves amps[i] * sin,
    i * lag poses after the root. Amplitudes are 0 or over 1 px, so a link that moves takes a whole pixel and keeps
    it a third of the wave (never a 1-pose blip)."""
    return [a * math.sin(2 * math.pi * (t - i * lag) / period + phase) for i, a in enumerate(amps)]


# ---- idle ------------------------------------------------------------------------------------------------------------
# One breath of 8 poses, timed slow over the rise and the top (3 frames a pose, 0.1 s) and quick on the drop (2
# frames): the Pixelblog 52 idle. Every pose moves the body's mass or the tail's tip, never a lone small part. The
# trunk, the neck, the head and the ears are one piece: they rise and fall together, so no seam opens at the neck
# and no ear hops on its own; the legs take the move, stretching and bending under it with the paws planted. The lag
# is the tail's: its tip trails the rump by a pose, never more than a pixel off it (a tail pulled further stretches),
# and swings a pixel out over the bottom of the breath. Three breaths a loop.
TORSO = [0, 1, 1, 1, 0, -1, -1, -1]                      # the trunk's height per pose, up positive: a pixel above
IDLE_HOLDS = [3, 3, 3, 3, 2, 2, 2, 2]                    # rest and a pixel below; frames each pose is held
TIP_OUT = range(3, 7)                                    # poses the tail's tip swings a pixel back (out)
BREATHS = 3


def idle_pose(P):
    P %= len(TORSO)
    trunk = -TORSO[P]
    tip = TORSO[P] - TORSO[P - 1] if P else 0               # a pose behind the rump, 1 px at most; caught up on
                                                             # pose 0, which is the drawing exactly
    return STAND(body=(0, trunk, trunk, 0), tail=[(0, 0), (0, 0), (0, 0), (-int(P in TIP_OUT), tip)])


# ---- move ------------------------------------------------------------------------------------------------------------
# On ones: a new pose every frame. Drawn in place over a road scrolling ROAD_SPEED px a frame, a planted paw goes
# back exactly that much every frame, so it stays on its pixel of road; held two frames it would lag the road a
# pixel and then catch up, and the feet would judder against it. The trunk, the neck, the head and the ears rise and
# fall together, one piece, twice a stride; the tail sways as a chain on its own wave.
MOVE_FRAMES = 32
PLANT, SWING = 20, 12                                     # frames a paw stays planted, then swings forward
STEP = int(ROAD_SPEED)                                    # 1 px a frame
SWING_X = [-8, -5, -1, 3, 7, 9, 9]                        # the swinging paw's eased path forward, a key every
SWING_LIFT = {("hind", True): [1, 3, 4, 4, 2, 1, 1], ("hind", False): [1, 2, 3, 3, 2, 1, 1],   # 2 frames, the
              ("front", True): [1, 2, 3, 3, 2, 1, 1], ("front", False): [1, 1, 2, 2, 1, 1, 1]}  # frame between
                                                          # taking the mid place; the near legs lift higher
HOCK = {True: [(-1, 0), (-2, -1), (-1, -1), (0, 0), (0, 0), (0, 0)],  # the hock flexes back as the hind paw lifts
        False: [(-1, 0), (-1, 0), (-1, -1), (0, 0), (0, 0), (0, 0)]}
HOCK_PLANTED = [-1, -1, -1, -1, -1, 0, 0, 0, 1, 1]       # the hock against the planted paw: behind it, then opening
ELBOW = {True: [(0, 0), (-1, 0), (-2, 0), (-1, 0), (-1, 0), (0, 0)],   # the elbow draws back as the paw lifts (the
         False: [(0, 0), (-1, 0), (-1, 0), (0, 0), (0, 0), (0, 0)]}     # forearm angled forward as the paw reaches)
FOLD = {True: [40, 65, 90, 60, 15, 0], False: [20, 35, 45, 25, 0, 0]}   # the forepaw folds back at the wrist
                                                                      # (degrees), then snaps forward
LEG_OFFSET = {"near_hind": 0, "near_front": 8, "far_hind": 16, "far_front": 24}   # lateral sequence
HIPS_UP = range(6, 14)                                    # frames (mod 16) with the trunk a pixel up
MOVE_TAIL = dict(period=8, amps=[0, 1.05, 1.1, 1.2], lag=1, phase=-1.0)   # read every 2 frames: the tail's
                                                                             # wave steps on twos
HOCK_T = (R.HOCK_Y - R.HIP_Y) / (R.HPAW_Y - R.HIP_Y)


def leg_at(leg, t):
    near = leg.startswith("near")
    k = (t - LEG_OFFSET[leg]) % MOVE_FRAMES
    if k < PLANT:
        foot = PLANT // 2 * STEP - 1 - STEP * k              # 9 .. -10, back 1 px a frame
        if leg.endswith("hind"):                      # the hock kept a set step behind the paw, not on the
            return (foot, 0, foot + HOCK_PLANTED[k // 2] - R.rnd(foot * HOCK_T), 0, 0)   # line from the hip
        return (foot, 0, 0, 0, 0)
    s = k - PLANT                                             # the swing: 12 frames forward
    i, half = s // 2, s % 2
    lifts = SWING_LIFT[(leg.split("_")[1], near)]
    x = R.rnd(SWING_X[i] + (SWING_X[i + 1] - SWING_X[i]) * half / 2)
    lift = max(1, R.rnd(lifts[i] + (lifts[i + 1] - lifts[i]) * half / 2))
    if leg.endswith("hind"):
        j, fold = HOCK[near][s // 2], 0
    else:
        j, fold = ELBOW[near][s // 2], FOLD[near][s // 2]   # the paw's turn steps on twos: a turn held 2 frames
    return (x, lift, j[0], j[1], fold)


def hips(t):
    return -1 if t % 16 in HIPS_UP else 0


def move_pose(t):
    trunk = hips(t)                                          # the trunk, neck, head and ears rise whole, one piece
    tail = [(R.rnd(v), 0) for v in sway(t // 2, **MOVE_TAIL)]
    return STAND(body=(0, trunk, trunk, 0), tail=tail, legs={leg: leg_at(leg, t) for leg in LEG_OFFSET})


# ---- attack ----------------------------------------------------------------------------------------------------------
def legs(hock=(0, 0), elbow=(0, 0), near_front=(0, 0, 0), far_front=(0, 0, 0)):
    """The attack's legs: the hind paws stay planted, each hock at hock = (x against its paw, as drawn at 0; dy), so
    the metatarsus keeps its drawn slant however far the hips go; each forepaw at (dx, lift, fold)."""
    nf, ff = near_front, far_front
    return {"near_hind": (0, 0) + hock + (0,), "far_hind": (0, 0) + hock + (0,),
            "near_front": (nf[0], nf[1]) + elbow + (nf[2],), "far_front": (ff[0], ff[1]) + elbow + (ff[2],)}


def streaks(rear_dx, long):
    """Speed lines behind the lunging rump: long and pale on the strike frame, then shorter and darker (the trail
    fading)."""
    ch, n = ("z", 7) if long else ("Z", 4)
    return [(x, y, ch) for y, x1 in ((27, 3), (33, 2), (39, 4)) for x in range(x1 + rear_dx - n, x1 + rear_dx)]


DUST = [[(0, 0), (1, 0), (-1, 0), (0, -1), (1, -1)],            # a puff kicked back off the hind paws' heels:
        [(0, 0), (1, 0), (-1, 0), (-2, 0), (-3, 0), (0, -1), (-1, -1), (1, -1), (-2, -1), (-1, -2), (0, -2)],
        [(-2, -1), (-4, 0), (-3, -2), (0, -2), (-1, -3), (1, -1)]]  # small, bigger, thinning out (about 4x4 px)


def dust(stage):
    return [(18 + dx, 51 + dy, "z" if stage < 2 else "Z") for dx, dy in DUST[stage]]


STAR = [((0, 0), "x"), ((1, 0), "x"), ((-1, 0), "x"), ((0, 1), "x"), ((0, -1), "x"), ((2, 0), "x"), ((0, -2), "x"),
        ((0, 2), "y"), ((3, 0), "y"), ((-2, 0), "y"), ((0, -3), "y"), ((0, 3), "y"),
        ((2, -2), "y"), ((-2, -2), "y"), ((2, 2), "y"), ((-2, 2), "y")]
BURST = [((4, -1), "y"), ((1, -4), "y"), ((3, 3), "y"), ((-1, 4), "Z"), ((5, 1), "Z"), ((-3, -3), "Z"),
         ((3, -4), "Z")]


def bite_fx(at, stage):
    """The bite's flash just ahead of the teeth: a four-pointed star, its long arm forward, with four small
    diagonal points (stage 0); then its sparks thrown out round where it was, uneven, the far ones fading
    (stage 1)."""
    x, y = at
    return [(x + dx, y + dy, ch) for (dx, dy), ch in (STAR if stage == 0 else BURST)]


def chain(*xs):
    """Tail link moves from each link's place against the rump (root, two middles, tip), in px along x."""
    return [(x - (xs[i - 1] if i else 0), 0) for i, x in enumerate(xs)]


# The tail: each entry (link places, lift); the lift raises the tail's columns by their reach behind the root
# (beast_rig.place_tail), (px, span) with a short span lifting the hanging length bodily, the root turning first.
TUCK1 = (chain(0, 0, 1, 1), 0)                 # tucked under on the crouch,
TUCK = (chain(0, 0, 1, 2), 0)
TRAIL = (chain(0, -1, -2, -4), 0)              # left behind as the rump shoots forward, the tip trailing 4 px,
WHIP = (chain(0, -2, -3, -3), (2, 6))          # the root whipping up and back first, the tip still low,
TAIL_HOLD = [(chain(0, -2, -4, -7), 5),        # then the tip up and back (5 px over rest), held out while the
             (chain(0, -1, -3, -7), (5, 22)),  # jaws hold, coming down through the hold root first, the tip a
             (chain(0, -1, -2, -5), (3, 20)),  # pose behind,
             (chain(0, 0, -1, -3), (2, 20)),
             (chain(0, 0, -1, -2), (1, 20))]
TAIL_BACK = [(chain(0, 0, 0, -1), 0),          # and on past rest under the haunch in the recovery (the middle,
             (chain(0, 1, 1, 0), 0),           # then the tip a pose late), settling back
             (chain(0, 1, 2, 2), 0),
             (chain(0, 0, 1, 2), 0),
             (chain(0, 0, 0, 1), 0)]
BRACE = legs((0, 0), (1, 0))                             # on the bite the forelegs braced, the elbows in
#    frames  body (dx, rear_dy, front_dy, stretch): the rear rides dx, the front dx + stretch; head against the front.
# The trunk is one piece: every change moves it whole, or turns it by a tilt of 2 px spread over its length as a
# staircase; it never moves its rear and its front apart by a lone pixel. The anticipation moves the trunk on every
# other pose and only the head, the ears or the tail between, so its steps stay small against the strike's.
ATTACK = [(2, dict()),
          # anticipation: the head dips and the ears start back; the trunk sinks 2 px and rocks back, the elbows fold;
          # the head draws back and the ears lie flat; the trunk back again, crouched on the hind legs; wound up
          (2, dict(head=(0, 1), pin=2, tail=TUCK1)),
          (2, dict(body=(-1, 2, 2, 0), head=(0, 1), ears=(0, 1), pin=3, tail=TUCK, legs=legs((-1, 0), (-2, 0)))),
          (2, dict(body=(-1, 2, 2, 0), head=(-1, 1), ears=(0, 1), pin=5, tail=TUCK, legs=legs((-1, 0), (-2, 0)))),
          (2, dict(body=(-3, 3, 3, 0), head=(-1, 1), ears=(0, 1), pin=5, tail=TUCK, legs=legs((-3, 1), (-3, 0)))),
          (4, dict(body=(-3, 4, 4, 0), head=(-1, 1), ears=(0, 1), pin=5, tail=TUCK,            # wound up (held)
                   legs=legs((-3, 1), (-3, 1)))),
          # strike, on ones: the trunk lunges first, stretched, the forepaws lifting to reach, the head dragged a beat
          # behind with the jaw opening; then the rump catches up, the head and neck shoot the last pixels forward,
          # the jaw wide, the ears dragged back, the tail left behind, then whipped up from the root
          (1, dict(body=(2, 0, 0, 1), head=(-2, -1), ears=(-2, 1), pin=5, jaw=3, tail=TRAIL, fx="strike",
                   legs=legs((0, 0), (1, 0), (1, 2, 20), (0, 1, 0)))),
          (1, dict(body=(3, 0, 0, 0), head=(3, -1), ears=(-1, 1), pin=5, jaw=5, tail=WHIP, fx="contact", legs=BRACE)),
          # the bite, held: the jaws snap shut and tug back a pixel, the trunk sinks whole, the head a pose later;
          # then, still biting, the trunk pulls back a pixel whole
          (2, dict(body=(3, 0, 0, 0), head=(2, -1), ears=(0, 1), pin=5, tail=TAIL_HOLD[0], fx="flash", legs=BRACE)),
          (2, dict(body=(3, 1, 1, 0), head=(2, -2), ears=(0, 1), pin=5, tail=TAIL_HOLD[1], fx="sparks", legs=BRACE)),
          (2, dict(body=(3, 1, 1, 0), head=(0, 0), ears=(0, 1), pin=5, tail=TAIL_HOLD[2], legs=BRACE)),
          (2, dict(body=(2, 1, 1, 0), head=(1, 0), ears=(0, 1), pin=5, tail=TAIL_HOLD[3], legs=BRACE)),
          (2, dict(body=(2, 1, 1, 0), head=(0, -1), ears=(0, 1), pin=4, tail=TAIL_HOLD[4], legs=BRACE)),
          # recovery: the trunk comes back a pixel whole, up a pixel whole (the neck and the back of the head with
          # it), then home; the head comes back a pose behind it, the muzzle a pixel past rest, the ears a pose
          # after it; then the neck leads the head down, the ears with it; the last pose is the rest pose but for
          # the tail's tip
          (2, dict(body=(1, 1, 1, 0), head=(1, -1), ears=(0, 1), pin=3, tail=TAIL_BACK[0])),
          (2, dict(body=(1, 0, 0, 0), neck=(1, -1), head=(1, 0), poll=-1, ears=(0, 1), pin=2, tail=TAIL_BACK[1])),
          (2, dict(neck=(2, -1), head=(2, 0), poll=-1, ears=(0, 1), pin=1, tail=TAIL_BACK[2])),
          (2, dict(neck=(1, -1), head=(1, -1), ears=(0, 1), tail=TAIL_BACK[3])),
          (2, dict(neck=(0, -1), head=(0, -1), ears=(0, 0), tail=TAIL_BACK[3])),
          (2, dict(neck=(0, 0), head=(0, -1), poll=1, ears=(0, 0), tail=TAIL_BACK[4])),
          (2, dict(tail=TAIL_BACK[4])),
          ]


def attack_poses():
    """[(frames, pose)]: the table above, with its effects placed: speed lines and a puff of dust on the strike and
    the contact, the star at the teeth on the bite, then its sparks."""
    out = []
    for n, kw in ATTACK:
        kw = dict(kw)
        fx = kw.pop("fx", None)
        if "tail" in kw:
            kw["tail"], kw["tail_lift"] = kw["tail"]
        pose = STAND(**kw)
        for leg in ("near_hind", "far_hind"):          # the hock's place against the paw, into the rig's joint push
            f, lift, h, hy, fold = pose["legs"][leg]
            pose["legs"][leg] = (f, lift, f + h - R.rnd(f + (pose["body"][0] - f) * (1 - HOCK_T)), hy, fold)
        hw = R.head_world(pose)
        teeth = (R.JAW_FRONT + 4 + hw[0], 20 + hw[1])
        pose["fx"] = {"strike": streaks(pose["body"][0], True) + dust(0),
                      "contact": streaks(pose["body"][0], False) + dust(1),
                      "flash": bite_fx(teeth, 0) + dust(2), "sparks": bite_fx(teeth, 1)}.get(fx, [])
        out.append((n, pose))
    return out


# ---- frames, strips --------------------------------------------------------------------------------------------------
def loops():
    """{loop: [(rendered pose, frames held)]} for every loop."""
    return {"idle": [(R.render(idle_pose(P)), IDLE_HOLDS[P]) for _ in range(BREATHS) for P in range(len(TORSO))],
            "move": [(R.render(move_pose(t)), 1) for t in range(MOVE_FRAMES)],
            "attack": [(R.render(p), n) for n, p in attack_poses()]}


def frame_box(all_loops):
    """One fixed box for every frame of every loop: the union of all poses, with a pixel of air round it."""
    pts = [p for poses in all_loops.values() for fr, _ in poses for p in fr]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs) - 1, min(ys) - 1, max(xs) + 2, max(ys) + 2


def hexrgba(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def image(fr, box, parts=False):
    x0, y0, x1, y1 = box
    im = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    for (x, y), (ch, part) in fr.items():
        im.putpixel((x - x0, y - y0), hexrgba(R.PART_RGB[part] if parts else R.RGB[ch]))
    return im


def strip(poses, box, parts=False):
    frames = [image(fr, box, parts) for fr, n in poses for _ in range(n)]
    im = Image.new("RGBA", (frames[0].width * len(frames), frames[0].height), (0, 0, 0, 0))
    for k, f in enumerate(frames):
        im.paste(f, (k * f.width, 0))
    return im


def drawing(box):
    """The approved drawing at 1x in the frame box (the check's --ref), and its palette image: the drawing with the
    mouth's layers (hidden under the head at rest) laid out beside it."""
    art = {(x, y): (ch, "body") for y, row in enumerate(C.ART) for x, ch in enumerate(row) if ch != "."}
    ref = image(art, box)
    pal = Image.new("RGBA", (ref.width + 16, ref.height), (0, 0, 0, 0))
    pal.paste(ref, (0, 0))
    for i, key in enumerate("MGJ"):
        for (x, y), ch in C.layer_pixels(key).items():
            pal.putpixel((ref.width + x - 62, 4 * i + y - 16), hexrgba(C.PALETTE[ch]))
    return ref, pal


def print_poses():
    """The check before rendering: each tick's pose, and no tick equal to the one before (a lost update)."""
    for name, n, fn in (("idle", len(TORSO), idle_pose), ("move", MOVE_FRAMES, move_pose)):
        frames = [R.render(fn(t)) for t in range(n)]
        print(f"{name}:")
        for t in range(n):
            p = fn(t)
            same = "  SAME AS BEFORE" if frames[t] == frames[t - 1] else ""
            legs = " ".join(f"{k[0]}{k.split('_')[1][0]}{v[:2]}" for k, v in p["legs"].items())
            print(f"  {t:2d} body {p['body']} neck {p['neck']} head {p['head']} poll {p['poll']} ears {p['ears']} "
                  f"flick {p['flick']} pin {p['pin']} look {p['look']} jaw {p['jaw']} tail {p['tail']} {legs}{same}")


def main():
    all_loops = loops()
    box = frame_box(all_loops)
    os.makedirs(os.path.join(HERE, "check"), exist_ok=True)
    for name, poses in all_loops.items():
        strip(poses, box).save(os.path.join(HERE, f"{KEY}_{name}.png"))
        strip(poses, box, parts=True).save(os.path.join(HERE, "check", f"{KEY}_{name}_parts.png"))
    ref, pal = drawing(box)
    ref.save(os.path.join(HERE, "check", f"{KEY}_art.png"))
    pal.save(os.path.join(HERE, "check", f"{KEY}_palette.png"))
    C.to_image(C.ART, 8).save(os.path.join(HERE, f"{KEY}_art_8x.png"))
    if "--poses" in sys.argv:
        print_poses()
    counts = ", ".join(f"{k} {sum(n for _, n in v)}" for k, v in all_loops.items())
    print(f"wrote {KEY}_idle/move/attack.png (frames: {counts}), FRAME_W {box[2] - box[0]} (frame "
          f"{box[2] - box[0]}x{box[3] - box[1]}); ROAD_SPEED {ROAD_SPEED} px a frame")


if __name__ == "__main__":
    main()
