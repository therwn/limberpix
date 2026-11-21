"""Animate the bird from its one drawing (creature.py, bird_wings.py, bird_heads.py) by posing its parts, the
pixel-animate way.

    python animate.py            # writes bird_idle.png, bird_move.png, bird_attack.png (strips) and bird_art_8x.png,
                                 # and in check/ the part strips, the drawing at game size and its palette
    python animate.py --poses    # also prints each loop's pose per clock tick and flags a tick equal to the one before

Every loop runs on one clock at 30 fps: a new pose every 2 frames (15/s), so the loops share one rate. The frame is
86x69, one box for every loop (the union of all their poses, 1 px of air round it).

Two rules run through every loop. The torso is one piece: the body layer is never cut, it moves whole by whole
pixels (and turns whole in the dive), and the neck that joins it to the head bends rather than steps (its rows under
the head ride the head, the rows below ride the body, drawn at both places so no gap or step shows: bird_rig.py,
NECK_STEP). The head is carried on the neck as a chain on the body's beat (head_chain): the body and the neck take a
rise or a fall first, the back of the head and the eye a pose later, the bill and the crest a pose after that. The
bill's lag is a small turn, not a step: for that pose the head wears a nod key (bird_heads.py: 3 nose down after a
rise, -3 nose up after a fall), turned about the neck, so the head's one pixel spreads over two poses and over its
pixels, and the head never steps alone as a rigid block.

  idle    72 frames (36 poses): a hover, three slow beats of 12 poses (the move's are 8): the wings dwell two poses at
          the top and two at the bottom and ease through half_up on the way down (five steps down, four up), and
          the body rises a whole pixel on the downstroke (5 poses up, 7 down). The far wing trails the near one on
          the way down, crossing edge-on for a single pose while the near wing is already past it, and meets it at
          the bottom, so its tip shows under the breast; it trails again on the way up. The head, the bill and the
          crest follow each rise and fall as the chain above; the tail is a chain whose links take the body's
          height one pose after another, the tip furthest, and as the downstroke starts its tip presses down a
          pixel; the hanging feet follow a pose behind the body. Beat 1 is plain. Beat 2 is the accent: the whole
          bird rises a pixel for 6 poses on top of the beat, and at its top the bill opens and shuts as a solid
          mandible about its hinge, a straight wedge to its tip (a call), the crest thrown back after it. Beat 3 is
          the rest: the head turns down to look at the water (the nods 3, then 6) and reaches forward a pixel on its
          neck, holds the look while the body rises under it, then turns back up into the beat; the crest follows
          the turn a pixel a pose.
  move    32 frames (16 poses): level flight. Two quicker beats of 8 poses, four steps down and four up; the far
          wing trails the near one, crossing edge-on for a single pose each way, and reaches the bottom with it.
          The body rises a pixel on the downstroke; the head takes it a pose later and reaches forward a pixel (a
          nod), the bill and the crest a pose after the head; the tail steers as a chain, its links a pose apart
          and the tip swinging furthest. Unlike the hover it leans into its flight: the head rides a pixel lower and
          the tail a pixel higher, and the feet are tucked away out of sight. Drawn in place, to be shown over a
          road scrolling at ROAD_SPEED.
  attack  56 frames (28 poses): from the hover's top, a dive strike, 5 : 2 : 2 : 18 poses (anticipation, strike,
          held key, follow-through and recovery). The body never turns while the wings are open, and the head is
          never turned at run time: it is the drawing's own head or one of its drawn keys (the nods, and the dive's
          keys from 10 to 45 degrees nose down), carried whole to where the body's turn takes the neck and never
          more than 6 degrees off the body's own turn, so the face stays one drawing on every pose.
          Anticipation (poses 1-5), small steps (41, 20, 57, 17, 32 % of the figure; the 57 is the near wing
          cocking): the bird draws up 4 px, the head a pose behind the body, then back a pixel and pitched nose up
          (the nod -3: the bill rises against the strike); the tail and the feet drop; the near wing, then the far
          one, change to the cocked key (higher, swept back); the last pose holds the body while the head and the
          crest settle on the mark.
          Strike (6-7) on an arc: first forward over the top (9 px on, level), the wings swept back (the sweep key,
          the feathers still drawn), the feet tucked away, the body turned 20 degrees and the head on its 22 key;
          then the drop (4 px on, 16 down) along the bill's line, the wings folded, body and head in line at 45
          degrees. Speed lines run behind it along the body's line, back from a gap behind its trailing edge; on
          contact a flash at the bill's tip.
          The held key (7-9, 6 frames): the thrust as a moving hold: the body sinks a pixel, the head follows a pose
          later; the speed lines fade, and single grains fly out of the flash point round the strike line, then
          further out and darker.
          Follow-through (10-17): still folded, it recoils on an arc, back first and then up (steps of 1, 1, 1, 2, 2,
          1, 1, 2 px back against 0, 1, 1, 2, 2, 2, 1, 2 px up), and levels out in turns of 5 or 6 degrees (45, 40,
          35, 30, 24, 18, 12, 6, 0); the head turns with it every pose, one pose behind the body (45, 45, 40, 34,
          28, 22, 16, 10, 6, then 3 for the recovery's first two poses), so the bill tip travels 1-4 px a pose
          on an even, easing path with no hold and no snap; the tail trails the turn, and the feet come out as it
          levels.
          Recovery (18-27): one beat. The wings open through the sweep key (an in-between: the feathers unfold back
          to front instead of jumping from folded to half_up), the near wing first and the far one a pose later,
          and beat down, lifting it a pixel over its hover mark (the overshoot, held through the downstroke); the
          upstroke lets it settle back. The head, the tail and the feet ride the body's height as the chain above.
          pixel-anim-check's `recover` asks every step after the strike to change at most half as much of the
          figure as the strike does: the follow-through turns in small steps and the unfolding moves the bird a
          pixel at a time, so the largest step after the strike is 73 % of the figure against the strike's 162 %.

ROAD_SPEED = 1.0 game px a frame (30 px/s at 30 fps): the speed of the ground scrolling under the move. Nothing of
the bird is planted (its feet are tucked in flight), so no pixel of it is tied to the road; the speed is given to
the check (--speed) for its GIF's ground line and is what a game should scroll under this flight.

Nothing of the rest drawing is redrawn: each part is the drawing's own pixels, moved by whole pixels; the wing keys,
the head's turns (the nods and the dive's keys) and the open bill are drawn keys (bird_wings.py, bird_heads.py,
bird_rig.JAW); only the attack's dive and recoil turn the body, tail, folded wings and feet (bird_rig.py), and the
outline is drawn last round whatever the parts cover.

Check (from this folder):
  python ../../../skills/pixel-anim-check/pixel_anim_check.py --loop idle=bird_idle.png --loop move=bird_move.png
         --loop attack=bird_attack.png --frame 86 --eye "#22110f" --ink "#0e0a16,#1f5d68,#5a1f2c" --flier
         --action attack:strike:right --speed 1.0 --effects "#e2f8ff,#7fb6c8,#fff0a8"
         --parts idle=check/bird_idle_parts.png --parts move=check/bird_move_parts.png
         --parts attack=check/bird_attack_parts.png --squash "#3f7fd0,#24497a,#c8a040,#9a6b2f,#40c0a0,#d88a3a"
         --palette check/bird_palette.png --ref check/bird_ref.png --out check --name bird
--ink names the three outline colours: the lit outlines are lighter than the check's default ink threshold. The
effects are the speed lines, their fading trail and the hit's flash and grains. --squash names the parts whose seen
area changes on purpose: both wings (each key is its own drawing), the body and the tail (the near wing covers them
on its downstroke), the crest (it slides under the cap and out again as it follows the head, and the head's keys
show more or less of it) and the neck (it bends to carry the head, and the head and the near wing cover more or less
of it). Head and bill keep their area in every frame.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bird_heads as HK  # noqa: E402
import bird_rig as R  # noqa: E402
import creature as C  # noqa: E402

KEY = C.KEY
HOLD = 2                                   # one clock: every pose is held 2 frames at 30 fps
ROAD_SPEED = 1.0                           # game px a frame (see above)
PART_COLOURS = {"wing_far": "#24497a", "tail": "#9a6b2f", "body": "#c8a040", "neck": "#d88a3a", "foot_far": "#7a3050",
                "foot_near": "#d0607a", "wing": "#3f7fd0", "nape": "#40c0a0", "head": "#e0e070",
                "bill_low": "#a050c0", "bill_up": "#6040a0"}


def P(**kw):
    p = dict(R.REST)
    p.update(kw)
    return p


# ---- the head on the neck: one chain for every loop -----------------------------------------------------------
NOD = {1: 3, -1: -3}                       # the bill a pixel below its place (the head has risen): nose down 3; above
                                           # it (the head has fallen): nose up -3


def head_chain(lift, t):
    """The head carried on the neck after the body's height lift(t) (pixel-animate 3.3, 3.8, 3.10): the neck bends
    with the body at once (bird_rig.neck_pixels), the back of the head and the eye take the rise or fall a pose late,
    and the bill and the crest a pose after them. The bill's lag is a turn, not a step: for that pose the head wears
    a nod key (bird_heads: 3 nose down after a rise, -3 nose up after a fall), so the head's one pixel spreads over
    two poses and over its pixels, the back first, the bill last. Returns (head dy against the body, nod key, the
    crest's dy against the head)."""
    body, head, bill = lift(t), lift(t - 1), lift(t - 2)
    return head - body, NOD.get(bill - head, 0), bill - head


def crest(key, dx, dy):
    """The crest's (dx, dy) against the head wearing key. In the one-pose nods (-3, 3) the crest rides the cap's turn
    as the key carries it (bird_heads.CREST) and lags only in height; in the held look (6) (dx, dy) is where it sits
    from the drawing's own head, so it can follow the turn a pixel a pose (LOOK): the key's own move is taken out."""
    kx, ky = HK.CREST[key] if key == 6 else (0, 0)
    return dx - kx, dy - ky


def chain(lift_at, t, amp=(1.0, 1.0, 1.0)):
    """The tail's links (root, middle, tip) as dy against their parents: link i takes the body's height of i + 1
    poses ago, times amp[i] (a tip swinging further than the root), against the body's height now."""
    now = lift_at(t)
    absolute = [round(amp[i] * lift_at(t - 1 - i)) for i in range(3)]
    rel = [a - now for a in absolute]
    return rel[0], rel[1] - rel[0], rel[2] - rel[1]


# ---- idle: a hover ------------------------------------------------------------------------------------------
# A slow beat of 12 poses (the move's is 8), (near wing, far wing) per pose: two poses dwelling at the top and two at
# the bottom, a downstroke of five steps easing through half_up twice, an upstroke of four. The far wing trails the
# near one on the way down (passing edge-on for a single pose, while the near wing is past it) and catches it at the
# bottom, so its tip shows under the breast for the whole low half; it trails again on the way up.
IDLE_STROKE = [("up", "up"), ("half_up", "up"), ("half_up", "half_up"), ("level", "half_up"), ("half_down", "half_up"),
               ("down", "level"), ("down", "down"), ("half_down", "down"), ("level", "half_down"),
               ("half_up", "level"), ("up", "half_up"), ("up", "up")]
IDLE_UP = {4, 5, 6, 7, 8}                  # the beat's poses with the body a pixel up: it rises on the downstroke
IDLE_POSES = 36                            # three beats: a plain one, the accent, the rest
DRIFT = {t: -1 for t in range(13, 19)}     # the accent: the whole bird rises a pixel for 6 poses (on top of the beat)
CALL = {19: 1, 20: 2, 21: 1}               # the accent's call at its top: the bill opens about its hinge (on the
                                           # drawing's own head: the opening bill carries the head's fall that pose)
THROW = {20: -1, 21: -1, 22: -1}           # and the crest is thrown back a pixel after it
LOOK = {24: (3, 0, (0, 0)), 25: (6, 0, (1, 0)), 26: (6, 1, (2, 0)), 27: (6, 1, (3, 0)), 28: (6, 1, (3, 0)),
        29: (6, 0, (3, 0)), 30: (3, 0, (2, 0)), 31: (0, 0, (1, 0)), 32: (0, 0, (0, 0))}
#        the rest, pose: (head key, reach, crest): the head turns down to look at the water (the nods 3, then 6) and
#        reaches forward a pixel on its neck; it holds the look while the body rises under it, then turns back up
#        through 3 into the beat. The crest (its place against the drawing's head, x forward) follows the turn a
#        pixel a pose, to where the look key carries it and back.
TAIL_PRESS = {1, 2, 3}                     # the beat's poses with the tail tip pressed down (the downstroke's start)


def beat_lift(t):
    return -1 if t % len(IDLE_STROKE) in IDLE_UP else 0


def idle_lift(t):
    return beat_lift(t) + DRIFT.get(t % IDLE_POSES, 0)


def idle_key(t):
    t %= IDLE_POSES
    return LOOK[t][0] if t in LOOK else 0 if t in CALL else head_chain(idle_lift, t)[1]


def idle_pose(t):
    t %= IDLE_POSES
    k = t % len(IDLE_STROKE)
    near, far = IDLE_STROKE[k]
    lift = idle_lift(t)
    dy, _, lag = head_chain(idle_lift, t)
    key = idle_key(t)
    reach, (cx, cy) = LOOK.get(t, (0, 0, (0, 0)))[1:]
    jaw = CALL.get(t, 0)
    return P(s=near, far=far, y=lift, hkey=key, head=(reach, dy), jaw=jaw,
             nape=crest(key, cx - reach + THROW.get(t, 0), cy + lag),
             tail=press(chain(idle_lift, t, (1.0, 1.0, 1.5)), k), feet=(0, idle_lift(t - 1) - lift))


def press(links, k):
    """At the top of the beat the tail's tip presses down a pixel, as the wings lift (a balance)."""
    return links[0], links[1], links[2] + (1 if k in TAIL_PRESS else 0)


# ---- move: level flight -------------------------------------------------------------------------------------
# (near wing, far wing) per pose: an even beat of 8, four steps down and four up; the far wing trails the near one,
# crossing edge-on for a single pose each way, and reaches the bottom with it so its tip shows under the breast.
MOVE_STROKE = [("up", "half_up"), ("half_up", "up"), ("level", "half_up"), ("half_down", "level"), ("down", "down"),
               ("half_down", "down"), ("level", "half_down"), ("half_up", "level")]
MOVE_UP = {2, 3, 4}
MOVE_POSES = 16
PITCH = 1                                  # in flight it leans forward: the head a pixel lower, the tail a pixel
                                           # higher, and the feet tucked out of sight


def move_lift(t):
    return -1 if t % len(MOVE_STROKE) in MOVE_UP else 0


def move_pose(t):
    t %= MOVE_POSES
    k = t % len(MOVE_STROKE)
    near, far = MOVE_STROKE[k]
    lift = move_lift(t)
    dy, key, lag = head_chain(move_lift, t)
    push = -move_lift(t - 1)                       # the head reaches forward a pixel as it rises, back as it falls,
    late = -move_lift(t - 2)                       # and the crest follows it a pose late
    root, mid, tip = chain(move_lift, t, (1.0, 1.5, 2.0))
    return P(s=near, far=far, y=lift, hkey=key, head=(push, dy + PITCH), nape=crest(key, late - push, lag),
             tail=(root - PITCH, mid, tip), feet=None)


# ---- attack: a dive strike ----------------------------------------------------------------------------------
DIVE_PIVOT = (56.0, 28.0)                  # the dive turns the body about the bill's base: the tail swings up over it
CHAIN = "chain"                            # in a row: the head (and the tail, the feet) carried on the body's height
# One row per pose (each held 2 frames): wing, far wing, x, y, body turn (nose down +), head key, head (dx, dy),
# crest (dx, dy), tail links, feet (dx, dy) or None (tucked out of sight), effects. The head is never turned at run
# time: it is the drawing's own (key 0) or a drawn key (the nods -3, 3 and 6, the dive's 10 to 45: bird_heads.py),
# carried whole to the turned neck, and never more than 6 degrees off the body's own turn. CHAIN in the head's
# place carries it on the neck after the body's height (head_chain: the head a pose late, the bill a pose after it
# as a nod); in the tail's and the feet's place, it hangs them after the body the same way.
ATTACK = [
    # rest: the hover's top
    ("up", "up", 0, 0, 0, 0, (0, 0), (0, 0), (0, 0, 0), (0, 0), ()),
    # anticipation, eased: the bird draws up 4 px, the head a pose behind the body, then back a pixel, and pitched
    # nose up (the nod -3: the bill rises against the strike); the tail and the feet drop; the near wing, then the far
    # one, cock (higher, swept back); the last pose holds the body while the head and the crest settle on the mark
    ("up", "up", 0, -1, 0, 0, (0, 1), (0, 0), (1, 0, 0), (0, 1), ()),
    ("up", "up", 0, -2, 0, -3, (0, 1), (0, 0), (1, 1, 0), (0, 1), ()),
    ("cock", "up", 0, -3, 0, -3, (-1, 1), (1, 0), (1, 1, 1), (0, 2), ()),
    ("cock", "cock", 0, -4, 0, -3, (-1, 1), (0, 0), (2, 1, 1), (0, 2), ()),
    ("cock", "cock", 0, -4, 0, -3, (-1, 0), (-1, 0), (2, 1, 2), (0, 2), ()),
    # strike, two poses on an arc: first forward over the top, wings swept back and the feet tucked away, the head
    # pitching down (key 22); then the drop along the bill's line, wings folded, head and body in line (key 45);
    # speed lines behind it, a flash at the bill's tip on contact
    ("sweep", "sweep", 9, -4, 20, 22, (0, 0), (-1, 0), (0, 0, 0), None, (("streak", 0),)),
    ("fold", "fold", 13, 12, 45, 45, (1, 0), (0, 0), (0, 0, -1), None, (("streak", 0), ("hit", 0))),
    # the held key, the thrust: a moving hold (the body sinks a pixel, the head follows a pose later, sparks)
    ("fold", "fold", 13, 13, 45, 45, (1, 0), (0, 0), (0, 0, -1), None, (("streak", 1), ("hit", 1))),
    ("fold", "fold", 13, 13, 45, 45, (1, 1), (0, 0), (0, 0, 0), None, (("hit", 2),)),
    # follow-through: still folded, it recoils on an arc, back first and then up, levelling out in turns of 5-7
    # degrees that shrink at the end; the head turns with it a pose behind (a key every 4-6 degrees: 45, 40, 34,
    # 28, 22, 16, 10, 6), never more than 6 degrees off it; the tail trails the turn, and the feet come out as it
    # levels
    ("fold", "fold", 12, 13, 40, 45, (1, 0), (0, 0), (0, 1, 0), None, ()),
    ("fold", "fold", 11, 12, 35, 40, (1, 1), (0, 0), (0, 1, 1), None, ()),
    ("fold", "fold", 10, 11, 30, 34, (0, 0), (0, 0), (0, 1, 1), None, ()),
    ("fold", "fold", 8, 9, 24, 28, (0, 0), (0, 0), (0, 0, 1), None, ()),
    ("fold", "fold", 6, 7, 18, 22, (0, 0), (0, 0), (0, 0, 1), None, ()),
    ("fold", "fold", 5, 5, 12, 16, (0, 0), (0, 0), (0, 0, 0), None, ()),
    ("fold", "fold", 4, 4, 6, 10, (0, 0), (0, 0), (0, 0, 0), None, ()),
    ("fold", "fold", 2, 2, 0, 6, (0, 0), (0, 0), (0, 0, 0), (-1, 1), ()),
    # recovery, one beat: the wings open through the swept key (an in-between, the feathers unfolding back to
    # front) and beat down, lifting it a pixel over its hover mark (the overshoot, on the downstroke); the upstroke
    # lets it settle back onto the mark; the head, the tail and the feet ride the body's height as a chain (the
    # head's last turn up, 6 to 3 to 0, ends over the first two poses: their own key 3)
    ("sweep", "fold", 2, 2, 0, 3, CHAIN, (0, 0), CHAIN, CHAIN, ()),
    ("half_up", "sweep", 2, 1, 0, 3, CHAIN, (0, 0), CHAIN, CHAIN, ()),
    ("level", "half_up", 1, 0, 0, 0, CHAIN, (0, 0), CHAIN, CHAIN, ()),
    ("half_down", "half_up", 0, -1, 0, 0, CHAIN, (0, 0), CHAIN, CHAIN, ()),
    ("down", "level", 0, -1, 0, 0, CHAIN, (0, 0), CHAIN, CHAIN, ()),
    ("down", "down", 0, -1, 0, 0, CHAIN, (0, 0), CHAIN, CHAIN, ()),
    ("half_down", "down", 0, -1, 0, 0, CHAIN, (0, 0), CHAIN, CHAIN, ()),
    ("level", "half_down", 0, -1, 0, 0, CHAIN, (0, 0), CHAIN, CHAIN, ()),
    ("half_up", "level", 0, 0, 0, 0, CHAIN, (0, 0), CHAIN, CHAIN, ()),
    ("up", "half_up", 0, 0, 0, 0, CHAIN, (0, 0), CHAIN, CHAIN, ()),
]
ATTACK_FRAMES = len(ATTACK) * HOLD


SETTLE = next(i for i, row in enumerate(ATTACK) if row[6] == CHAIN) - 1   # the last pose of the follow-through


def attack_lift(t):
    """The body's height the chained rows ride: their own, and before them the follow-through's last, level pose (the
    turned recoil is not a height for a chain to follow)."""
    return ATTACK[max(t % len(ATTACK), SETTLE)][3]


def attack_pose(t, hit=True):
    t %= len(ATTACK)
    s, far, x, y, rot, hkey, head, nape, tail, feet, fx = ATTACK[t]
    if head == CHAIN:
        dy, nod, lag = head_chain(attack_lift, t)
        hkey = hkey or nod                     # a row's own key (the recoil's last turn up) or the chain's nod
        head, nape = (0, dy), (nape[0], nape[1] + lag)
    if tail == CHAIN:
        tail = chain(attack_lift, t)
    if feet == CHAIN:
        feet = (0, attack_lift(t - 1) - y)
    p = P(s=s, far=far, x=x, y=y, rot=rot, pivot=DIVE_PIVOT, hkey=hkey, head=head, nape=nape, tail=tail,
          feet=feet, fx=fx)
    if hit and any(name == "hit" for name, _ in fx):
        p["hit_pose"] = attack_pose(CONTACT, hit=False)
    return p


CONTACT = next(i for i, row in enumerate(ATTACK) if ("hit", 0) in row[-1])


LOOPS = {"idle": (IDLE_POSES, idle_pose), "move": (MOVE_POSES, move_pose), "attack": (len(ATTACK), attack_pose)}


# ---- frames, the one box, output ----------------------------------------------------------------------------
def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def render_all():
    """{loop: [(rows, owner, fx) per pose]}, each pose rendered once."""
    return {name: [R.render(fn(t)) for t in range(n)] for name, (n, fn) in LOOPS.items()}


def union_box(rendered):
    """One box for every frame of every loop (pixel-animate 2.5): the union of all poses, 1 px of air round it."""
    xs, ys = [], []
    for poses in rendered.values():
        for rows, _, fx in poses:
            for y, r in enumerate(rows):
                for x, ch in enumerate(r):
                    if ch != ".":
                        xs.append(x)
                        ys.append(y)
            for x, y in fx:
                xs.append(x)
                ys.append(y)
    return min(xs) - 1, min(ys) - 1, max(xs) + 2, max(ys) + 2


def pose_image(pose, box, parts=False):
    rows, owner, fx = pose
    x0, y0, x1, y1 = box
    im = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    px = im.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            ch = rows[y][x] if 0 <= y < len(rows) and 0 <= x < len(rows[0]) else "."
            if ch != ".":
                px[x - x0, y - y0] = rgb(PART_COLOURS[owner[(x, y)]] if parts else C.PALETTE[ch]) + (255,)
            elif (x, y) in fx and not parts:
                px[x - x0, y - y0] = rgb(fx[(x, y)]) + (255,)
    return im


def strip(poses, box, parts=False):
    w, h = box[2] - box[0], box[3] - box[1]
    im = Image.new("RGBA", (w * len(poses) * HOLD, h), (0, 0, 0, 0))
    for t, pose in enumerate(poses):
        one = pose_image(pose, box, parts)
        for k in range(HOLD):
            im.paste(one, ((t * HOLD + k) * w, 0))
    return im


def print_poses(rendered):
    """The check before rendering (pixel-animate 5.1): each tick's pose, and no tick equal to the one before."""
    for name, (n, fn) in LOOPS.items():
        print(f"{name}:")
        for t in range(n):
            p = fn(t)
            same = " SAME AS BEFORE" if rendered[name][t][0] == rendered[name][t - 1][0] and \
                rendered[name][t][2] == rendered[name][t - 1][2] else ""
            print(f"  {t:2d} wing {p['s']:9s} far {p['far']:9s} x {p['x']:+3d} y {p['y']:+3d} turn {p['rot']:3d} "
                  f"key {p['hkey']:2d} head {p['head']} crest {p['nape']} jaw {p['jaw']} tail {p['tail']} "
                  f"feet {p['feet']} "
                  f"fx {list(p['fx'])}{same}")


def main():
    rendered = render_all()
    box = union_box(rendered)
    os.makedirs(os.path.join(HERE, "check"), exist_ok=True)
    for name, poses in rendered.items():
        strip(poses, box).save(os.path.join(HERE, f"{KEY}_{name}.png"))
        strip(poses, box, parts=True).save(os.path.join(HERE, "check", f"{KEY}_{name}_parts.png"))
    pose_image(R.render(R.REST), box).save(os.path.join(HERE, "check", f"{KEY}_ref.png"))
    pal = Image.new("RGBA", (len(C.PALETTE), 1))
    for i, h in enumerate(C.PALETTE.values()):
        pal.putpixel((i, 0), rgb(h) + (255,))
    pal.save(os.path.join(HERE, "check", f"{KEY}_palette.png"))
    C.to_image(C.ART, 8).save(os.path.join(HERE, f"{KEY}_art_8x.png"))
    if "--poses" in sys.argv:
        print_poses(rendered)
    w, h = box[2] - box[0], box[3] - box[1]
    print(f"wrote {KEY}_idle.png ({IDLE_POSES * HOLD} frames), {KEY}_move.png ({MOVE_POSES * HOLD} frames), "
          f"{KEY}_attack.png ({ATTACK_FRAMES} frames), {KEY}_art_8x.png; frame {w}x{h}")


if __name__ == "__main__":
    main()
