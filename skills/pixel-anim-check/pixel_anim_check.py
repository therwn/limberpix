"""Pixel-art animation check: finds the faults that make a sprite animation look broken, before anyone sees it.

    python pixel_anim_check.py --loop idle=idle.png --loop move=walk.png --frame 32 [options]
    python pixel_anim_check.py --selftest
    python pixel_anim_check.py --help

A loop is a horizontal sprite strip, a folder of frame PNGs, or a GIF. Every loop of a creature must have frames of
one size, the figure in place (not trimmed per frame). A strip is cut by --frame (one frame's width) or --frames (how
many frames it holds); with neither, its frames are taken as square, and a strip whose width is not a whole number
of its height is refused. A folder is read in file-name order: zero-pad the numbers (f00.png, f01.png, ...). A GIF
is sampled at --fps by rounding elapsed playback time to game frames. Exporters store a held pose as one image
with a longer duration. Colours are #rrggbb, any case, the #
optional. Options:
  --frame W           a strip's frame width in px          --frames N   how many frames each strip holds
  --eye #rrggbb       the eye's colour: checked on every frame, the head round it must move (frozen), its row track
                      must not tick (tick), and the face round it must keep its shape (reshape)
  --eye-at X,Y        where the eye is on each loop's first frame (column, row), when the eye colour is used
                      elsewhere too (a gem, a bead, a glow): the piece nearest that place is the eye. Without it
                      the biggest piece is taken, and a note says which
  --flier             it flies: its shadow (--shadow colours, anywhere in the frame) must not slide; its body
                      height track is read for ticks; its idle wing stroke is judged against its move (shallow)
  --facing right|left which way the head faces (default right): where the face window of reshape lies
  --ink #hex,...      the outline colours (default: every colour darker than lightness 40)
  --shadow #hex,...   a flier's ground shadow colours
  --effects #hex,...  colours of effects drawn apart from the figure on purpose (sparks, rings, auras)
  --allow loop=N      pieces up to N px may sit apart from the figure in that loop (a thrown coin)
  --glows-eye loop    the eye is recoloured by a glow in that loop (not checked there)
  --idle NAME --move NAME   which loops are the rest and the travel loop (default idle, move). A loop named
                      with them must be given; with no loop of the default name a note says which checks do not run
  --legless           it crawls without legs (a snake, a slug): no body rise asked of its move; hop judges every loop
  --out DIR --fps N   where the contact sheet and the GIF go (default .); the rate the game plays them, frames a
                      second, a decimal allowed (default 30: used to sample a GIF input and play the GIF, and by
                      choppy, boil's rates, snap, hitch, the eye tick's dwell and an action's held keys)
  --name NAME         the stem of the written files (default anim)
  --no-preview        print the same checks and motion tracks without rendering a PNG or GIF
  --action NAME[:KIND[:DIR]]  that loop is an action: it may hold up to two keys (a wind-up and a follow-through),
                      each up to 13 frames (at 30 fps), outside choppy and uneven. KIND strike (its phases are
                      judged; DIR right|left|up|down, default the facing), jump (it leaves the ground: ground is
                      not asked), or any other word (a gesture)
  --speed PX          the road's scroll in game px a frame: the planted feet's speed is printed beside it, and the
                      GIF scrolls a ground line under the move
  --parts LOOP=PATH   a part strip for that loop (same frames, each rig part one flat colour): per-part volume and
                      follow-through lag are judged on it
  --squash #hex,...   part colours whose area changes on purpose (wings, a squashed body): left out of volume
  --palette PATH      the approved drawing's colours: every frame must keep to them (palette)
  --ref PATH          the approved drawing at game size: the idle's nearest pose must match it (drift)
  --glow #hex,...     colours shown in some frames on purpose (glow steps, glints, blink lids)
  --mark #hex,...     small defining marks (a gem, a lamp): on every frame, never jumping 2 px in one frame
  --sheet LOOP        that loop was drawn as a sheet or by AI: a part switched off for a cell is looked for (swap)
  --min-rate R        choppy's floor for the idle and the move, updates a second, for a style held longer than the
                      fitted floors allow (Slynyrd 45's 16 px sprites hold a pose 200 ms, 5 a second, text; his
                      2-pose idles 800 ms, measured; give --min-rate 4 for poses of 250 ms). Default: 10, or the
                      walk's and the idle's own floors (see choppy)
  --spots PATH        (with --ref) a JSON file {"group": [[row, column], ...], ...}: the approved drawing's small
                      marks, placed by eye in its pixels (a hat's specks, a mouth); each must show in every pose
                      (spots). The approved drawing must be at the loops' scale
  --style pixel|redrawn   how the frames were made (default pixel). pixel: one drawing moved by whole pixels, its
                      texture kept (the cut-out rules below). redrawn: every pose a new drawing of the whole figure
                      (frame by frame, or generated): stepped replaces choppy, uneven and lurch; lostmark and gaps
                      are run; shimmer is not run; reshape and outline only warn
  --key #rrggbb       the background colour of strips with no transparency: read as air in the loops, --parts,
                      --ref and --palette (that exact colour only: clean a key's fringe first). Without it, a loop
                      with no transparent pixel in any frame is refused (exit 2)
Exit code: 0 no fault, 1 one fault or more, 2 a usage error (a bad option, a missing file, a strip that does not cut).
Frame numbers in the output are 0-based: move[3] is the move's fourth frame; "frame k" in a jump or a snap is the
change from frame k to the next.
Faults (each a line "kind: ..."):
  size     frames differ in size            empty    a frame with nothing drawn
  apart    a piece apart from the figure
  eye      the eye missing on a frame, or (in the idle or the move; a warning elsewhere) the eye leaving its head's
           box in one frame: a cell mirrored or off its anchor, or the eye lost while its colour shows elsewhere.
           The eye is one piece of its colour, the biggest on the first frame, then the nearest one
  outline  coloured edge pixels with no ink round them (an open contour)
  ground   a walker's feet leave one ground line in a loop other than the move; a flier's shadow slides; in a
           legged walker's move the lowest drawn row moving is a warning (a whole-figure lift; a run leaves the
           ground on purpose)
  jump     a change between two frames over JUMP times the loop's usual step: the mean of its moving steps with
           the two biggest left out, since a pose out of order makes two (into it and out of it); a declared
           strike's own step and a declared jump's launch and landing are left out first. Under 4 usual steps the
           change must also reach a quarter of the figure; under 2 (3 moving steps or fewer) only the sideways test
           runs. Or one pose knocked sideways out of step against the
           distinct poses either side of it, a pose held on twos or threes included ("move[6-7] (a held pose)")
  still    the move changes under STILL of the figure a frame
  shimmer  pixels taking another tone for 0.1 s at most (3 frames at 30 fps) and going back, on a sixth of the
           frames and 3 times a loop at the least (texture crawling), a drawing held on twos or threes read too; a
           stroke's turning poses, tones too alike to tell apart (FAINT), and a tone stepping monotonically along a
           moving edge (a sub-pixel in-between) are not counted
  frozen   the head (round the eye) hardly changes in the idle or the move, read as drawn: a mask on a living body
           (a head carried whole on the body's rise and fall moves)
  stiff    a walker's body never rises or falls in the move (the top of its middle third holds to under STIFF px):
           legs stepping under a board
  choppy   a loop updating fewer than CHOPPY_RATE times a second, or one update dropped (a hold twice the usual
           of 3+ frames): read as a dropped frame rate (--fps: the rate the game plays it at). A rest (a hold of a
           third of the loop) is left out and the rest of the loop judged. An idle moving its whole body on every
           pose may update 2.5 times a second and hold one pose twice the others; a move whose every pose
           change is big (a new drawing of the stride), 5.2 times; --min-rate sets both floors
  uneven   the holds between a loop's moves jump in turn (1 frame, then 3, then 1): the motion stutters though
           the rate is the same (ease lengthening the holds at a turn is on purpose; an idle that breathes, its
           body moving whole, is not judged: its breath is eased, slow over the top and quick on the drop)
  lurch    a held loop whose moves alternate big and small (a whole-body bob after a leg's small step, frames held
           between): a hitch each beat; with something moving on every frame the bob reads as a gait (not in the
           idle, where a whole-body step between a free tip's small steps is the breath)
  snap     an idle stops dead (a third of a second or more) and then changes a quarter of the figure in one step
  tick     a whole-pixel level is left and regained within a few frames: the eye's row in the idle, or a flier's
           whole-body height in its idle or move (a lift peaking just over half a pixel)
  hop      a grounded body (any idle but a flier's; every loop of a --legless body) lifts off its contact row, air
           opening above the contact (legs stretching to keep a risen trunk on its feet is a breath)
  vanish   a big piece switches off while the rest of the figure is nearly still, and stays gone (a far wing hidden
           at the turn of its stroke)
  shallow  a flier's idle moves only the upper half of the figure, where its move beats the whole wing
  reshape  the face, aligned on itself, changes its silhouette and ink lines between poses in the idle (a sheet
           redrawing the head in every cell)
  palette  (with --palette) a frame holds a colour outside the approved drawing's, --effects, --shadow and --glow
  mark     (with --mark) a mark missing on a frame, or jumping 2+ px in one frame, in the idle or the move
  stepped  (--style redrawn) a loop other than an action whose whole body moves (a new pose changing 40 % of the
           figure's tiles) fewer than 6 times a second: it reads slow and stepped
  lostmark (--style redrawn) the marks a patch of one colour closes in (a mouth on a face, a stud on a coat), there
           in most poses, gone in 3 or more separate runs of poses (a blink, once or twice a loop, passes)
  gaps     (--style redrawn) the outline broken in short stretches: over 5 runs per 100 edge px of 1-4 coloured
           pixels between ink on the figure's edge. Give every outline colour, lit ones too, with --ink
  spots    (with --spots) a pose of a loop other than an action showing fewer of a group's marks than the approved
           drawing, each looked for at its place (the group's window found again in the pose); a mark that turned
           another colour, or into a pinhole, still counts
Warnings (lines "warn: ...", not faults; look at them): the eye tick, reshape and mark in loops other than the idle
(an action may jump or open its jaw on purpose), and the later checks, whose margins are not yet fitted:
  boil     outline-only steps that come back (A, B, A) are a quarter of the updates, or hide a real-pose rate
           under 10/s          skate    a planted foot slides forward, or its steps swing over 2 px (the move)
  gait     the move's body does not bob twice a loop, or it has an odd number of poses
  seam     the pose at the loop's seam held longer than every other, all alike: the first pose repeated at the end
  counter, strike, recover, stage, piston   a declared strike: no wind-up against it, a strike under 3 times the
           anticipation's step, a return to rest in one step or one big one, a contact pose keeping 90 % of the rest
           silhouette, a lead travelling on a straight line
  gravity, squash, recover   a declared action that leaves the ground: an even fall, a squash that narrows or
           loses mass or lasts 3+ poses, an abrupt landing
  volume, lag   (with --parts) a part's area changing over 10 %; every part riding the body on its frame
  blend    (--sheet) a rare colour between the tones it touches
  orphans  a frame with over twice the loop's usual lone pixels     speck  a glaring pixel blinking once a loop
  doubles  a frame with over twice the loop's usual doubled outline cells
  drift    (with --ref) the idle's nearest pose differs from the drawing   swap (--sheet) a part switched off
  split    the torso's two sides move rigidly by different amounts, a 1-px step between them where its drawing's
           topline (or belly line) is level: a body cut into bands (not read on a flier)
  hitch    the head (the eye's track), or a --parts part, steps alone after holding still 10+ frames at 30 fps
After the faults it prints read-outs: per loop the steps, the eye's rows, the update and real-pose rates, the box and
its anchor, rare colours; the move's bob, leg band and planted-foot speed; each action's phases and staging; parts.
Unless --no-preview is given, writes <name>_check.png and <name>_check.gif in the folder printed as "sheets".
The PNG shows up to 12 distinct poses per loop plus any pose named in a fault, with frame labels and changes
from the last pose. The GIF plays the loops side by side at --fps. <out>/<name>_check.json points to the latest
complete pair. When --out is a frame input folder, look under its anim-previews subfolder. Look at both previews:
the numbers do not see likeness or taste.
--selftest draws a small walker and flier, checks they pass, then breaks them on purpose in every way above and
checks each break is caught. Run it after changing this file.

The thresholds of choppy, snap, tick, hop, vanish, shallow and reshape were fitted to a private calibration set (39
animated creatures, with 15 accept or reject judgements on them by one reviewer; not included), with the margins
stated in each function. No source gives a pixel threshold for judder: rerun the check on every animation you have
accepted whenever a threshold changes."""
import colorsys
import json
import math
import os
import re
import shutil
import statistics
import sys
import tempfile
import time
from fractions import Fraction

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:                                  # python -I does not see a pip install --user
    raise type(e)(f"{e}: {os.path.basename(__file__)} needs numpy and Pillow. python -I (isolated mode) does "
                  "not see packages installed with pip install --user: install them in a virtual "
                  "environment or for the whole system, or run without -I", name=e.name) from None

JUMP, STILL, SHIMMER, FROZEN, FAINT, STIFF = 3.6, 0.015, 0.03, 0.12, 10, 0.5
MOVE_MIN, CADENCE_STEP, LURCH = 0.02, 0.08, 3.0          # uneven and lurch (unchanged)
CHOPPY_RATE, MOVE_EPS = 10.0, 0.002                      # choppy: updates a second; a move is over MOVE_EPS of A
BODY_TOPS = 0.8                                          # a pose change moving the body: this share of the columns'
CHOPPY_BODY_IDLE = 2.5                                   # tops moves; then an idle may update this slowly a second
CHOPPY_WALK = 5.2                                        # a move whose every pose change is big: updates a second
SNAP_STEP, SNAP_STILL = 0.25, 0.02                       # snap: the step out of a dead stop; what counts as still
TICK_DUTY = 0.18                                         # tick: the shortest excursion against its share of the loop
HOP_LIFT, HOP_SHARE, HOP_STEP = 0.5, 0.6, 0.3            # hop: contact kept; rigid share of a big step; big step
VANISH_R, VANISH_MIN, VANISH_HOLD, VANISH_R4 = 2, 8, 3, 1.1
SHALLOW, SHALLOW_ROWS, SHALLOW_PX = 0.3, 0.8, 0.6
RESHAPE = 0.10
# The checks below warn only (except palette and mark, which run only when asked for): their margins are first
# guesses from the sources, not yet fitted to accepted animations. Rerun them on your accepted set before trusting.
ACTION_KEY = 13                                          # an action's held keys (two), frames at 30 fps (4-13 sourced)
STRIKE_SNAP, SETTLE = 3.0, 0.5                           # strike: >= 3x the anticipation; recover: no step over half
STAGE_IOU = 0.9                                          # stage: the strike pose's silhouette against the rest pose
PISTON_SPAN, PISTON_DEV = 4, 1.0                         # piston: a path of 4+ px within 1 px of its chord
SQUASH_H, SQUASH_AREA, SQUASH_POSES = 0.10, 0.15, 2      # a squash of 10 %+ keeps its area within 15 %, 2 poses
BOIL_EDGE, BOIL_SMALL, BOIL_BACK = 0.8, 0.25, 0.5        # boil: edge share, against the median step, reverted share
SKATE_SWING = 2                                          # skate: a planted foot's step may vary 1 px, plus 1 jitter
SKATE_NEAR = 2                                           # skate: another contact this close makes a match unsure
GAIT_CLEAR = 0.7                                         # gait: every other wave count under this share of the main
ORPHAN_PX, ORPHAN_X, SPECK_DL = 3, 2.0, 60              # orphans over 2x the loop's usual + 3; a speck's contrast
DOUBLES, DOUBLES_X = 2, 2.0                              # doubles over 2x the loop's usual + 2
REF_DRIFT = 0.02                                         # drift: the idle's nearest pose against the approved drawing
VOLUME, VOLUME_PX, VOLUME_MIN = 0.10, 2, 40              # volume: a part of 40+ px keeps max(10 %, 2 px) of its area
SWAP_LOW, SWAP_HIGH, SWAP_POSES, SWAP_BACK = 0.3, 2.0, 3, 0.7   # swap: a colour group dropping or doubling briefly
SPLIT_ROWS, SPLIT_COLS, SPLIT_RUN, SPLIT_MIN = 0.6, 0.6, 0.3, 10   # split: the torso's rows and columns; each side
HITCH_HOLD, HITCH_ELSE, HITCH_RIGID, HITCH_MIN = 10, 0.5, 0.7, 8  # hitch: frames held at 30 fps; the rest's change
SPLIT_BLOCK = 0.25                                       # split: a side's pixels off its rigid move
# --style redrawn (every pose a new drawing of the whole figure: frame by frame, or generated). Fitted on three idles
# of one character only (a generated idle the user accepted, two cut-out idles the user rejected as slow and stepped):
# see stepped. Rerun it on every redrawn animation judged since.
STEP_ROWS, STEP_TILE, STEP_COVER, STEPPED_RATE = 8, 0.15, 0.4, 6.0   # stepped: tile grid, a tile's change, a body
                                                                     # move's share of tiles, body moves a second
PATCH_MIN, PATCH_FRAC, PATCH_REACH, PATCH_SIZE = 12, 0.003, 0.12, 1.6   # lostmark: a patch's least px and share of
LOST_HAVE, LOST_RUNS = 0.6, 3                            # the figure, its reach a pose (of the height), its size swing;
GAP_LEN, GAP_RATE = 4, 5.0                               # marks on this share of the poses, gone this many times; gaps
SPOT_PX, SPOT_HUE, SPOT_SAT, SPOT_INK = 3, 1 / 8, 0.15, 45   # spots: a mark's most px; a patch tone's hue reach (of
SPOT_PAD, SPOT_REACH, SPOT_TOL, SPOT_DROP = 8, 12, 1, 0.4    # the circle), least saturation; ink's lightness; the
                                                             # window round a group, its search, a mark's slack in
                                                             # px, the share of a tone mark's lightness step
MAX_INPUT_FRAMES = 2048
MAX_INPUT_PIXELS = 8_000_000
MAX_CLIP_SECONDS = 120
MAX_PREVIEW_PIXELS = 80_000_000          # the 144-image bird preview is 72,532,800 pixels at the default zoom
MAX_PREVIEW_SIDE = 32_768


def hexrgb(v):
    return int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16)


def lum_hex(v):
    r, g, b = hexrgb(v)
    return 0.299 * r + 0.587 * g + 0.114 * b


class Spec:
    """What the check knows of a creature. Pixels are any hashable colour key; lum and rgb read one (default: hex)."""

    def __init__(self, ink=None, shadow=(), effects=(), eye=None, flier=False, idle="idle", move="move",
                 allow=None, glows_eye=(), lum=lum_hex, rgb=hexrgb, gait=True, fps=30, facing="right",
                 actions=None, speed=None, parts=None, squash=(), palette=None, glow=(), ref=None, marks=(),
                 sheets=(), min_rate=None, style="pixel", spots=None, eye_at=None):
        self.ink, self.shadow, self.effects = ink, set(shadow), set(effects)
        self.eye_at = tuple(eye_at) if eye_at else None   # (column, row) of the eye on a loop's first frame: which
                                                          # piece of the eye colour is the eye (see _eye_piece)
        self.eye, self.flier, self.idle, self.move = eye, flier, idle, move
        self.allow, self.glows_eye, self.lum, self.rgb = allow or {}, set(glows_eye), lum, rgb
        self.gait = gait                                  # it walks on legs (a snake or a slug does not: no stiff;
        self.fps = fps                                    # hop then judges every loop); the rate the loops play at
        self.facing = facing                              # "right" or "left": where reshape's face window lies
        self.actions = {k: parse_action(f"{k}:{v}", facing)[1] if isinstance(v, str) else tuple(v)
                        for k, v in (actions or {}).items()}   # {loop: (kind, direction)}: see parse_action
        self.speed = speed                                # the road's scroll, game px a frame (skate's readout)
        self.parts = dict(parts or {})                    # {loop: part-label frames, one flat colour a part}
        self.squash = set(squash)                         # part colours whose area changes on purpose (wings)
        self.palette = set(palette) if palette is not None else None   # the approved drawing's colours
        self.glow = set(glow)                             # colours shown in some frames on purpose (glow, glint, lid)
        self.ref = ref                                    # the approved drawing at game size, a frame
        self.marks = list(marks)                          # small defining marks (a gem, a lamp): on every frame
        self.sheets = set(sheets)                         # loops drawn as a sheet or by AI (swap judges them)
        self.min_rate = min_rate                          # choppy's floor for the idle and the move, updates a
                                                          # second (None: the fitted floors)
        self.style = style                                # "pixel": the cut-out rules (a drawing moved whole pixels,
                                                          # its texture kept); "redrawn": every pose a new drawing
        self.spots = dict(spots or {})                    # {group name: [(row, column)]}: small marks of the
                                                          # approved drawing (ref), placed by eye (spots)

    def is_ink(self, v):
        return v in self.ink if self.ink is not None else v is not None and self.lum(v) < 40


# ---- frame helpers ---------------------------------------------------------------------------------------------
def _pieces(f, skip):
    pts = {(x, y) for y, r in enumerate(f) for x, v in enumerate(r) if v is not None and v not in skip}
    sizes, seen = [], set()
    for q in pts:
        if q in seen:
            continue
        stack, n = [q], 0
        seen.add(q)
        while stack:
            x, y = stack.pop()
            n += 1
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    m = (x + a, y + b)
                    if m in pts and m not in seen:
                        seen.add(m)
                        stack.append(m)
        sizes.append(n)
    return sorted(sizes)


def _shifted(f, dy):
    h, w = len(f), len(f[0])
    return [f[y - dy] if 0 <= y - dy < h else [None] * w for y in range(h)]


def _diff(p, q):
    return sum(1 for y in range(len(p)) for x in range(len(p[0])) if p[y][x] != q[y][x])


def _change(p, q):
    """Pixels changed from p to q, p first moved a pixel up or down if that fits better (a bob is on purpose)."""
    return min(_diff(_shifted(p, dy), q) for dy in (-1, 0, 1))


def _change_action(p, q):
    """_change in a declared action, where the whole figure moved a pixel sideways is forgiven too: an attack's
    overshoot shows the rest pose a pixel back for a frame on purpose (Slynyrd 9 and 53, text), a recoil the same."""
    left = [r[1:] + [None] for r in p]
    right = [[None] + r[:-1] for r in p]
    return min(_change(p, q), _diff(left, q), _diff(right, q))


def _aligned(frames, dys=None):
    """Each frame moved up or down (at most 2 px) to match the first best, so a bob does not read as flicker.
    dys, if a list, receives each frame's shift."""
    out = [frames[0]]
    if dys is not None:
        dys.append(0)
    for f in frames[1:]:
        dy = min((-2, -1, 0, 1, 2), key=lambda d: _diff(_shifted(f, d), frames[0]))
        out.append(_shifted(f, dy))
        if dys is not None:
            dys.append(dy)
    return out


def _codes(f):
    keys = {}
    return np.array([[0 if v is None else keys.setdefault(v, len(keys) + 1) for v in r] for r in f])


def _best_dx(a, b, reach=6):
    """The sideways shift (and up to 3 px up or down) bringing frame a nearest frame b: (dx, pixels still off).
    The shift lets air in at the edge it leaves (_sh): nothing wraps round, so a shape touching one edge never
    comes back in at the other and matches what is not there (a band across the frame, its texture scrolling)."""
    best, best_dx = None, 0
    for dx in range(-reach, reach + 1):
        for dy in range(-3, 4):
            m = int((_sh(a, dy, dx) != b).sum())
            if best is None or m < best or (m == best and abs(dx) < abs(best_dx)):
                best, best_dx = m, dx
    return best_dx, best


def _flips(seq, lum, skip=(), raw=None):
    """How often a pixel takes a tone for one frame and goes straight back (A, B, A), skip's frames left out.
    raw, if given, is the same pixel's tones at frame k's own place in the unaligned frames k-1, k, k+1 (one triple
    per k): where those step monotonically (B's lightness between its neighbours', and not equal to both), the A, B, A
    seen after aligning is a sub-pixel in-between on an edge that moved a whole pixel with the bob, not a flicker."""
    n = len(seq)

    def mono(t):
        if t is None or any(v is None for v in t) or t[0] == t[2]:
            return False
        a, b, c = (lum(v) for v in t)
        return min(a, c) <= b <= max(a, c)
    return sum(1 for k in range(n) if k not in skip and seq[k - 1] == seq[(k + 1) % n] != seq[k]
               and (seq[k] is None or seq[k - 1] is None or abs(lum(seq[k]) - lum(seq[k - 1])) >= FAINT)
               and not (raw is not None and mono(raw[k])))


def _near_turns(frames):
    """The frames at and beside a stroke's end (the frames either side much alike, as a wing at the bottom of its
    beat): a pixel the stroke passes there goes A, B, A on purpose. Turns on over a quarter of the loop are no
    stroke but a texture crawling: nothing is left out then."""
    n = len(frames)
    step = [_diff(frames[k], frames[k - 1]) for k in range(n)]
    turns = [k for k in range(n) if 0 < (d := min(step[k], step[(k + 1) % n]))
             and _diff(frames[k - 1], frames[(k + 1) % n]) <= d / 2]
    return set() if len(turns) > n / 4 else {(k + j) % n for k in turns for j in (-1, 0, 1)}


def _figure(f, spec):
    rows = list(f)
    while rows and all(v is None or v in spec.shadow for v in rows[-1]):
        rows.pop()
    return rows


# ---- array helpers for the motion checks (choppy, snap, tick, hop, vanish, shallow, reshape) ---------------------
def _arrays(frames, spec, keys=None):
    """The creature alone (effects and shadow removed, A0) as int arrays sharing one key table: 0 is air.
    Returns (arrays, the set of ink codes); keys, if a dict, receives the table {colour: code}."""
    keys, ink = ({} if keys is None else keys), set()
    skip = spec.effects | spec.shadow
    out = []
    for f in frames:
        a = np.zeros((len(f), len(f[0])), np.int32)
        for y, r in enumerate(f):
            for x, v in enumerate(r):
                if v is not None and v not in skip:
                    if v not in keys:
                        keys[v] = len(keys) + 1
                        if spec.is_ink(v):
                            ink.add(keys[v])
                    a[y, x] = keys[v]
        out.append(a)
    return out, ink


def _sh(a, dy, dx=0):
    """a moved dy rows down and dx columns right (negative: up, left), air filling in; nothing wraps round."""
    h, w = a.shape
    out = np.zeros_like(a)
    if abs(dy) >= h or abs(dx) >= w:
        return out
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def _nd(p, q):
    return int((p != q).sum())


def _chg(p, q):
    """_change on arrays: pixels changed from p to q, a 1-px bob forgiven."""
    return min(_nd(_sh(p, dy), q) for dy in (-1, 0, 1))


def _area(arrs):
    return sum(int((a > 0).sum()) for a in arrs) / len(arrs)


def _holds(flags):
    """Frames from one move to the next, cyclic (flags: does step k move)."""
    n, mv = len(flags), [k for k, f in enumerate(flags) if f]
    return [((mv[(i + 1) % len(mv)] - mv[i]) % n) or n for i in range(len(mv))]


def _blobs(m):
    """8-connected pieces of a boolean array, each as (ys, xs) index arrays."""
    pts = set(zip(*np.nonzero(m)))
    out = []
    while pts:
        stack = [pts.pop()]
        piece = list(stack)
        while stack:
            y, x = stack.pop()
            for b in (-1, 0, 1):
                for a in (-1, 0, 1):
                    q = (y + b, x + a)
                    if q in pts:
                        pts.remove(q)
                        stack.append(q)
                        piece.append(q)
        out.append((np.array([p[0] for p in piece]), np.array([p[1] for p in piece])))
    return out


def _dilate(m, r):
    out = np.zeros_like(m)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= _sh(m, dy, dx)
    return out


def _stabilised(arrs, ink):
    """Each frame moved by the whole rows that best match the rest pose's colours exactly (ink excluded: an outline
    matches anywhere), so a whole-figure lift is taken out before reading what changed (vanish, shallow). The rest
    pose is the one the loop shows most often (ties: the fullest), not frame 0, so the reading does not depend on
    where the loop starts: started inside a far wing's hidden stretch, frame 0 aligned the others against the gap
    and the vanish went unseen."""
    seen = {}
    for a in arrs:
        seen.setdefault(a.tobytes(), [a, 0])[1] += 1
    ref = max(seen.values(), key=lambda e: (e[1], int((e[0] > 0).sum()), (e[0] > 0).tobytes()))[0]
    can = (ref > 0) & ~np.isin(ref, list(ink))
    out = []
    for a in arrs:
        dy = max(range(-8, 9), key=lambda d: (int(((_sh(a, d) == ref) & can).sum()), -abs(d)))
        out.append(_sh(a, dy))
    return out


# ---- the check -------------------------------------------------------------------------------------------------
def _frame_size(f):
    return len(f[0]), len(f)


def _shadow_pixels(f, colours):
    return {(x, y) for y, row in enumerate(f) for x, v in enumerate(row) if v in colours}


def check(loops, spec, warns=None):
    """loops: {name: [frame, ...]}, a frame a list of rows of colour keys or None. Returns fault lines; warns, if a
    list, receives the warning lines (looked at, not counted as faults)."""
    return [str(line) for line in _check(loops, spec, warns)]


def _check(loops, spec, warns=None):
    faults, warns = [], (warns if warns is not None else [])
    allf = [(a, i, f) for a, v in loops.items() for i, f in enumerate(v)]
    sizes = {_frame_size(f) for _, _, f in allf}
    if len(sizes) > 1:
        return [f"size: frames differ {sorted(sizes)}"]
    skip = spec.effects | spec.shadow
    empty_frames = {}
    for a, i, f in allf:
        drawn = [(x, y) for y, r in enumerate(f) for x, v in enumerate(r) if v is not None and v not in skip]
        if not drawn:
            faults.append(f"empty: {a}[{i}]")
            empty_frames.setdefault(a, set()).add(i)
            continue
        stray = [s for s in _pieces(f, skip)[:-1] if s > spec.allow.get(a, 0)]
        if stray:
            faults.append(f"apart: {a}[{i}] {len(stray)} piece(s) of {stray} px apart from the figure")
        if spec.eye is not None and a not in spec.glows_eye and not any(f[y][x] == spec.eye for x, y in drawn):
            faults.append(f"eye: {a}[{i}] has no eye ({spec.eye})")
        h, w = len(f), len(f[0])
        open_edge = sum(1 for x, y in drawn if not spec.is_ink(f[y][x])
                        and any(not (0 <= x + dx < w and 0 <= y + dy < h)
                                                      or f[y + dy][x + dx] is None
                                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
        if open_edge > 2:                                 # a redrawn style may line its edges in colour (selout)
            line = f"outline: {a}[{i}] {open_edge} coloured edge pixel(s) with no ink"
            (faults.append(line) if spec.style == "pixel" else warns.append("warn: " + line))
    palette_faults = palette(loops, spec)                # only temporal checks need a body in every frame
    all_loops = loops
    loops = {a: frames for a, frames in loops.items() if frames and a not in empty_frames}
    if not loops:                                         # spots reads each pose alone and passes over empty ones
        return faults + palette_faults + marks(all_loops, spec, warns, empty_frames) + spots(all_loops, spec, warns)
    for a, frames in loops.items():
        kind = spec.actions.get(a, (None, None))[0]
        figs = [[[None if v in skip else v for v in r] for r in f] for f in frames]
        if spec.flier:
            if spec.shadow:
                rest_shadow = _shadow_pixels(frames[0], spec.shadow)
                if any(_shadow_pixels(f, spec.shadow) != rest_shadow for f in frames[1:]):
                    faults.append(f"ground: {a} the shadow moves")
        elif kind != "jump":                              # a declared jump leaves the ground on purpose
            feet = {max(y for y, r in enumerate(f) for v in r if v is not None) for f in figs}
            if len(feet) > 1 and a != spec.move:
                faults.append(f"ground: {a} the feet leave the ground line (rows {sorted(feet)})")
            elif len(feet) > 1 and spec.gait:             # the move of a legged body: a warning only
                warns.append(f"warn: ground: {a} the lowest drawn row moves (rows {sorted(feet)}): a lift applied "
                             f"to the whole figure takes the feet off the ground twice a stride; raise the body, not "
                             f"the feet. A run, a gallop or a hopping gait leaves the ground on purpose")
        chg = _change_action if a in spec.actions else _change
        steps = [chg(figs[k], figs[(k + 1) % len(figs)]) for k in range(len(figs))]
        moving = [s for s in steps if s]
        mean = sum(moving) / len(moving) if moving else 0
        faults += _jump(a, steps, figs, kind)
        faults += _knocked(a, frames, spec)

        body = sum(v is not None for r in figs[0] for v in r)
        if a == spec.move and body and mean / body < STILL:
            faults.append(f"still: {a} changes {mean / body:.1%} of the figure a frame")
        if spec.style == "pixel":                         # a redrawn pose redraws its texture on purpose
            faults += _shimmer(a, figs, spec)
    redrawn = spec.style == "redrawn"
    face = reshape(loops, spec, warns)
    if redrawn:                                           # a redrawn face changes its pixels on purpose
        warns += ["warn: " + x for x in face]
        face = []
    faults = (faults + eye_jumps(loops, spec, warns) + frozen(loops, spec) + stiff(loops, spec)
              + (stepped(loops, spec) + lostmark(loops, spec) + gaps(loops, spec) if redrawn
                 else cadence(loops, spec)) + snap(loops, spec)
              + tick(loops, spec, warns) + hop(loops, spec) + vanish(loops, spec) + shallow(loops, spec)
              + face + palette_faults + marks(all_loops, spec, warns, empty_frames) + spots(all_loops, spec, warns))
    for later in (action, boil, seam, skate, gait, parts, orphans, doubles, blend, drift, swap, split,
                  hitch):                                 # warnings
        later(loops, spec, warns)
    return faults


def _jump(a, steps, figs, kind):
    """A change far over the loop's usual step (jump). steps: the pixels changed from each frame to the next (a
    1-px bob forgiven). The steps meant to be big are left out first: a declared strike's own step (strike judges
    it) and a declared jump's two biggest (its launch and its landing). The usual step is then the mean of the
    moving steps left once the two biggest are also set aside: a pose out of order makes two big steps (into it
    and out of it), and with them in the mean a short loop could hardly fire (on 6 moving steps or fewer the
    bigger of two alike big steps can never pass 3.2 times a mean both are part of; on 8 it must be 12 times the
    others). Fault when the biggest step left is over JUMP times the usual. Under 4 usual steps the base is thin
    (a sparse idle: a 3-px blink and one ear flick out and back): the step must then also change SNAP_STEP of the
    figure, snap's big change. Under 2 usual steps (3 moving steps or fewer; 4 in a declared strike, 5 in a
    declared jump) there is no usual step to compare with: this test is off and only the sideways one (_knocked)
    runs. Fitted on the 13 clean loops of this repo (the selftest's walker and flier, which examples/ holds too,
    and the showcase's nine) and examples/broken_move.png, by one person's look: the clean loops' ratios run
    1.35-3.25 (the lizard's idle highest), the broken move's 5.56. JUMP 3.6 keeps about 10 % over the highest
    clean loop and 54 % under the broken one. On a long loop (36 steps) leaving two steps out raises the ratio
    about 1.13 times, so 3.6 is there as strict as 3.2 against the plain mean. Not yet rerun on the private set of
    39 creatures the motion thresholds were fitted to: rerun it on your accepted animations before trusting it."""
    moving = sorted(s for s in steps if s)
    drop = {"strike": 1, "jump": 2}.get(kind, 0)          # big on purpose: a strike's own step, a jump's launch
    if drop and len(moving) > drop:                       # and landing
        moving = moving[:-drop]
    top = moving[-1] if moving else 0
    usual = moving[:-2]                                   # a pose out of order makes two big steps: both left out
    base = sum(usual) / len(usual) if len(usual) >= 2 else 0
    body0 = sum(1 for r in figs[0] for v in r if v is not None)
    if base and top > JUMP * base and (len(usual) >= 4 or top >= SNAP_STEP * body0):
        return [f"jump: {a} a change of {top} px against a usual {base:.0f} (frame {steps.index(top)})"]
    return []


def _knocked(a, frames, spec):
    """A pose knocked sideways out of step (jump). The frames are collapsed into cyclic runs of identical frames
    (a pose held on twos or threes is one pose), and each pose is compared with the distinct pose before it and the
    one after it: it fits both moved by one dx (2 px or more) while they fit each other (within 1 px), or it fits
    one of them moved 2 px or more with almost nothing else changed (3 % of the figure). On ones the neighbours are
    the frames either side; on twos they are the poses either side of the hold, not the hold's own twin. The whole
    run is reported: "move[6-7] (a held pose)"."""
    arr, _ = _arrays(frames, spec)
    runs, n, out = _same_runs(arr), len(arr), []
    P = len(runs)
    if P < 2:
        return out
    for i, (k0, ln) in enumerate(runs):
        p, c, q = arr[runs[i - 1][0]], arr[k0], arr[runs[(i + 1) % P][0]]
        (dp, mp), (dq, mq), (pq, _) = _best_dx(c, p), _best_dx(c, q), _best_dx(p, q)
        twin = [d for d, m in ((dp, mp), (dq, mq)) if abs(d) >= 2 and m <= 0.03 * int((c != 0).sum())]
        if (dp == dq and abs(dp) >= 2 and abs(pq) <= 1) or twin:
            where = f"{a}[{k0}]" if ln == 1 else f"{a}[{k0}-{(k0 + ln - 1) % n}] (a held pose)"
            out.append(f"jump: {where} is knocked {abs((twin or [dp])[0])} px sideways out of step")
    return out


def _raw_triples(frames, dys, x, y):
    """For the aligned pixel (x, y): per frame k, the tones at frame k's own source place (row y - dys[k]) in the
    unaligned frames k-1, k, k+1 (None off the frame). _flips reads them to tell a sub-pixel step from a flicker."""
    n, h = len(frames), len(frames[0])
    return [tuple(frames[j % n][y - dys[k]][x] for j in (k - 1, k, k + 1)) if 0 <= y - dys[k] < h else None
            for k in range(n)]


def _shimmer(a, frames, spec):
    """Texture crawl: pixels drawn in every (bob-aligned) frame that take a tone for 0.1 s at most (3 frames at 30
    fps, scaled with spec.fps) and go straight back to the tone before it, on at least a sixth of the frames and at
    least 3 times a loop, over SHIMMER of those pixels. Each pixel is read by its own runs of one tone, so a texture
    redrawn on a drawing held 2 or 3 frames (A, A, B, B, A, A) counts as well as one on ones (A, B, A); a tone held
    longer than 0.1 s is a pose. The floor of 3 is for short loops: a two-step walk passes a leg over the same pixel
    twice a loop. Not counted: a flip on a pose at or beside a stroke's turn (_near_turns, read on the distinct
    poses, since held frames make every other step zero), between tones too alike to see (FAINT), or one that steps
    monotonically in the unaligned frames (a sub-pixel in-between on an edge that moved with the bob).
    Measured on this repo only (by one person's look; the private 39-creature set was not rerun): the selftest's
    cases all hold; the 13 clean loops (the showcase's nine, the walker and the flier) give no fault, nor do the
    walker and flier thinned to 15 and 10 fps or with every frame held 2 and 3 times; a texture alternating between
    two tones is caught on ones, twos and threes. Its limit: a texture redrawn at random is caught on ones but not on
    twos or threes, where it changes half or a third as often and a pixel's flips stay under the floor. Reading the
    poses alone (collapsing held frames and running the old test on them) was tried and refused: the clean bird's
    move then fails (47 of 762 steady pixels), and a texture changing on its own clock, apart from the poses, is
    missed."""
    dys = []
    al = _aligned(frames, dys)
    n, h, w = len(al), len(al[0]), len(al[0][0])
    held = [(x, y) for y in range(h) for x in range(w) if all(f[y][x] is not None for f in al)]
    runs = _same_runs(frames)                             # the loop's distinct poses, cyclic
    if not held or len(runs) <= 4:
        return []
    poses = [al[k] for k, _ in runs]
    near = set()                                          # every frame of a pose at or beside a stroke's turn
    for i in _near_turns(poses):
        k0, ln = runs[i]
        near |= {(k0 + j) % n for j in range(ln)}
    short = math.ceil(3 * spec.fps / 30 - 1e-9)           # 0.1 s: a tone shown longer is a pose, not a flicker
    need = max(3, n / 6)
    hh = len(frames[0])

    def flips(x, y):
        seq = [f[y][x] for f in al]
        if len(set(seq)) < 2:
            return 0
        s = next(k for k in range(n) if seq[k] != seq[k - 1])
        R = []                                            # [first frame, length, tone], cyclic from a change
        for j in range(n):
            k = (s + j) % n
            if R and R[-1][2] == seq[k]:
                R[-1][1] += 1
            else:
                R.append([k, 1, seq[k]])
        m, c = len(R), 0
        for i, (k0, ln, v) in enumerate(R):
            p, q = R[i - 1], R[(i + 1) % m]
            if m < 3 or ln > short or p[2] != q[2] or abs(spec.lum(v) - spec.lum(p[2])) < FAINT:
                continue
            if any((k0 + j) % n in near for j in range(ln)):
                continue
            sy = y - dys[k0]                              # the sub-pixel in-between: monotone in the raw frames
            if 0 <= sy < hh:
                tr = (frames[(k0 - 1) % n][sy][x], frames[k0][sy][x], frames[(k0 + ln) % n][sy][x])
                if all(u is not None for u in tr) and tr[0] != tr[2]:
                    la, lb, lc = (spec.lum(u) for u in tr)
                    if min(la, lc) <= lb <= max(la, lc):
                        continue
            c += 1
        return c
    flick = sum(1 for x, y in held if flips(x, y) >= need)
    if flick / len(held) > SHIMMER:
        return [f"shimmer: {a} {flick} of its {len(held)} steady pixels flicker back and forth"]
    return []


def _body_moves(figs):
    """Does every change from one distinct pose to the next move the body: the top of BODY_TOPS of the columns both
    poses fill shifting? A body rising or swaying moves its topline along its whole length; a head nodding or a tail
    wagging over a still body moves only its own columns. False with fewer than 2 poses."""
    runs = _same_runs(figs)
    P = [figs[k] > 0 for k, _ in runs]
    if len(P) < 2:
        return False
    for i in range(len(P)):
        a, b = P[i - 1], P[i]
        cols = a.any(0) & b.any(0)
        if not cols.any() or (np.argmax(a, 0)[cols] != np.argmax(b, 0)[cols]).sum() < BODY_TOPS * cols.sum():
            return False
    return True


def _big_steps(figs, area):
    """Does every change from one distinct pose to the next change CADENCE_STEP of the figure or more (a walk whose
    poses are each a new drawing of the stride, not one part stepping over a still body)?"""
    runs = _same_runs(figs)
    P = [figs[k] for k, _ in runs]
    return len(P) >= 2 and all(_nd(P[i - 1], P[i]) >= CADENCE_STEP * area for i in range(len(P)))


def _breathes(figs, area):
    """Is the loop a breath: its body moves (_body_moves' test on some pose change), and every pose change that does
    not move the body is small (under CADENCE_STEP of the figure: a free tip's step, a tail's or a blink's)?"""
    runs = _same_runs(figs)
    P = [figs[k] for k, _ in runs]
    body = False
    for i in range(len(P)):
        a, b = P[i - 1] > 0, P[i] > 0
        cols = a.any(0) & b.any(0)
        if cols.any() and (np.argmax(a, 0)[cols] != np.argmax(b, 0)[cols]).sum() >= BODY_TOPS * cols.sum():
            body = True
        elif _nd(P[i - 1], P[i]) >= CADENCE_STEP * area:
            return False
    return body


def cadence(loops, spec):
    """How the motion is spread over the frames: choppy on the creature alone (effects and shadow removed, A0);
    uneven and lurch exactly as before (effects removed, a flier's shadow kept).

    choppy (A1). Perceived smoothness is set by the longest holds, not the mean (Klein et al. 2023): twos read smooth,
    threes start to read choppy, a 4-frame hold inside a cycle reads as a dropped rate. A move is a step changing over
    max(1, MOVE_EPS * A) px (A: the mean figure area); holds are the cyclic frames from one move to the next. A loop
    with fewer than 4 moves is a gesture. A rest (a hold of n/3 or more) is left out, frames and all, and the rest of
    the loop is judged; under 3 holds left, it is a gesture (a rest and a blink). With n' the frames left:
        rate = holds left * fps / n'    fault when rate < CHOPPY_RATE (10/s), however small the steps;
        dropped update                  fault when median(holds) >= 3 and some hold >= 2 * median(holds)
    (the second sees one lost update the mean rate hides: twelve poses on threes with one skipped, a 6-frame hold).
    A declared action (--action) may hold one key (a wind-up or a contact) up to ACTION_KEY frames at 30 fps: that
    single longest hold is left out, and the rest of the frames must still update at CHOPPY_RATE with no dropped
    update. A second held key is left out too when it is also within ACTION_KEY and at least twice the median of
    the rest (Slynyrd 56, text: the hammer holds its wind-up 250 ms and its follow-through 300 ms; the sword and
    the spear hold both as well; the selftest's blog_attacks). Every other hold keeps the rules: the proven limits
    govern idles, moves and an action's other frames.
    An idle in which every change of pose moves the body (_body_moves: the top of BODY_TOPS of the columns shifts, as
    a body rising or swaying does) may update more slowly, CHOPPY_BODY_IDLE a second (a pose held up to 0.4 s), and
    may hold one pose twice the others (not a dropped update: eased on purpose). Slynyrd's idles hold 100-400 ms a
    pose (Slynyrd's text: 52's 100 and 50 ms; measured from the GIF: 55's 200, 200, 400 ms, which his text calls
    less robotic than even holds), the torso moving on every pose (52, text); the faulty idles of the private set
    stepped one part over a still body. A move whose every pose change is big (_big_steps: CADENCE_STEP of the figure or
    more, each pose a new drawing of the stride) may update CHOPPY_WALK (5.2) times a second: Slynyrd's walks and
    runs hold a pose 80-200 ms (text: 8's run 80 and 160 ms, 58's 100, 60's 120; measured from the GIFs: 25's and
    50's walks 8 x 140 ms, 7.1 a second, 50's six poses at 200, 180, 180 ms, 5.4), while the private set rejected
    four walk drawings held 6 frames (exactly 5 a second, the selftest's few_drawings). The margin between the two
    is narrow (5.0 to 5.4); the likely difference is the sprite's size and texture (45's 200 ms walk is a 16 px
    sprite, text). A move stepping one part over a still body keeps the CHOPPY_RATE floor. What the idle and walk floors
    no longer catch: an idle moving its whole body 2.5-10 times a second, a walk of big pose changes 5.2-10 times a
    second; an idle moving its whole body 2 times a second is still choppy (relaxed_bounds). Spec.min_rate (--min-rate)
    sets the floor of the idle and the move outright, for a style held longer (his 8-16 px sprites, 200-800 ms a
    pose). Not rerun on the private 39-creature set.
    Leaving the rest out, rather than the whole loop, was measured on this repo only: the selftest holds (a dead stop
    is still snap's; the declared bite and leap stay clean), the 13 clean loops give no fault, and an idle stepped
    every 6 frames after a 12-frame rest, or four walk drawings with the last held 14 frames more, are caught (they
    passed when a rest excused the loop). The risk: an accepted idle with a rest whose other poses are held long
    would now fail. Not rerun on the private 39-creature set.

    uneven: the holds between moves (here a move is over MOVE_MIN of the figure: a blink or a glint is not) differ by
    2 frames or more and by twice (one long rest, at least twice the next longest, is an idle's pause and is left
    out). Among equally long action keys, prefer the pose with more changed pixels across its entrance and exit.
    lurch: the median ratio of one move to the next over LURCH (a whole-body bob after a small leg step: a hitch
    on each beat). uneven and lurch only where the moves are big enough to see (over CADENCE_STEP of the figure), and
    on a cycle of moves (four or more; six for lurch): one gesture in an idle is drawn on purpose. Neither judges an
    idle that breathes (_breathes: its body moves whole, and its other pose changes are a free tip's small steps):
    a breath of whole-pixel steps is eased on purpose, slow over the top and quick on the drop (Slynyrd 52, text),
    so its holds differ, and its body's one-pixel steps fall between small ones of the free tips (a tail's) that
    follow it. An idle whose body stands while its parts
    step at uneven holds is still judged (the selftest's idle stepping its head and tail at 1 and 3 frames in turn:
    uneven). What this no longer catches: a whole-body breath whose holds stutter (1, 3, 1, 3) rather than ease.
    Left out after one person judged the showcase's wolf idle so drawn smooth, on this repo only; not rerun on the
    private 39-creature set. Walks and actions keep both rules."""
    out = []
    for a, frames in loops.items():
        n = len(frames)
        if n < 4:
            continue
        key = round(ACTION_KEY * spec.fps / 30) if a in spec.actions else 0   # an action's held keys
        figs, _ = _arrays(frames, spec)
        area = _area(figs)
        steps = [_nd(figs[k], figs[(k + 1) % n]) for k in range(n)]
        flags = [s > max(1.0, MOVE_EPS * area) for s in steps]
        if sum(flags) >= 4:
            hs = _holds(flags)
            js, jn = list(hs), n
            rests = [h for h in hs if h >= n / 3]         # a rest is left out; what is left must still update
            for h in rests:
                js.remove(h)
                jn -= h
            if not rests and max(hs) <= key:              # an action's held keys (up to ACTION_KEY frames
                js.remove(max(hs))                        # each): the longest, and a second when it is held too
                jn = n - max(hs)                          # (the wind-up and the follow-through, Slynyrd 56)
                if len(js) > 3 and max(js) <= key and max(js) >= 2 * statistics.median(sorted(js)[:-1]):
                    jn -= max(js)
                    js.remove(max(js))
            body = a == spec.idle and _body_moves(figs)   # an idle moving its body on every pose: longer
            if spec.min_rate is not None and a in (spec.idle, spec.move):   # holds read smooth
                floor = spec.min_rate                     # the user's own style
            elif body:
                floor = CHOPPY_BODY_IDLE
            elif a == spec.move and _big_steps(figs, area):   # a walk whose every pose is a new drawing of the
                floor = CHOPPY_WALK                       # whole stride
            else:
                floor = CHOPPY_RATE
            if len(js) >= 3:
                rate, med = len(js) * spec.fps / jn, statistics.median(js)
                if rate < floor:
                    most = int(spec.fps // floor)                 # the longest hold that keeps the floor
                    how = (f"at {spec.fps:g} fps hold each pose {most} frame{'s' if most > 1 else ''} at most"
                           if most >= 1 else f"at {spec.fps:g} fps even a new pose every frame is too few: play it "
                           f"faster")
                    out.append(f"choppy: {a} updates {rate:.1f} times a second (holds {hs}): a few drawings each "
                               f"held long read as a dropped frame rate: a new pose at least every "
                               f"{1 / floor:.2g} s ({how}); spread the parts on one clock with staggered "
                               f"phases, or draw in-betweens")
                elif med >= 3 and max(js) >= 2 * med and not body:
                    out.append(f"choppy: {a} drops an update: a hold of {max(js)} frames among holds of {med:g} "
                               f"(holds {hs}): two ticks running gave one pose; stagger the parts' phases so "
                               f"something changes on every tick")
        if a == spec.idle and _breathes(figs, area):      # an idle breathing with its whole body is eased on
            continue                                      # purpose: not judged here
        figs, _ = _arrays(frames, Spec(ink=spec.ink, effects=spec.effects, lum=spec.lum))   # as before: effects
        area = _area(figs)                                # alone removed (the shadow kept) for uneven and lurch
        steps = [_nd(figs[k], figs[(k + 1) % n]) for k in range(n)]
        moving = [s for s in steps if s > MOVE_MIN * area]
        if len(moving) < 3:
            continue
        big = sorted(moving)[len(moving) // 2] / max(1.0, area)
        if big <= CADENCE_STEP:
            continue
        held = steps.count(0) > 0
        holds = _holds([s > MOVE_MIN * area for s in steps])
        longest = sorted(holds)
        rest = (len(longest) > 2 and longest[-1] >= 2 * longest[-2]   # an idle's one long pause: left out; an
                or 0 < longest[-1] <= key)                            # action's held key too
        second = (key and len(longest) > 3 and 0 < longest[-2] <= key   # an action's second held key
                  and longest[-2] >= 2 * statistics.median(longest[:-2]))
        exempt_ranks = ([0] if rest else []) + ([1] if second else [])
        seq = holds
        if exempt_ranks:
            # A hold sits between these two visible moves. A key pose stands out on entry and exit together.
            poses = [(h, p + q) for h, p, q in zip(holds, moving, moving[1:] + moving[:1])]
            ranked = sorted(poses, reverse=True)
            exempt = [ranked[rank] for rank in exempt_ranks]
            if longest[0] != longest[-1] and any(poses.count(k) > exempt.count(k) for k in exempt):
                # Identical evidence for more candidates than slots: give the ring a common start and direction.
                first = min(poses)
                poses = min(ring[i:] + ring[:i] for ring in (poses, poses[::-1])
                            for i, pose in enumerate(ring) if pose == first)
            seq = []
            for pose in poses:
                if pose in exempt:
                    exempt.remove(pose)
                else:
                    seq.append(pose[0])
        abrupt = sum(1 for p, q in zip(seq, seq[1:] + seq[:1]) if max(p, q) >= 2 * min(p, q) and abs(p - q) >= 2)
        if len(seq) >= 4 and abrupt >= len(seq) / 2:      # a cycle (a gesture of two or three moves is not); a
            # sway's ease doubling its hold at each turn is half less: ease at a stroke's turn lengthens holds gradually
            out.append(f"uneven: {a} holds {holds} frames between its moves in turn: hold every pose alike")
        pairs = sorted(max(p, q) / max(1, min(p, q)) for p, q in zip(moving, moving[1:] + moving[:1]))
        if held and len(moving) >= 6 and pairs[len(pairs) // 2] > LURCH:   # a held cycle alternating big and small
            out.append(f"lurch: {a} its moves alternate big and small (x{pairs[len(pairs) // 2]:.1f}) between held "
                       f"frames: move something on every frame, or spread the big change (a bob) over the steps")
    return out


def snap(loops, spec):
    """A2, the idle only: a dead stop, then a big change. s[k] = _change(F[k], F[k+1]) / A (a 1-px bob forgiven).
    For each step with s[k] > SNAP_STILL, hold = 1 + the still run (s <= SNAP_STILL) ending just before it, cyclic.
    Fault when some step has hold >= fps/3 (a third of a second) and s[k] >= SNAP_STEP. Why: the moving hold
    (Williams): an idle never stops dead and then lurches; a rest may be long only when what ends it is small (a
    blink, a glint). Actions are left out: an anticipation held and then sprung is on purpose. Fitted margins: the
    faulty idle held 30 frames before a 73 % step; accepted idles held 26 frames before a 7 % step (a blink and glow),
    12 before 2 %, and 1-4 frames before anything bigger."""
    a = spec.idle
    if a not in loops or len(loops[a]) < 4:
        return []
    figs, _ = _arrays(loops[a], spec)
    n, area = len(figs), max(1.0, _area(figs))
    s = [_chg(figs[k], figs[(k + 1) % n]) / area for k in range(n)]
    worst = None
    for k in range(n):
        if s[k] <= SNAP_STILL:
            continue
        run = 0
        while run < n - 1 and s[(k - 1 - run) % n] <= SNAP_STILL:
            run += 1
        hold = run + 1
        if hold >= spec.fps / 3 and s[k] >= SNAP_STEP and (worst is None or hold * s[k] > worst[0]):
            worst = (hold * s[k], hold, s[k], k)
    if worst:
        score, hold, step, k = worst
        return [f"snap: {a} stands dead still {hold} frames, then changes {step:.0%} of the figure at once (frame "
                f"{k}, score {score:.1f}): keep something small moving through the rest (a breath, a blink, a "
                f"glint) and ease the big change in and out (holds 3, 2, 2, 3), each step under a quarter"]
    return []


def _eye_piece(f, spec, last=None):
    """Where the eye is on frame f, as (row, column) floats: the centroid of one 8-connected piece of the eye colour.
    With no last place, the biggest piece (the frontmost on a tie), or with spec.eye_at the piece nearest that
    place; after that, the piece nearest the last place, so the eye is followed from frame to frame and not confused
    with the same colour used elsewhere. None if f has no pixel of the eye colour. Every check that reads the eye
    finds it here; a one-piece eye gives its plain centroid. The biggest piece is a guess: two eyes drawn a pixel
    apart are two 1-px pieces, and a 2-px bead of the same colour on a staff was read as the eye (a hand-drawn
    wizard sheet: its eye track, frozen and reshape then followed the bead). eye_at settles it."""
    pcs = _blobs(np.array([[v == spec.eye for v in r] for r in f]))
    if not pcs:
        return None
    cents = [(float(ys.mean()), float(xs.mean()), len(ys)) for ys, xs in pcs]
    if last is None and spec.eye_at:
        last = (spec.eye_at[1], spec.eye_at[0])
    if last is None:
        front = 1 if spec.facing != "left" else -1
        c = max(cents, key=lambda t: (t[2], front * t[1]))
    else:
        c = min(cents, key=lambda t: (t[0] - last[0]) ** 2 + (t[1] - last[1]) ** 2)
    return c[0], c[1]


def _eye_rows(frames, spec):
    """The eye's row per frame (followed by _eye_piece), its mean row rounded half up. None if a frame has no eye."""
    out, last = [], None
    for f in frames:
        last = _eye_piece(f, spec, last)
        if last is None:
            return None
        out.append(math.floor(last[0] + 0.5))
    return out


def _runs(levels):
    """Cyclic runs [level, length], starting at a change of level; [] when the level never changes."""
    n = len(levels)
    if len(set(levels)) == 1:
        return []
    s = next(k for k in range(n) if levels[k] != levels[k - 1])
    out = []
    for v in levels[s:] + levels[:s]:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return out


def _pulse(R, fps=30):
    """Extremum runs (both neighbours on one side) dwelling too briefly: under 3 frames, or under 4 when a neighbour
    is itself an extremum (a two-level square wave). A run inside a cluster of 3+ consecutive short runs (3 frames or
    less each: a sniff, a buzz) is exempt. The frame counts are for 30 fps (0.1 s and 0.13 s) and scale with fps:
    at 15 fps an extreme needs 2 frames, a square wave's level 2."""
    N, bad = len(R), []
    if N < 2:
        return bad
    d3, d4 = math.ceil(3 * fps / 30 - 1e-9), math.ceil(4 * fps / 30 - 1e-9)   # 0.1 s and 0.13 s, in frames

    def ext(i):
        return N <= 2 or (R[(i - 1) % N][0] - R[i % N][0]) * (R[(i + 1) % N][0] - R[i % N][0]) > 0

    def short(i):
        return R[i % N][1] <= d3
    for i, (v, ln) in enumerate(R):
        if not ext(i):
            continue
        if N >= 3 and short(i) and ((short(i - 1) and short(i - 2)) or (short(i - 1) and short(i + 1))
                                    or (short(i + 1) and short(i + 2))):
            continue
        need = d4 if (ext(i - 1) or ext(i + 1)) else d3
        if ln < need:
            bad.append((v, ln))
    return bad


def _lift_track(figs):
    """A flier's whole-body height: per step, dy = +-1 when shifting the frame by it cuts the diff below 0.6 of the
    unshifted diff, summed. Returns (track, closes): a track that does not come back is not a lift cycle."""
    def dy_of(p, q):
        d0 = _nd(p, q)
        best = min(((d0, 0), (_nd(_sh(p, -1), q), -1), (_nd(_sh(p, 1), q), 1)), key=lambda t: (t[0], abs(t[1])))
        return best[1] if best[1] and best[0] < 0.6 * d0 else 0
    y, ys = 0, [0]
    for k in range(len(figs) - 1):
        y += dy_of(figs[k], figs[k + 1])
        ys.append(y)
    return ys, y + dy_of(figs[-1], figs[0]) == 0


def tick(loops, spec, warns):
    """A3: a whole-pixel level left and regained within a few frames reads as a tick, not a lift. After rounding, a
    1-px sine of peak A is up for (pi - 2 asin(0.5/A)) / 2pi of the beat: 0.17 at A = 0.58, so a lift peaking just
    over half a pixel (or a head turn moving the eye 0.5-0.9 px) shows its top for two frames.
    Eye anchor (the idle; a warning in other loops, where a jump or a strike may be quick on purpose): the eye's row
    per frame split into cyclic runs; an extremum run must last 3 frames, 4 in a two-level square wave (_pulse; at
    30 fps, 0.1 s and 0.13 s, scaled with spec.fps).
    Shift anchor (a flier's idle and move, eye or none): the whole-body height track (_lift_track); rest = the level
    held longest; each run at another level is an excursion; duty = the shortest excursion / (n / the number of
    excursions), i.e. its length against its fair share of the loop; fault under TICK_DUTY. Fitted margins: the
    faulty hovers 0.11 and 0.14, the lowest accepted 0.21."""
    out = []
    for a, frames in loops.items():
        n = len(frames)
        if n < 4:
            continue
        if spec.eye is not None and a not in spec.glows_eye:
            ys = _eye_rows(frames, spec)
            R = _runs(ys) if ys else []
            bad = _pulse(R, spec.fps)
            if bad:
                v, ln = min(bad, key=lambda t: t[1])
                d4 = math.ceil(4 * spec.fps / 30 - 1e-9)  # _pulse's square-wave dwell at this fps
                line = (f"tick: {a} the eye reaches row {v} for only {ln} frame(s) (eye runs "
                        f"{[tuple(r) for r in R]}): a lift peaking 0.5-0.9 px or a quick head turn; make each level "
                        f"dwell {d4}+ frames (lift under 0.5 or 1+ game px), or keep the head's turn under half a "
                        f"pixel")
                (out if a == spec.idle else warns).append(line if a == spec.idle else "warn: " + line)
        if spec.flier and a in (spec.idle, spec.move):
            figs, _ = _arrays(frames, spec)
            ys, closes = _lift_track(figs)
            R = _runs(ys) if closes else []
            if len(R) >= 2:
                rest = max({v for v, _ in R}, key=lambda v: sum(ln for w, ln in R if w == v))
                ex = [ln for v, ln in R if v != rest]
                duty = min(ex) / (n / len(ex))
                if duty < TICK_DUTY:
                    out.append(f"tick: {a} the body leaves its rest height for only {min(ex)} frame(s) a beat "
                               f"(duty {duty:.2f}, runs {[tuple(r) for r in R]}): a lift peaking just over half a "
                               f"pixel; use no lift (under 0.5 px) or a whole one (1+ px) held a third of the beat")
    return out


def hop(loops, spec):
    """A4: a grounded body never lifts off its contact. The lowest-row check (ground) misses a body whose belly row
    stays while everything above it rises. G = the loop's lowest drawn row; C_k = the columns whose lowest drawn
    cell lies on G; lift = min|C_k| / median|C_k|. For each step changing at least HOP_STEP of the figure,
    share = 1 - min over dy in +-1, +-2 of diff(shift(F_k, dy), F_k+1) / diff(F_k, F_k+1): how much of the step a
    rigid vertical shift explains, counted only for a step that opens (or closes) air right above the contact on
    half the contact's columns or more: the body leaving its feet. A body rising whole over planted feet whose legs
    stretch to keep it joined (a breath) shifts rigidly too, but it stays on its feet. Fault when lift < HOP_LIFT or
    share >= HOP_SHARE. The air test was added on this repo's showcase only (the wolf's breath, its legs stretching
    under a trunk risen whole, judged right by one person; the selftest's body lifted off its feet's row still
    fails); not rerun on the private 39-creature set. What this no longer catches: a body rising whole a pixel over
    its feet while its legs stretch to keep it joined, whatever the reason (the selftest's breath passes); a body
    lifted off its feet's row, air opening above the contact, is still a hop (lift_off).
    Scope: the idle of any non-flier, and every loop of a legless body (gait False). A legged walk rises on purpose
    (rigid shares 0.14-0.35), a legged action may jump, and a flier is off the ground anyway."""
    if spec.flier:
        return []
    out = []
    for a, frames in loops.items():
        if a != spec.idle and spec.gait:
            continue
        figs, _ = _arrays(frames, spec)
        n, area = len(figs), _area(figs)
        if n < 2 or not area:
            continue
        rows = [np.nonzero(f.any(1))[0] for f in figs]
        G = max(int(r.max()) for r in rows if len(r))
        C = []
        for f in figs:
            low = np.where(f.any(0), f.shape[0] - 1 - np.argmax((f > 0)[::-1], 0), -1)
            C.append(int((low == G).sum()))
        lift = min(C) / max(1.0, statistics.median(C))
        share = 0.0

        def gaps(f):                                      # contact columns with air right above the contact
            if G < 1:
                return 0
            return int(((f[G] > 0) & (f[G - 1] == 0)).sum())
        for k in range(n):
            p, q = figs[k], figs[(k + 1) % n]
            c = _nd(p, q)
            if c and c >= HOP_STEP * area and abs(gaps(q) - gaps(p)) >= 0.5 * max(1, min(C[k], C[(k + 1) % n])):
                share = max(share, 1 - min(_nd(_sh(p, dy), q) for dy in (-2, -1, 1, 2)) / c)
        if lift < HOP_LIFT or share >= HOP_SHARE:
            why = (f"its contact on row {G} shrinks to {lift:.0%} of the usual" if lift < HOP_LIFT
                   else f"{share:.0%} of a big step is the whole body shifted up or down")
            out.append(f"hop: {a} the body lifts off the ground ({why}): keep the belly and feet on the ground row; "
                       f"move the parts above it (neck, head, arches), never the whole layer")
    return out


def vanish(loops, spec):
    """A5: a part never blinks out at a stroke's turning point (the far wing always shows a little). Frames are
    stabilised for whole-figure lift. For each transition i -> i+1, 'gone' blobs are 8-connected pieces of F_i lying
    over VANISH_R px from F_i+1, 'came' blobs of F_i+1 over VANISH_R px from F_i. An event is a blob of VANISH_MIN+ px
    whose place stays empty (under 1/3 of it within VANISH_R of the figure) for VANISH_HOLD+ frames, with under half
    its size arriving (or leaving) in the same transition. r4 = blob px / (the mean occupancy change of the
    transitions while the place is empty * the loop's median hold): a big piece going while everything else is slow
    is the turning-point signature; a fast stroke changes much around it. The median hold (moves counted as choppy
    counts them) makes r4 a change per update, not per frame: a sheet holding each drawing 3 frames has two still
    transitions to every moving one, and without it a wing coming up in one drawing step read as a vanish (an accepted
    12-drawing move on twos, r4 1.44 per frame, 0.72 per update). Holding every pose h frames leaves r4
    as it was. Fault when r4 >= VANISH_R4. Fitted margins: the faulty idles 1.22 and 1.50 (updating every frame), the
    highest accepted 0.92. A part covered by others when it vanishes is not seen: a rig should lint its hide rule
    instead."""
    out = []
    for a, frames in loops.items():
        n = len(frames)
        if n < 4:
            continue
        arrs, ink = _arrays(frames, spec)
        area = _area(arrs)                                # the loop's usual hold (moves as choppy counts them):
        flags = [_nd(arrs[k], arrs[(k + 1) % n]) > max(1.0, MOVE_EPS * area) for k in range(n)]
        hold_n = statistics.median(_holds(flags)) if any(flags) else 1   # a sheet on threes moves a third as
        ms = [s > 0 for s in _stabilised(arrs, ink)]      # much per frame as per update
        dil = [_dilate(m, VANISH_R) for m in ms]
        ch = [int((ms[i] ^ ms[(i + 1) % n]).sum()) for i in range(n)]
        best = None
        for i in range(n):
            gone = _blobs(ms[i] & ~dil[(i + 1) % n])
            came = _blobs(ms[(i + 1) % n] & ~dil[i])
            sg, sc = sum(len(b[0]) for b in gone), sum(len(b[0]) for b in came)
            for blob, kind in [(b, "gone") for b in gone] + [(b, "came") for b in came]:
                s = len(blob[0])
                if s < VANISH_MIN or (sc if kind == "gone" else sg) >= s / 2:
                    continue
                hold = 0
                for j in range(1, n):
                    k = (i + j) % n if kind == "gone" else (i + 1 - j) % n
                    if dil[k][blob].sum() / s < 1 / 3:
                        hold += 1
                    else:
                        break
                if hold < VANISH_HOLD:
                    continue
                idx = [(i + d) % n if kind == "gone" else (i - d) % n for d in range(1, hold + 1)]
                r4 = s / max(1.0, hold_n * sum(ch[j] for j in idx) / len(idx))
                # A part going and coming back are one event read from both ends; on a tie report it going, so
                # the loop's start does not pick the end.
                if best is None or (round(r4, 9), kind == "gone") > (round(best[0], 9), best[4] == "gone"):
                    best = (r4, s, hold, i, kind)
        if best and best[0] >= VANISH_R4:
            r4, s, hold, i, kind = best
            out.append(f"vanish: {a} a {s}-px piece {'switches off' if kind == 'gone' else 'switches on'} at "
                       f"frame {(i + 1) % n} and its place stays empty {hold} frames while the rest barely moves (r4 "
                       f"{r4:.2f}): a far wing hidden at the turn of its stroke; let it show (25-30 % of it) or "
                       f"hide it only while it crosses edge-on")
    return out


def _lowfrac(frames, spec):
    """Stabilised for lift; per cell the transitions whose colour changes. Returns (share of the changes lying below
    the middle row of the figure's union, share of the union's rows that ever change, share of its cells that ever
    change, total changes)."""
    arrs, ink = _arrays(frames, spec)
    st = _stabilised(arrs, ink)
    n = len(st)
    cnt = sum((st[i] != st[(i + 1) % n]).astype(int) for i in range(n))
    fig = np.any([s > 0 for s in st], 0)
    ys = np.nonzero(fig.any(1))[0]
    if not len(ys):
        return 0.0, 0.0, 0.0, 0
    y0, y1 = int(ys.min()), int(ys.max())
    tot = int(cnt.sum())
    low = int(cnt[int(math.floor((y0 + y1) / 2)) + 1:].sum())
    rows = int((cnt.any(1)[y0:y1 + 1]).sum()) / (y1 - y0 + 1)
    px = int(((cnt > 0) & fig).sum()) / max(1, int(fig.sum()))
    return low / max(1, tot), rows, px, tot


def shallow(loops, spec):
    """A6, a flier: an idle beats more slowly than the move, not with a different part of the wing. A squeeze about
    the wing's own lower edge moves only its top: the lower half of the bird is dead. lowfrac = the share of all
    (lift-stabilised) cell changes lying below the middle row of the figure's union; fault when
    lowfrac(idle) / lowfrac(move) < SHALLOW. With no move loop: the rows that ever change must cover SHALLOW_ROWS of
    the figure's rows and the changed cells SHALLOW_PX of its union. Fitted margins: the faulty idle 0.04, the lowest
    accepted 0.37; an absolute bar fails a beetle whose idle and move both keep low (0.07). Walkers are left out: a
    standing idle rightly keeps its legs still while its walk moves them."""
    if not spec.flier or spec.idle not in loops or len(loops[spec.idle]) < 4:
        return []
    li, rows, px, tot = _lowfrac(loops[spec.idle], spec)
    if not tot:
        return []
    a = spec.idle
    if spec.move in loops and len(loops[spec.move]) >= 4:
        lm = _lowfrac(loops[spec.move], spec)[0]
        if lm > 0 and li / lm < SHALLOW:
            return [f"shallow: {a} moves only the upper part ({li:.0%} of its changes in the lower half, against "
                    f"{lm:.0%} in the {spec.move}; ratio {li / lm:.2f}): beat the same wing less often, not less "
                    f"far: it must cross the shoulder line (edge-on, then under the belly)"]
    elif rows < SHALLOW_ROWS or px < SHALLOW_PX:
        return [f"shallow: {a} moves only part of the figure ({rows:.0%} of its rows, {px:.0%} of its pixels "
                f"ever change): beat the whole wing, crossing the shoulder line"]
    return []


def _distinct(frames):
    out = [frames[0]]
    for f in frames[1:]:
        if f != out[-1]:
            out.append(f)
    if len(out) > 1 and out[-1] == out[0]:
        out.pop()
    return out


def reshape(loops, spec, warns):
    """A7: the face is rigid. Aligned on itself, the head keeps its silhouette and ink lines (mouth line, jaw) unless
    a face move is drawn on purpose. AI sheets fail this first, redrawing the head in every cell.
    1. The eye: spec.eye's piece in the first pose (_eye_piece), or else the frontmost ink pixel in the front third
       with colour on 3 of its 4 sides. 2. The face window: rows eye +- r, columns from 1 px behind the eye forward
       (mirrored for facing left), r = max(3, round(0.12 * figure width)). 3. Distinct poses only; every pixel classed
       air, ink or colour. 4. For each pose change p -> q, q's window slid by dx, dy in [-3, 3] ([-7, 7] outside the
       idle, where a hop may carry the head far): the fewest class mismatches / p's drawn pixels in the window. 5.
       Fault in the idle when the mean over the pose changes > RESHAPE; a warning in other loops (an action may open
       its jaw).
    The mean, not the max: one accepted change of 0.41 (wisps passing the face) sits among zeros. A rigid head that
    bobs, slides or turns 1.5 degrees keeps its class map after the best shift. Fitted margins: the faulty idles 0.16
    and 0.13, the highest accepted 0.065."""
    out = []
    for a, frames in loops.items():
        poses = _distinct(frames)
        if len(poses) < 2:
            continue
        fx = spec.effects | spec.shadow
        cls = [np.array([[0 if v is None or v in fx else 1 if spec.is_ink(v) else 2 for v in r] for r in f])
               for f in poses]
        c0, f0 = cls[0], poses[0]
        xs = np.nonzero(c0.any(0))[0]
        if not len(xs):
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        left = spec.facing == "left"
        eye = None
        c = _eye_piece(f0, spec) if spec.eye is not None else None
        if c:
            eye = (round(c[1]), round(c[0]))
        else:
            h, w = c0.shape
            span = range(max(1, x0), min(w - 1, x0 + (x1 - x0) // 3 + 1)) if left else \
                range(max(1, x0 + 2 * (x1 - x0) // 3), min(w - 1, x1 + 1))
            for y in range(1, h - 1):
                for x in span:
                    if c0[y, x] == 1 and sum(c0[y + b, x + c] == 2 for c, b in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3:
                        if eye is None or (x < eye[0] if left else x > eye[0]):
                            eye = (x, y)
        if eye is None:
            continue
        ex, ey = eye
        r = max(3, round(0.12 * (x1 - x0)))
        cx0, cx1 = (ex - r, ex + 1) if left else (ex - 1, ex + r)

        R = 3 if a == spec.idle else 7
        M = r + R + 2                                     # a margin of -1 (outside the frame) round each pose
        pads = []
        for c in cls:
            P = np.full((c.shape[0] + 2 * M, c.shape[1] + 2 * M), -1)
            P[M:M + c.shape[0], M:M + c.shape[1]] = c
            pads.append(P)

        def win(P, dx, dy):
            return P[ey - r + dy + M:ey + r + dy + M + 1, cx0 + dx + M:cx1 + dx + M + 1]
        res = []
        for k in range(len(cls)):
            W0 = win(pads[k - 1], 0, 0)
            drawn = int((W0 > 0).sum())
            if not drawn:
                continue
            best = min(int(((W0 != (W1 := win(pads[k], dx, dy))) & (W0 >= 0) & (W1 >= 0)).sum())
                       for dx in range(-R, R + 1) for dy in range(-R, R + 1))
            res.append(best / drawn)
        if not res:
            continue
        mean = sum(res) / len(res)
        if mean > RESHAPE:
            line = (f"reshape: {a} the face changes shape between poses (mean {mean:.3f} of its pixels change class "
                    f"after the best alignment; worst {max(res):.2f}): draw the head once and move it whole (paste "
                    f"one approved head, placed by the eye), or read every drawing on one grid")
            (out if a == spec.idle else warns).append(line if a == spec.idle else "warn: " + line)
    return out


# ---- the redrawn style (--style redrawn) -----------------------------------------------------------------------
def _cover(p, q):
    """The share of the figure's tiles that change from pose p to pose q: the box both poses fill cut into tiles of
    STEP_ROWS to its height; a tile counts when the figure fills a quarter of it, and moves when STEP_TILE of its
    figure pixels change. A body redrawn whole moves nearly every tile; a band of rows stepped over a still body, or
    a sparkle, moves a few."""
    fig = (p > 0) | (q > 0)
    if not fig.any():
        return 0.0
    ys, xs = np.nonzero(fig)
    t = max(2, round((ys.max() - ys.min() + 1) / STEP_ROWS))
    diff = (p != q) & fig
    moving = total = 0
    for y in range(ys.min(), ys.max() + 1, t):
        for x in range(xs.min(), xs.max() + 1, t):
            f = int(fig[y:y + t, x:x + t].sum())
            if f < t * t / 4:
                continue
            total += 1
            moving += int(diff[y:y + t, x:x + t].sum() >= STEP_TILE * f)
    return moving / total if total else 0.0


def _body_times(figs):
    """The frames at which a new pose moves the whole body (_cover at least STEP_COVER), cyclic."""
    runs = _same_runs(figs)
    if len(runs) < 2:
        return []
    return [runs[i][0] for i in range(len(runs)) if _cover(figs[runs[i - 1][0]], figs[runs[i][0]]) >= STEP_COVER]


def stepped(loops, spec):
    """The redrawn style's cadence, for every loop but a declared action: the whole body must move often. A body
    move is a new pose changing STEP_COVER of the figure's tiles (_cover); fault when the loop has fewer than
    STEPPED_RATE of them a second. Played, a body that moves whole on every pose reads alive; one that holds still
    and steps a band of rows at a time (a breath rolling down the body), however many small glints and specks
    change between, reads slow and stepped, "like scanning".
    The three idles it was fitted on, one character, judged by the user playing them: a generated idle, accepted, 16
    poses at 8 fps, each new pose moving every tile (8 body moves a second); a cut-out idle with whole-pixel body
    steps on 9-frame holds and cloth steps between, rejected (3.3 a second, 0.3 s still); a cut-out idle whose body
    rose band by band with sparkles changing every frame, rejected (0.8 a second, up to 0.8 s still). 6 lies between
    the accepted 8 and the rejected 3.3: a guess on three samples, not a fitted margin."""
    out = []
    for a, frames in loops.items():
        n = len(frames)
        if a in spec.actions or n < 2:
            continue
        figs, _ = _arrays(frames, spec)
        times = _body_times(figs)
        rate = len(times) * spec.fps / n
        if rate < STEPPED_RATE:
            gaps = [((times[(i + 1) % len(times)] - times[i]) % n) or n for i in range(len(times))] or [n]
            out.append(f"stepped: {a} the whole body moves {rate:.1f} times a second (longest still "
                       f"{max(gaps) / spec.fps:.2f} s): it reads slow and stepped. Redraw the whole figure on every "
                       f"pose, at least {STEPPED_RATE:g} new poses a second, rather than stepping one band or part "
                       f"over a still body")
    return out


def _comps4(m):
    """4-connected pieces of a boolean array, each as (ys, xs) index arrays."""
    H, W = m.shape
    seen = np.zeros_like(m, bool)
    out = []
    for y, x in zip(*np.nonzero(m)):
        if seen[y, x]:
            continue
        stack, ys, xs = [(y, x)], [], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop()
            ys.append(cy)
            xs.append(cx)
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        out.append((np.array(ys), np.array(xs)))
    return out


def _enclosed(ys, xs, H, W):
    """How many pixels a patch (its pixels ys, xs) closes in: those its box holds that air from outside the box
    cannot reach in 4-connected steps (a mouth on a face, a stud on a coat)."""
    y0, x0 = ys.min() - 1, xs.min() - 1
    m = np.ones((ys.max() - y0 + 2, xs.max() - x0 + 2), bool)
    m[ys - y0, xs - x0] = False
    reach = np.zeros_like(m)
    border = [(y, x) for y in range(m.shape[0]) for x in (0, m.shape[1] - 1)] + \
             [(y, x) for x in range(m.shape[1]) for y in (0, m.shape[0] - 1)]
    stack = [p for p in border if m[p]]
    for p in stack:
        reach[p] = True
    while stack:
        cy, cx = stack.pop()
        for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
            if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not reach[ny, nx]:
                reach[ny, nx] = True
                stack.append((ny, nx))
    return int((m & ~reach).sum())


def _pose_ref(a, runs, i, n):
    k0, ln = runs[i]
    return f"{a}[{k0}]" if ln == 1 else f"{a}[{k0}-{(k0 + ln - 1) % n}]"


class _PoseFault(str):
    """A diagnostic carrying the original pose runs for the contact sheet."""

    def __new__(cls, text, loop, runs):
        line = super().__new__(cls, text)
        line.loop = loop
        line.runs = tuple(runs)
        return line


def lostmark(loops, spec):
    """The redrawn style: marks drawn inside a patch of one colour (a mouth on a face, a stud on a coat) that vanish
    in some poses. Every patch of one colour of PATCH_MIN px and PATCH_FRAC of the figure or more in the first pose
    is followed through the distinct poses: in each, the patch of its colour nearest its last place, within
    PATCH_REACH of the figure's height and within PATCH_SIZE times its last size either way (a patch not found in
    some pose is let go). In each pose, the pixels the patch closes in are its marks. Fault when the marks are there
    in LOST_HAVE of the poses and gone in LOST_RUNS or more separate runs of poses: a blink, once or twice a loop, is
    drawn on purpose; a mouth missing again and again is a generated frame's slip.
    Tried on: the generated wizard idle the user judged, whose mouth they saw missing in poses 9, 10, 13 and 15: the
    face's patch has marks in the other 12 and none in exactly those 4. On the same idle it also names the hat's
    patch in poses 1, 2, 10 and 15, where the user saw the hat's yellow specks lost; but the marks it counts there are
    1-px dark specks and holes, not the yellow specks, which sit across the hat's shades and close in no one patch,
    and the specks' partial losses (poses 4, 9, 13: some of the four left) it does not see. A search for the approved
    drawing's small marks in every pose was tried for them and refused: the generated poses redraw the specks a few
    px away and in another colour, and it named nearly the opposite poses. The two cut-out wizard idles, the
    showcase's nine loops, the fighter and six test creatures: nothing (the bird's two blinks and a beast's closing
    eye in its attack, one or two runs, are let go). Not proven beyond these."""
    out = []
    for a, frames in loops.items():
        if a in spec.actions:
            continue
        figs, ink = _arrays(frames, spec)
        runs = _same_runs(figs)
        if len(runs) < 3:
            continue
        P = [figs[k] for k, _ in runs]
        n, H, W = len(frames), *P[0].shape
        area = _area(P)
        rows = [np.nonzero(p.any(1))[0] for p in P]
        height = statistics.mean(int(r.max() - r.min() + 1) for r in rows if len(r))
        least = max(PATCH_MIN, PATCH_FRAC * area)
        reach = PATCH_REACH * height
        found = []
        for i, p in enumerate(P):
            found.append({})
            for c in np.unique(p):
                if c == 0 or c in ink or (p == c).sum() < least:
                    continue
                found[i][c] = [(ys, xs, (ys.mean(), xs.mean())) for ys, xs in _comps4(p == c) if len(ys) >= least]
        for c, seeds in found[0].items():
            for ys, xs, cen in seeds:
                track, last = [(ys, xs)], (len(ys), cen)
                for i in range(1, len(P)):
                    near = [(math.dist(ce, last[1]), y_, x_, ce) for y_, x_, ce in found[i].get(c, [])
                            if 1 / PATCH_SIZE <= len(y_) / last[0] <= PATCH_SIZE]
                    near = [t for t in near if t[0] <= reach]
                    if not near:
                        track = None
                        break
                    _, y_, x_, ce = min(near, key=lambda t: t[0])
                    track.append((y_, x_))
                    last = (len(y_), ce)
                if not track:
                    continue
                marks = [_enclosed(y_, x_, H, W) for y_, x_ in track]
                gone = [i for i, m in enumerate(marks) if not m]
                times = sum(1 for i in gone if (i - 1) % len(P) not in gone)
                if gone and len(P) - len(gone) >= LOST_HAVE * len(P) and times >= LOST_RUNS:
                    line = (f"lostmark: {a} the marks inside a patch at row {round(cen[0])}, column "
                            f"{round(cen[1])} (a mouth on a face, a stud on a coat: {marks[0]} px in the first "
                            f"pose) vanish in {', '.join(_pose_ref(a, runs, i, n) for i in gone)}: a generated "
                            f"frame dropping them. Draw them on every pose")
                    out.append(_PoseFault(line, a, (runs[i] for i in gone)))
    return out


def gaps(loops, spec):
    """The redrawn style: an outline broken in short stretches. On the figure's edge (a pixel beside air), a run of
    GAP_LEN or fewer coloured (not ink) pixels with edge ink beside it at both ends is a gap. Fault when a loop has
    over GAP_RATE gaps per 100 edge pixels over its poses. A lit outline (selout) colours long stretches of the edge
    on purpose; those are longer than GAP_LEN or have no ink at an end.
    Tried on: the generated wizard idle the user judged (they saw the contour lost in a few px at random on every
    pose, hair, hat and robe alike, and found most of them among the gaps it marks, a few more missed): 8.1 gaps per
    100 edge px, 37-76 a pose, many along the cape's and the staff's edges;
    the two cut-out wizard idles 0; the showcase's beast 1.9, lizard 3.7 (its lit outline), the fighter 2.3, a test
    crab 3.1. 5 lies between: a guess, not a fitted margin."""
    out = []
    for a, frames in loops.items():
        figs, ink = _arrays(frames, spec)
        runs = _same_runs(figs)
        P = [figs[k] for k, _ in runs]
        total = edges = 0
        worst = []
        for i, p in enumerate(P):
            drawn = p > 0
            pad = np.zeros((drawn.shape[0] + 2, drawn.shape[1] + 2), bool)
            pad[1:-1, 1:-1] = drawn
            air = ~pad
            edge = drawn & (air[:-2, 1:-1] | air[2:, 1:-1] | air[1:-1, :-2] | air[1:-1, 2:])
            inked = edge & np.isin(p, list(ink))
            g = 0
            for ys, xs in _blobs(edge & ~inked):
                if len(ys) > GAP_LEN:
                    continue
                near = inked[max(0, ys.min() - 1):ys.max() + 2, max(0, xs.min() - 1):xs.max() + 2]
                ty, tx = np.nonzero(near)
                if len(ty) >= 2 and (np.ptp(ty) + np.ptp(tx)) >= len(ys) + 1:
                    g += 1
            total += g
            edges += int(edge.sum())
            worst.append((g, i))
        rate = 100 * total / max(1, edges)
        if rate > GAP_RATE:
            top = sorted(worst, reverse=True)[:3]
            line = (f"gaps: {a} the outline breaks in short stretches, {rate:.1f} per 100 edge px (most in "
                    f"{', '.join(f'{_pose_ref(a, runs, i, len(frames))} ({g})' for g, i in top)}): coloured "
                    f"pixels of 1-{GAP_LEN} px between ink on the edge. Ink the edge on every pose")
            out.append(_PoseFault(line, a, (runs[i] for _, i in top)))
    return out


def _rgbd(f, spec):
    """A frame as an RGB array and a drawn mask (the shadow and effects left undrawn)."""
    h, w = len(f), len(f[0])
    rgb, drawn = np.zeros((h, w, 3), int), np.zeros((h, w), bool)
    skip = spec.shadow | spec.effects
    for y, r in enumerate(f):
        for x, v in enumerate(r):
            if v is not None and v not in skip:
                rgb[y, x] = spec.rgb(v)
                drawn[y, x] = True
    return rgb, drawn


def _lum3(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _tone_of(c, hue):
    """Is colour c a tone of a patch of this hue: not near-black, saturated (SPOT_SAT, and 30 between its channels),
    its hue within SPOT_HUE of the patch's. The patch's shading and dark shadow tones count; grey, a speck of another
    hue and ink do not."""
    h, _, s = colorsys.rgb_to_hls(*(v / 255 for v in c))
    return (_lum3(c) >= 20 and s >= SPOT_SAT and max(c) - min(c) >= 30
            and min(abs(h - hue), 1 - abs(h - hue)) <= SPOT_HUE)


def _spot_maps(rgb, drawn, hue):
    """For one patch hue: its tone mask, ink (dark, not its tone), lightness, and the air outside the figure (air
    joined to the frame's border: a pinhole inside is not)."""
    H, W = drawn.shape
    tone, ink, L = np.zeros((H, W), bool), np.zeros((H, W), bool), np.zeros((H, W))
    cache = {}
    for y, x in zip(*np.nonzero(drawn)):
        c = tuple(int(v) for v in rgb[y, x])
        if c not in cache:
            t = _tone_of(c, hue)
            cache[c] = (t, _lum3(c) < SPOT_INK and not t, _lum3(c))
        tone[y, x], ink[y, x], L[y, x] = cache[c]
    air = np.zeros((H, W), bool)
    for ys, xs in _comps4(~drawn):
        if ys.min() == 0 or xs.min() == 0 or ys.max() == H - 1 or xs.max() == W - 1:
            air[ys, xs] = True
    return tone, ink, L, air


def _ring(ys, xs, shape):
    own = set(zip(ys.tolist(), xs.tolist()))
    ring = {(y + b, x + a) for y, x in own for b in (-1, 0, 1) for a in (-1, 0, 1)} - own
    return [q for q in ring if 0 <= q[0] < shape[0] and 0 <= q[1] < shape[1]]


def _marks_found(rgb, drawn, hue, kind, drop):
    """The small marks a frame shows on patches of this hue: (row, column) of each. kind "off": a blob of SPOT_PX px
    or fewer of another hue, grey, or a pinhole, with only the patch's tones, ink and outside air round it, half of
    it the patch (a speck on a hat: one that turned grey, or into a hole, still counts). kind "dark" or "light": a
    blob of SPOT_PX px or fewer darker (lighter) than the patch's tones within 2 px by drop or more, three quarters of
    its ring the patch (a mouth line on a face)."""
    tone, ink, L, air = _spot_maps(rgb, drawn, hue)
    if kind == "off":
        cand = ~air & ~tone & ~ink
    else:
        med = np.full(L.shape, np.nan)
        tl = np.where(tone, L, np.nan)
        for y, x in zip(*np.nonzero(drawn)):
            w = tl[max(0, y - 2):y + 3, max(0, x - 2):x + 3]
            if not np.isnan(w).all():
                med[y, x] = np.nanmedian(w)
        with np.errstate(invalid="ignore"):
            cand = drawn & ((L <= med - drop) if kind == "dark" else (L >= med + drop))
    out = []
    for ys, xs in _blobs(cand):
        if len(ys) > (SPOT_PX - 1 if kind == "off" else SPOT_PX):   # a speck of another hue: 2 px at most
            continue
        ring = _ring(ys, xs, drawn.shape)
        n = sum(1 for q in ring if tone[q])
        if kind == "off":
            ok = all(tone[q] or ink[q] or air[q] for q in ring) and n >= len(ring) / 2
        else:
            ok = n >= 0.75 * len(ring)
        if ok:
            out.append((float(ys.mean()), float(xs.mean())))
    return out


def _spot_kind(rgb, drawn, pts):
    """A group's patch hue, read round its marks in the approved drawing (the tones 2 px out), and the marks' kind:
    "off" when a mark is not a tone of the patch (a gold speck on a blue hat), else "dark" or "light" with the
    lightness step from the patch (a mouth on a face)."""
    hs, ls, ms = [], [], []
    for y, x in pts:
        y, x = int(round(y)), int(round(x))
        ms.append(tuple(int(v) for v in rgb[y, x]))
        for b in range(-2, 3):
            for a in range(-2, 3):
                if max(abs(a), abs(b)) == 2 and 0 <= y + b < drawn.shape[0] and 0 <= x + a < drawn.shape[1] \
                        and drawn[y + b, x + a]:
                    c = tuple(int(v) for v in rgb[y + b, x + a])
                    if _lum3(c) >= 20 and max(c) - min(c) >= 30:
                        hs.append(colorsys.rgb_to_hls(*(v / 255 for v in c))[0])
                        ls.append(_lum3(c))
    if not hs:
        return None
    hue = float(np.angle(np.mean(np.exp(2j * np.pi * np.array(hs)))) / (2 * np.pi)) % 1
    if any(not _tone_of(m, hue) for m in ms):
        return hue, "off", 0.0
    step = statistics.median(ls) - statistics.median(_lum3(m) for m in ms)
    return hue, ("dark" if step > 0 else "light"), SPOT_DROP * abs(step)


def _class40(rgb, drawn):
    return np.where(drawn, 1 + (np.array([[_lum3(c) for c in r] for r in rgb]) // 40).astype(int), 0)


def _group_shift(pts, rc, pc, prior):
    """Where a group of marks went in a pose: the shift (within SPOT_REACH of the figure's own) bringing the
    approved drawing's window round the group (SPOT_PAD px out) nearest the pose, read in bands of 40 lightness."""
    ys, xs = [p[0] for p in pts], [p[1] for p in pts]
    y0, x0 = max(0, int(min(ys)) - SPOT_PAD), max(0, int(min(xs)) - SPOT_PAD)
    w = rc[y0:int(max(ys)) + SPOT_PAD + 1, x0:int(max(xs)) + SPOT_PAD + 1]
    H, W = pc.shape
    best = None
    for dy in range(prior[0] - SPOT_REACH, prior[0] + SPOT_REACH + 1):
        for dx in range(prior[1] - SPOT_REACH, prior[1] + SPOT_REACH + 1):
            a, b = y0 + dy, x0 + dx
            if a < 0 or b < 0 or a + w.shape[0] > H or b + w.shape[1] > W:
                continue
            m = int((pc[a:a + w.shape[0], b:b + w.shape[1]] != w).sum())
            key = (m, abs(dy - prior[0]) + abs(dx - prior[1]))
            if best is None or key < best[0]:
                best = (key, (dy, dx))
    return best[1] if best else prior


def _matched(pts, found, shift):
    """How many of a group's marks have a found mark of their own within SPOT_TOL px of their place (each found mark
    answers one), the group moved by the shift or by one px more either way (the most found)."""
    best = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            sy, sx = shift[0] + dy, shift[1] + dx
            near = sorted((abs(fy - y - sy) + abs(fx - x - sx), i, j) for i, (y, x) in enumerate(pts)
                          for j, (fy, fx) in enumerate(found)
                          if abs(fy - y - sy) <= SPOT_TOL and abs(fx - x - sx) <= SPOT_TOL)
            took, used = set(), set()
            for _, i, j in near:
                if i not in took and j not in used:
                    took.add(i)
                    used.add(j)
            best = max(best, len(took))
    return best


def _validate_spot_coordinates(groups, ref):
    w, h = _frame_size(ref)
    for group, coords in groups.items():
        for y, x in coords:
            if not (0 <= y < h and 0 <= x < w and round(y) < h and round(x) < w):
                raise ValueError(f"--spots group {group!r}: ({y:g}, {x:g}) is outside the {w}x{h} reference")


def spots(loops, spec, warns):
    """(with --spots and --ref) Small marks of the approved drawing, placed by eye in groups (a hat's four specks, a
    mouth), looked for in every distinct pose of every loop but an action. The approved drawing must be at the loops'
    scale. For a group: its patch's hue and its marks' kind are read from the drawing (_spot_kind); in a pose, the
    group's window is found again near the figure's own shift (its top row and middle column against the drawing's;
    _group_shift), and its marks are looked for there (_marks_found, _matched). A mark that turned another colour, or
    into a pinhole, still counts: its place is what is asked. Fault when a pose shows fewer of a group's marks than
    the drawing does.
    Tried on: the generated wizard idle the user judged, with the hat's four yellow specks and the mouth placed on
    the approved drawing: the poses it names are exactly those the user saw lose a speck (1, 2, 4, 9, 10, 13, 15; in
    13 two of four left, as they marked) and the mouth (9, 10, 13, 15), 32 judgements of 32. One character, two
    groups: not proven beyond them."""
    out = []
    if not spec.spots or spec.ref is None:
        return out
    _validate_spot_coordinates(spec.spots, spec.ref)
    rr, rd = _rgbd(spec.ref, spec)
    if not rd.any():
        return out
    rc = _class40(rr, rd)
    rys, rxs = np.nonzero(rd)
    groups = {}
    for name, pts in spec.spots.items():
        got = _spot_kind(rr, rd, pts)
        if got is None:
            warns.append(f"warn: spots: group {name!r} has no patch round it in the approved drawing (place its marks "
                         f"on the drawing's own pixels)")
            continue
        hue, kind, drop = got
        n_ref = _matched(pts, _marks_found(rr, rd, hue, kind, drop), (0, 0))
        if n_ref < len(pts):
            warns.append(f"warn: spots: group {name!r}: only {n_ref} of its {len(pts)} marks read as marks in the "
                         f"approved drawing (a mark must be {SPOT_PX} px or fewer, set in its patch): move them onto "
                         f"the marks")
        if n_ref:
            groups[name] = (pts, hue, kind, drop, n_ref)
    for a, frames in loops.items():
        if a in spec.actions:
            continue
        runs = _same_runs(_arrays(frames, spec)[0])
        lost = {name: [] for name in groups}
        for i, (k, _) in enumerate(runs):
            pr, pd = _rgbd(frames[k], spec)
            if not pd.any():
                continue
            ys, xs = np.nonzero(pd)
            prior = (int(ys.min() - rys.min()), int(round(float(np.median(xs) - np.median(rxs)))))
            pc = _class40(pr, pd)
            for name, (pts, hue, kind, drop, n_ref) in groups.items():
                n = _matched(pts, _marks_found(pr, pd, hue, kind, drop), _group_shift(pts, rc, pc, prior))
                if n < n_ref:
                    lost[name].append((i, n))
        for name, where in lost.items():
            if where:
                poses = ', '.join(f"{_pose_ref(a, runs, i, len(frames))} {n}" for i, n in where)
                line = (f"spots: {a} the marks {name!r} ({groups[name][4]} in the approved drawing) are fewer in "
                        f"{poses}: draw every one on every pose, in its place")
                out.append(_PoseFault(line, a, (runs[i] for i, _ in where)))
    return out


def _tops(frames, spec):
    """Per frame the mean top row of the middle third of the figure's columns: the body's height track."""
    tops = []
    for f in frames:
        fig = [[None if v in spec.effects or v in spec.shadow else v for v in r] for r in f]
        xs = [x for r in fig for x, v in enumerate(r) if v is not None]
        if not xs:
            tops.append(None)
            continue
        x0, x1 = min(xs), max(xs)
        cols = range(x0 + (x1 - x0) // 3, x0 + 2 * (x1 - x0) // 3 + 1)
        t = [next((y for y in range(len(fig)) if fig[y][x] is not None), None) for x in cols]
        t = [v for v in t if v is not None]
        tops.append(sum(t) / len(t) if t else None)
    return tops


def stiff(loops, spec):
    """A walker's move: the mean top row of the middle third of the figure, frame by frame. Under STIFF px of rise
    and fall over the loop, the body is a board the legs step under (a gait lifts the body on every step)."""
    if spec.flier or not spec.gait or spec.move not in loops:
        return []
    tops = _tops(loops[spec.move], spec)
    if tops and None not in tops and max(tops) - min(tops) < STIFF:
        return [f"stiff: {spec.move} the body never rises or falls ({max(tops) - min(tops):.1f} px): lift it on "
                f"each step"]
    return []


def _head(frames, spec):
    """The first frame showing the eye, the eye's place on it (_eye_piece: (row, column)) and hr, the half side of
    the head's box round the eye: max(3, round(0.12 * the figure's width)) on that frame. None with no eye."""
    eye = spec.eye
    if eye is None or eye in spec.effects or eye in spec.shadow:
        return None
    f0 = next((f for f in frames if any(eye in r for r in f)), None)
    if f0 is None:
        return None
    skip = spec.shadow | spec.effects
    xs = [x for r in f0 for x, v in enumerate(r) if v is not None and v not in skip]
    return _eye_piece(f0, spec), max(3, round(0.12 * (max(xs) - min(xs))))


def eye_jumps(loops, spec, warns):
    """The eye leaving its head's box in one frame: from one frame to the next (cyclic), the eye's place (followed
    by _eye_piece) moves 2 * hr + 1 px or more along its row or its column, hr being frozen's half side of the head
    box. A fault in the idle and the move; a warning elsewhere, since an attack may carry the head fast. A cell
    mirrored or placed off its anchor does it, and so does an eye lost where its colour shows elsewhere (then the
    track jumps to that other piece, and the plain "no eye" test, which asks only for the colour, does not fire).
    Measured on this repo only (by one person's look; not rerun on the private 39-creature set): the 13 clean loops'
    idles and moves jump 1-2 px a frame against limits of 7 (walker, flier) and 17-19 (showcase); the showcase's
    attacks 3-15 px against 17-19 (they would only warn); a walk frame mirrored 21 px against 7; the broken example
    (a frame knocked 4 px) 4 against 7, so it does not fire there."""
    out = []
    for a, frames in loops.items():
        if a in spec.glows_eye or len(frames) < 2:
            continue
        head = _head(frames, spec)
        if head is None:
            continue
        lim = 2 * head[1] + 1
        tr, n, worst = _eye_track(frames, spec), len(frames), None
        for k in range(n):
            p, q = tr[k], tr[(k + 1) % n]
            if p and q:
                d = max(abs(p[0] - q[0]), abs(p[1] - q[1]))
                if d >= lim and (worst is None or d > worst[0]):
                    worst = (d, k)
        if worst:
            d, k = worst
            line = (f"eye: {a}[{(k + 1) % n}] the eye jumps {d} px in one frame (frame {k}): a cell mirrored or "
                    f"placed off its anchor, or the eye lost and another patch of its colour read for it")
            (out if a in (spec.idle, spec.move) else warns).append(line if a in (spec.idle, spec.move)
                                                                    else "warn: " + line)
    return out


def frozen(loops, spec):
    """The head, a box round the eye reaching 0.12 of the figure's width to each side of it (about a quarter of the
    width across, 3 px each side at least; _head), in the idle and the move: under FROZEN of its pixels ever change,
    it is a mask on a living body, staying put while the body moves. The frames are read as drawn, not with the bob
    aligned away: a head carried whole on the body's rise and fall moves, and at 1-px steps carrying it whole is the
    right way (moved against the body by a pixel, a head that is cut from its neck opens a seam there). Changed from
    the bob-aligned reading on this repo's showcase only (the wolf's idle and walk, head and trunk one piece, were
    judged smooth by one person); not rerun on the private 39-creature set. What this no longer catches: a head that
    never changes within itself but rides the body's bob or breath (the selftest's walker breathing whole, head
    riding). It still catches a head pasted in place while the body moves under it (the selftest's mask, and the
    same in relaxed_bounds). The eye is the piece _eye_piece reads, so its colour used elsewhere on the body does
    not move the box."""
    out = []
    for a in (spec.idle, spec.move):
        if a not in loops or a in spec.glows_eye:
            continue
        fr = loops[a]                                     # as drawn: a head riding the body's bob is alive
        head = _head(fr, spec)
        if head is None:
            continue
        (ey, ex), hr = head
        h, w = len(fr[0]), len(fr[0][0])
        box = [(x, y) for y in range(max(0, int(ey - hr)), min(h, int(ey + hr) + 1))
               for x in range(max(0, int(ex - hr)), min(w, int(ex + hr) + 1))]
        drawn = [(x, y) for x, y in box if any(f[y][x] is not None for f in fr)]
        moved = sum(1 for x, y in drawn if len({f[y][x] for f in fr}) > 1)
        if drawn and moved / len(drawn) < FROZEN:
            out.append(f"frozen: {a} the head hardly moves ({moved} of its {len(drawn)} pixels ever change)")
    return out


# ---- poses, actions and the later checks ------------------------------------------------------------------------
_DIRS = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1)}
_N8 = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]


def parse_action(text, facing="right"):
    """'NAME[:KIND[:DIR]]' -> (NAME, (KIND, DIR)). KIND: strike (its anticipation, strike and recovery are judged),
    jump (it leaves the ground on purpose: ground is not asked), or any other word (a gesture: a breath, a spit, a
    bell). DIR: right, left, up or down; a strike's defaults to the facing, any other kind's to up. Every declared
    action may hold up to two keys, each up to ACTION_KEY frames, outside choppy and uneven. ValueError on a bad
    form."""
    name, _, rest = text.partition(":")
    kind, _, d = rest.partition(":")
    kind = kind or "other"
    d = d or (facing if kind == "strike" else "up")
    if not name or d not in _DIRS or ":" in d:
        raise ValueError(f"--action takes NAME[:KIND[:right|left|up|down]], not {text!r}")
    return name, (kind, d)


def _eq(p, q):
    return np.array_equal(p, q) if isinstance(p, np.ndarray) else p == q


def _same_runs(frames):
    """Cyclic runs of identical frames: [(first frame, length)], starting at a change; [(0, n)] when all alike."""
    n = len(frames)
    eq = [_eq(frames[k], frames[k - 1]) for k in range(n)]
    if all(eq):
        return [(0, n)]
    s, out = eq.index(False), []
    for j in range(n):
        k = (s + j) % n
        if j and eq[k]:
            out[-1][1] += 1
        else:
            out.append([k, 1])
    return [tuple(r) for r in out]


def _seq_poses(frames):
    """An action's poses in order from frame 0: [(first frame, hold)]; a last run repeating frame 0's pose across
    the loop's seam is merged into the first."""
    out = []
    for k, f in enumerate(frames):
        if out and _eq(f, frames[out[-1][0]]):
            out[-1][1] += 1
        else:
            out.append([k, 1])
    if len(out) > 1 and _eq(frames[out[-1][0]], frames[0]):
        out[0][1] += out.pop()[1]
    return [tuple(r) for r in out]


def _key_mask(a, keys, colours):
    codes = [keys[c] for c in colours if c in keys]
    return np.isin(a, codes) if codes else np.zeros(a.shape, bool)


def _box(a):
    """(top, bottom, left, right, area) of an array's drawn cells; None when nothing is drawn."""
    ys, xs = np.nonzero(a)
    if not len(ys):
        return None
    return int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max()), int(len(ys))


def _spectrum(x):
    v = np.asarray(x, float)
    return np.abs(np.fft.rfft(v - v.mean()))[1:]          # [0] is one wave a loop, [1] two, ...


def _dom(x):
    """The dominant number of waves a loop in a track (0 when it is flat)."""
    s = _spectrum(x)
    return int(np.argmax(s)) + 1 if len(s) and s.max() > 1e-9 else 0


def _lag(a, b):
    """How many frames track b trails track a: the cyclic cross-correlation's peak, the smallest shift on a tie."""
    a = np.asarray(a, float) - np.mean(a)
    b = np.asarray(b, float) - np.mean(b)
    n, best = len(a), None
    for L in sorted(range(-(n // 2), n // 2 + 1), key=abs):
        c = float((a * np.roll(b, -L)).sum())
        if best is None or c > best[0] + 1e-9:
            best = (c, L)
    return best[1]


def _filled(m):
    """A silhouette with its holes filled: every cell not reached from the frame's border through air."""
    air = ~m
    reach = np.zeros_like(m)
    reach[0, :] |= air[0, :]
    reach[-1, :] |= air[-1, :]
    reach[:, 0] |= air[:, 0]
    reach[:, -1] |= air[:, -1]
    while True:
        nxt = (reach | _sh(reach, 1) | _sh(reach, -1) | _sh(reach, 0, 1) | _sh(reach, 0, -1)) & air
        if (nxt == reach).all():
            return ~reach
        reach = nxt


def _sil(frame, spec):
    """The filled silhouette of a frame, effects included (a breath or a spit changes it), the shadow left out."""
    return _filled(np.array([[v is not None and v not in spec.shadow for v in r] for r in frame]))


def _iou(p, q):
    u = int((p | q).sum())
    return int((p & q).sum()) / u if u else 1.0


def _action_poses(frames, spec):
    """An action's distinct poses from frame 0, the creature alone: (runs, arrays, steps), steps[i] the change from
    pose i to the next as a share of the figure (a 1-px bob forgiven), the last step returning to pose 0."""
    figs, _ = _arrays(frames, spec)
    runs = _seq_poses(figs)
    P = [figs[k] for k, _ in runs]
    area, m = max(1.0, _area(figs)), len(runs)
    return runs, P, [_chg(P[i], P[(i + 1) % m]) / area for i in range(m)]


def _lead(a, d):
    b = _box(a)
    return 0 if b is None else {"right": b[3], "left": -b[2], "up": -b[0], "down": b[1]}[d]


def _eye_at(frame, spec):
    if spec.eye is None:
        return None
    c = _eye_piece(frame, spec)
    return (c[1], c[0]) if c else None


def _strike(frames, spec, d):
    """A strike's phases (G3). S: the biggest step carrying the leading edge (d) forward; E: its end (a second
    forward step over half of it: a middle frame skipped). ant: the steps before it; rec: the steps after it, back to
    pose 0. back: how far the eye or the leading edge first moves against d (negative: backward), in px."""
    runs, P, steps = _action_poses(frames, spec)
    m = len(P)
    if m < 3:
        return None
    lead = [_lead(p, d) for p in P]
    fwd = [lead[(i + 1) % m] - lead[i] for i in range(m)]
    cand = [i for i in range(m - 1) if fwd[i] > 0] or list(range(m - 1))
    S = max(cand, key=lambda i: steps[i])
    E = S + 1 if S + 1 < m - 1 and fwd[S + 1] > 0 and steps[S + 1] > SETTLE * steps[S] else S
    dx, dy = _DIRS[d]
    back = [lead[i] - lead[0] for i in range(1, S + 1)]
    eyes = [_eye_at(frames[runs[i][0]], spec) for i in range(S + 1)]
    if S and all(eyes):
        back += [(e[0] - eyes[0][0]) * dx + (e[1] - eyes[0][1]) * dy for e in eyes[1:]]
    return dict(runs=runs, steps=steps, S=S, E=E, peak=max(steps[S:E + 1]), ant=[s for s in steps[:S] if s > 0],
                rec=[s for s in steps[E + 1:] if s > 0], back=min(back) if back else 0.0)


def _settle(rec, peak):
    """What is wrong with a return to rest (shared by recover after a strike and after a jump's landing): under two
    steps, or a step over SETTLE of the peak. None when it eases back."""
    if len(rec) < 2:
        return f"returns to rest in {len(rec)} step{'' if len(rec) == 1 else 's'}"
    if max(rec) > SETTLE * peak:
        return f"a step back of {max(rec):.0%} of the figure against the peak's {peak:.0%}"
    return None


def _path(frames, spec, st, d, labels=None):
    """The leading part's place on each pose from pose 0 to the strike's contact: the eye's centroid, or with a part
    strip the tip of the part travelling farthest along d (the mean of its pixels at its extreme)."""
    idx = [st["runs"][i][0] for i in range(min(st["E"] + 2, len(st["runs"])))]
    eyes = [_eye_at(frames[k], spec) for k in idx]
    if all(eyes):
        return eyes
    if not labels:
        return None
    keys = {}
    arrs, _ = _arrays([labels[k] for k in idx], Spec(ink=set()), keys)
    dx, dy = _DIRS[d]
    best = None
    for code in keys.values():
        tips, proj = [], []
        for x in arrs:
            ys, xs = np.nonzero(x == code)
            if not len(ys):
                break
            p = xs * dx + ys * dy
            sel = p == p.max()
            tips.append((float(xs[sel].mean()), float(ys[sel].mean())))
            proj.append(int(p.max()))
        else:
            if best is None or max(proj) - min(proj) > best[0]:
                best = (max(proj) - min(proj), tips)
    return best[1] if best else None


def _piston(pts):
    """(the path's largest distance from the chord between its two farthest points, that chord's length)."""
    if not pts or len(pts) < 3:
        return None
    i, j = max(((i, j) for i in range(len(pts)) for j in range(i + 1, len(pts))),
               key=lambda t: math.dist(pts[t[0]], pts[t[1]]))
    (ax, ay), (bx, by) = pts[i], pts[j]
    span = math.dist(pts[i], pts[j])
    if not span:
        return None
    return max(abs((px - ax) * (by - ay) - (py - ay) * (bx - ax)) / span for px, py in pts), span


def action(loops, spec, warns):
    """G3, G9, G14, G15: the loops declared with --action. Warnings only, until fitted on accepted actions.
    A strike (KIND strike) is read on its distinct poses from frame 0:
      strike   the strike step (the biggest step carrying the leading edge forward, a second forward step over half
               of it joined) is at least STRIKE_SNAP times the anticipation's median step;
      counter  some pose before it moves the eye or the leading edge 1 px or more against the strike first;
      recover  after it, 2+ steps back to rest, none over SETTLE of the strike (shared with a jump's landing);
      stage    the contact pose's filled silhouette (effects in) against the rest pose's: IoU under STAGE_IOU;
      piston   the eye (or, with --parts, the farthest-travelling part's tip) from the rest pose to the contact: a
               path of 3+ poses spanning PISTON_SPAN+ px that strays under PISTON_DEV px from its chord.
    An action whose figure's bottom row rises 2+ px (any kind, not a flier) is read as a jump:
      gravity  airborne steps (px a frame, from pose to pose) shrinking toward the apex and growing on the fall;
      squash   a pose whose height changes SQUASH_H or more changes its width the other way and keeps its area within
               SQUASH_AREA; on the ground a deformation lasts SQUASH_POSES poses at most;
      recover  after the landing, as above, against the loop's biggest step."""
    for a, (kind, d) in spec.actions.items():
        frames = loops.get(a)
        if not frames or len(frames) < 4:
            continue
        st = _strike(frames, spec, d) if kind == "strike" else None
        if st:
            k = st["runs"][st["S"]][0]
            med = statistics.median(st["ant"]) if st["ant"] else 0.0
            if not st["ant"] or st["back"] > -1:
                warns.append(f"warn: counter: {a} nothing moves back against the strike first (frame {k}; the eye "
                             f"or leading edge goes {st['back']:+.1f} px): wind up 1 px or more the other way over "
                             f"2-5 small poses; a still anticipation has no force")
            if st["ant"] and st["peak"] < STRIKE_SNAP * med:
                warns.append(f"warn: strike: {a} the strike (frame {k}) changes {st['peak']:.0%} of the figure, "
                             f"under {STRIKE_SNAP:g} times the anticipation's median step ({med:.0%}): strike in "
                             f"1-2 frames, the biggest step of the action, after small eased ones")
            why = _settle(st["rec"], st["peak"])
            if why:
                warns.append(f"warn: recover: {a} after the strike it {why}: follow through, then come back over "
                             f"2-5 poses, steps growing then shrinking, none over half the strike")
            runs = st["runs"]
            contact = runs[(st["E"] + 1) % len(runs)][0]
            iou = _iou(_sil(frames[contact], spec), _sil(frames[0], spec))
            if iou >= STAGE_IOU:
                warns.append(f"warn: stage: {a} the contact pose (frame {contact}) keeps {iou:.0%} of the rest "
                             f"pose's silhouette: push the key (a longer reach, a lower crouch) until the shape "
                             f"itself changes")
            pi = _piston(_path(frames, spec, st, d, spec.parts.get(a)))
            if pi and pi[1] >= PISTON_SPAN and pi[0] < PISTON_DEV:
                warns.append(f"warn: piston: {a} the leading part slides on a straight line to the strike (strays "
                             f"{pi[0]:.1f} px from a {pi[1]:.0f}-px chord): move it on an arc (the head rises, then "
                             f"drops into the bite; a tip sweeps round its joint)")
        if not spec.flier:
            warns += _airborne(a, frames, spec)
    return []


def _airborne(a, frames, spec):
    """The jump half of action (G9); [] when the figure's bottom never rises 2 px."""
    runs, P, steps = _action_poses(frames, spec)
    m, B = len(P), [_box(p) for p in P]
    if m < 4 or any(b is None for b in B):
        return []
    bots = [b[1] for b in B]
    G, out = max(bots), []
    if G - min(bots) < 2:
        return []
    apex = bots.index(min(bots))
    v = [(bots[(i + 1) % m] - bots[i]) / runs[i][1] for i in range(m)]
    land = next((i for i in range(apex + 1, m) if bots[i] == G), None)
    rise = [-v[i] for i in range(apex) if bots[i] < G and v[i] < 0]
    fall = [v[i] for i in range(apex, land if land is not None else m) if v[i] > 0]
    if len(rise) >= 2 and rise[-1] > rise[0]:
        out.append(f"warn: gravity: {a} it rises faster toward the apex ({rise[0]:.1f} then {rise[-1]:.1f} px a "
                   f"frame): steps shrink on the way up, two drawings near the apex or the apex held")
    elif len(fall) >= 2 and fall[-1] <= fall[0]:
        out.append(f"warn: gravity: {a} it falls at an even pace ({', '.join(f'{x:.1f}' for x in fall)} px a "
                   f"frame): the steps grow on the fall")
    t0, b0, l0, r0, A0 = B[0]
    h0, w0, bad, run = b0 - t0 + 1, r0 - l0 + 1, None, 0
    for i, (t, b, l, r, A) in enumerate(B):
        h, w = b - t + 1, r - l + 1
        bent = abs(h - h0) >= SQUASH_H * h0
        run = run + 1 if bent and b == G else 0
        if bad is None and bent and ((h < h0 and w < w0) or (h > h0 and w > w0)):
            bad = (i, f"{'narrows as it squashes' if h < h0 else 'widens as it stretches'} (height {h} against "
                      f"{h0}, width {w} against {w0})")
        elif bad is None and bent and abs(A - A0) > SQUASH_AREA * A0:
            bad = (i, f"changes its mass {A / A0 - 1:+.0%} as it deforms")
        elif bad is None and run > SQUASH_POSES:
            bad = (i, f"stays deformed on the ground {run} poses")
    if bad:
        out.append(f"warn: squash: {a} frame {runs[bad[0]][0]} {bad[1]}: squash wider, stretch narrower, keep "
                   f"the area within {SQUASH_AREA:.0%}, at most {SQUASH_POSES} poses")
    if land is not None:
        why = _settle([s for s in steps[land:] if s > 0], max(steps))
        if why:
            out.append(f"warn: recover: {a} after landing (frame {runs[land][0]}) it {why}: overshoot 1-2 px or "
                       f"ease back in shrinking steps, then hold")
    return out


def _edge_band(m):
    """Cells within 1 px of the silhouette's edge (figure cells with air beside them, dilated 1)."""
    return _dilate(m & _dilate(~m, 1), 1)


def seam(loops, spec, warns):
    """The loop's seam: a first pose repeated at the end doubles its hold where the loop closes. The loop's distinct
    poses (_same_runs, cyclic, starting at a change); when every run that does not cross the seam (start + length
    within the loop) has one length h, and the run crossing it is longer than h, warn. A loop whose holds differ is
    not judged: an idle's rest may fall on the seam. Measured on this repo only (by one person's look; not rerun on
    the private 39-creature set): none of the 13 clean loops fires (the showcase holds every pose 2 frames and no
    run crosses its seam; the clean flier's idle has a 4-frame run across its seam, but holds of 1-4, so it is not
    judged); a walk with its first frame copied to its end gives a crossing run of 2 against 1, on twos 4 against 2.
    A warning only."""
    for a, frames in loops.items():
        n = len(frames)
        runs = _same_runs(frames)
        inner = [ln for k0, ln in runs if k0 + ln <= n]
        cross = [ln for k0, ln in runs if k0 + ln > n]
        if len(inner) >= 3 and cross and len(set(inner)) == 1 and cross[0] > inner[0]:
            warns.append(f"warn: seam: {a} the pose at the seam (frame 0) is held {cross[0]} frames against "
                         f"{inner[0]} for every other: the first pose is repeated at the end; drop the last frame")


def _boil(figs):
    """Per distinct-pose step (cyclic): is it boil (G4)? A boil step (a) changes cells at least BOIL_EDGE inside the
    1-px edge band of the poses on both sides, (b) changes under BOIL_SMALL of the median of the other steps, and
    (c) is reverted: at least BOIL_BACK of its changed cells take their old colour again one or two poses later
    (A, B, A). A sub-pixel lead is small and edge-only too, but it settles into the move and never reverts."""
    runs = _same_runs(figs)
    P = [figs[k] for k, _ in runs]
    m = len(P)
    if m < 3:
        return runs, [False] * m
    ch = [P[i] != P[(i + 1) % m] for i in range(m)]
    cnt = [int(c.sum()) for c in ch]
    cand = []
    for i in range(m):
        if not cnt[i]:
            cand.append(False)
            continue
        band = _edge_band(P[i] > 0) | _edge_band(P[(i + 1) % m] > 0)
        edge = int((ch[i] & band).sum()) / cnt[i]
        back = max(int(((P[j] == P[i]) & ch[i]).sum()) / cnt[i] for j in {(i + 2) % m, (i + 3) % m} - {i})
        cand.append(edge >= BOIL_EDGE and back >= BOIL_BACK)
    others = [cnt[i] for i in range(m) if cnt[i] and not cand[i]]
    if not others:
        return runs, [False] * m
    med = statistics.median(others)
    return runs, [cand[i] and cnt[i] < BOIL_SMALL * med for i in range(m)]


def boil(loops, spec, warns):
    """G4: steps that change only the outline and come back (AI and sheet frames redraw every edge) are not poses.
    They inflate the update rate choppy reads: a sheet of 5 real poses a second with a boil frame between reads as
    10. Warn when 2+ steps boil and they are a quarter of the updates or more, or when the real-pose rate falls under
    CHOPPY_RATE while the counted rate does not. choppy's own count is unchanged until this is fitted."""
    for a, frames in loops.items():
        n = len(frames)
        if n < 4:
            continue
        runs, flags = _boil(_arrays(frames, spec)[0])
        b, m = sum(flags), len(runs)
        rate, real = m * spec.fps / n, (m - b) * spec.fps / n
        if m >= 3 and b >= 2 and (b >= m / 4 or real < CHOPPY_RATE <= rate):
            first = runs[flags.index(True)][0]
            warns.append(f"warn: boil: {a} {b} of its {m} updates change only the outline and come back (first after "
                         f"frame {first}; real poses {real:.1f}/s of {rate:.1f}/s): a frame that changes only the "
                         f"outline is not a pose; drop it, or thin a generated clip evenly")
    return []


def _contacts(row):
    """Runs of drawn cells in a row: [(x0, x1)]."""
    out, x0 = [], None
    for x, v in enumerate(list(row) + [False]):
        if v and x0 is None:
            x0 = x
        elif not v and x0 is not None:
            out.append((x0, x - 1))
            x0 = None
    return out


def _skate(frames, spec):
    """Planted feet of an in-place walk (G2), on distinct poses: the runs of drawn cells on the loop's lowest row,
    matched one to one with the next pose's by overlap. A match is skipped when either pose holds another contact
    within SKATE_NEAR px of it: feet merged on the ground row that split apart (one going back, one forward), or
    two that merge, cannot be told apart from one foot sliding. Returns (slides: [(pose run, px forward)], chains: per foot
    the rigid steps it takes while planted, back: px moved backward, frames: the frames those steps take)."""
    figs, _ = _arrays(frames, spec)
    runs = _same_runs(figs)
    P = [figs[k] for k, _ in runs]
    m = len(P)
    G = max(int(np.nonzero(f.any(1))[0].max()) for f in figs if f.any())
    fwd = -1 if spec.facing == "left" else 1
    C = [_contacts(p[G] > 0) for p in P]
    slides, link, chains, back, nfr = [], {}, [], 0, 0
    for i in range(m):
        A, B = C[i], C[(i + 1) % m]
        for ai, (a0, a1) in enumerate(A):
            hit = [bi for bi, (b0, b1) in enumerate(B) if b0 <= a1 + 1 and b1 >= a0 - 1]
            if len(hit) != 1:
                continue
            b0, b1 = B[hit[0]]
            if sum(1 for c0, c1 in A if b0 <= c1 + 1 and b1 >= c0 - 1) != 1:
                continue
            if (sum(1 for c0, c1 in B if c0 <= a1 + SKATE_NEAR and c1 >= a0 - SKATE_NEAR) != 1
                    or sum(1 for c0, c1 in A if b0 <= c1 + SKATE_NEAR and b1 >= c0 - SKATE_NEAR) != 1):
                continue                                  # a split or a merge of feet beside it: unsure which foot
            d0, d1 = (b0 - a0) * fwd, (b1 - a1) * fwd
            if d0 >= 1 and d1 >= 1:
                slides.append((runs[(i + 1) % m], min(d0, d1)))
            if d0 == d1:
                back -= d0
                nfr += runs[i][1]
                if i < m - 1:                              # chains do not wrap round the loop's seam
                    cid = link.get((i, ai))
                    if cid is None:
                        cid = len(chains)
                        chains.append([])
                    chains[cid].append(d0)
                    link[(i + 1, hit[0])] = cid
    return slides, chains, back, nfr


def skate(loops, spec, warns):
    """G2: a planted foot stays on one world pixel until it lifts. Drawn walking in place over a scrolling road,
    every planted foot moves back the same amount each pose and never forward. Warn when a planted contact slides
    forward 1 px or more, or when one foot's steps while planted differ by more than SKATE_SWING px (1 px of
    rounding and 1 of jitter allowed). Warnings only: on small quadrupeds near and far feet merge on the ground row;
    judge per foot with a part strip. A legged walker's move only."""
    if spec.flier or not spec.gait or spec.move not in loops or len(loops[spec.move]) < 4:
        return []
    slides, chains, _, _ = _skate(loops[spec.move], spec)
    a = spec.move
    if slides:
        (k0, ln), d = slides[0]
        where = f"frame {k0}" if ln == 1 else f"frames {k0}-{(k0 + ln - 1) % len(loops[a])}"
        warns.append(f"warn: skate: {a} a planted foot slides {d} px forward ({where}; {len(slides)} slide(s)): a "
                     f"planted foot stays on its world pixel; drawn in place it goes back the same amount each pose")
    for ch in chains:
        if len(ch) >= 2 and max(ch) - min(ch) > SKATE_SWING:
            warns.append(f"warn: skate: {a} a planted foot's steps swing {ch} px a pose: move it back by the same "
                         f"amount each pose (the road's speed)")
            break
    return []


def gait(loops, spec, warns):
    """G5: a legged walker's body bobs twice a loop (one bob a step), and a two-step loop has an even number of
    poses. Warn when the body-top track (stiff's) has a clear dominant wave count other than two (every other wave
    count under GAIT_CLEAR of it), or when the move has an odd number of distinct poses. A flat track is stiff's;
    a track with no clear wave count (a redrawn sheet's top row shifting a pixel at uneven times, a many-legged
    crawler) has no rhythm to judge."""
    if spec.flier or not spec.gait or spec.move not in loops or len(loops[spec.move]) < 4:
        return []
    a, frames = spec.move, loops[spec.move]
    tops = _tops(frames, spec)
    if None not in tops and max(tops) - min(tops) >= STIFF:
        k, s = _dom(tops), _spectrum(tops)
        if k != 2 and max((v for i, v in enumerate(s) if i != k - 1), default=0.0) < GAIT_CLEAR * s[k - 1]:
            warns.append(f"warn: gait: {a} the body bobs {k} time(s) a loop: a two-step walk rises and sinks twice, "
                         f"once a step")
    poses = len(_same_runs(frames))
    if poses > 1 and poses % 2:
        warns.append(f"warn: gait: {a} has {poses} poses, an odd number: the two steps cannot mirror each other")
    return []


def _part_tracks(labels):
    """{part colour: [(area, cx, cy, top, bottom) or None, per frame]} from a loop's part strip."""
    keys = {}
    arrs, _ = _arrays(labels, Spec(ink=set()), keys)
    out = {}
    for c, code in keys.items():
        tr = []
        for x in arrs:
            ys, xs = np.nonzero(x == code)
            tr.append((len(ys), float(xs.mean()), float(ys.mean()), int(ys.min()), int(ys.max())) if len(ys) else None)
        out[c] = tr
    return out


def _part_lags(labels):
    """(body colour, {part colour: frames it trails the body}) over the parts that ride the body: off the ground row,
    moving 0.75 px or more, with the body's dominant wave count. None when the body does not move up and down."""
    T = _part_tracks(labels)
    if not T:
        return None
    body = max(T, key=lambda c: sum(t[0] for t in T[c] if t))
    if not all(T[body]):
        return None
    by = [t[2] for t in T[body]]
    if max(by) - min(by) < 0.5:
        return None
    G, kb, lags = max(t[4] for tr in T.values() for t in tr if t), _dom(by), {}
    for c, tr in T.items():
        if c == body or not all(tr) or any(t[4] == G for t in tr):
            continue
        cy = [t[2] for t in tr]
        if max(cy) - min(cy) >= 0.75 and _dom(cy) == kb:
            lags[c] = _lag(by, cy)
    return body, lags


def parts(loops, spec, warns):
    """G6, G7: with a part strip (--parts; each rig part one flat colour, frame for frame with the loop).
    volume  a part of VOLUME_MIN+ px whose area leaves its median by over max(VOLUME, VOLUME_PX) (parts in --squash,
            such as wings, left out);
    lag     in the idle and the move, the parts riding the body (off the ground, with its wave count) all move on
            the body's own frame (no follow-through) while the body steps 1.5 px or more in a frame, or one trails it
            by over a quarter of the loop. At 1-px steps a part joined to the body by a seam (a neck, a tail's root)
            rides it: a pixel's lag opens the seam, so the follow-through goes to a free tip, too small to move a
            part's centre. The step limit was added on this repo's showcase only (the wolf, judged smooth by one
            person); not rerun on the private 39-creature set. What it no longer catches: a walk or idle bobbing 1
            px whose parts all move on the body's frame (relaxed_bounds: no warning); at 2 px it still warns."""
    for a, labels in spec.parts.items():
        if a not in loops or len(labels) != len(loops[a]):
            continue
        n = len(labels)
        for c, tr in _part_tracks(labels).items():
            if c in spec.squash:
                continue
            areas = [t[0] if t else 0 for t in tr]
            med = statistics.median(areas)
            if med < VOLUME_MIN:
                continue
            k = max(range(n), key=lambda i: abs(areas[i] - med))
            if abs(areas[k] - med) > max(VOLUME * med, VOLUME_PX):
                warns.append(f"warn: volume: {a}[{k}] part {c} has {areas[k]} px against its usual {med:g}: keep each "
                             f"part's volume (declare a part squashed or foreshortened on purpose with --squash)")
        if a not in (spec.idle, spec.move):
            continue
        got = _part_lags(labels)
        if not got or not got[1]:
            continue
        lags = got[1]
        body = _part_tracks(labels)[got[0]]
        steps = [abs(body[k][2] - body[k - 1][2]) for k in range(n)]
        if all(v == 0 for v in lags.values()) and max(steps) >= 1.5:   # 1-px steps: riding the body is right
            warns.append(f"warn: lag: {a} every part riding the body moves on its frame ({', '.join(map(str, lags))}): let the "
                         f"head, ears or tail follow a pose late (one pose is enough at sprite scale)")
        elif any(abs(v) > n / 4 for v in lags.values()):
            c = max(lags, key=lambda x: abs(lags[x]))
            warns.append(f"warn: lag: {a} part {c} trails the body by {lags[c]} frames, over a quarter of the loop")
    return []


def palette(loops, spec):
    """G11 (with --palette only): every frame keeps the approved drawing's colours; --effects, --shadow, --glow and
    the eye are allowed besides. A new colour that stays a few frames (a stray resample, a per-cell quantise) is
    what shimmer misses."""
    if spec.palette is None:
        return []
    ok = spec.palette | spec.effects | spec.shadow | spec.glow | {spec.eye}
    out = []
    for a, frames in loops.items():
        bad = {}
        for k, f in enumerate(frames):
            for r in f:
                for v in r:
                    if v is not None and v not in ok and v not in bad:
                        bad[v] = k
        if bad:
            cs = sorted(bad, key=bad.get)
            out.append(f"palette: {a}[{bad[cs[0]]}] holds {len(cs)} colour(s) outside the palette "
                       f"({', '.join(map(str, cs[:5]))}): snap every frame to the approved drawing's colours (one "
                       f"palette for the whole sheet); declare glow steps with --glow")
    return out


def _rare(frames, spec):
    """{colour: [frames]} for the colours shown in under a quarter of a loop's frames (the eye, --glow, --effects and
    --shadow left out)."""
    seen = {}
    for k, f in enumerate(frames):
        for c in {v for r in f for v in r if v is not None}:
            seen.setdefault(c, []).append(k)
    skip = spec.effects | spec.shadow | spec.glow | {spec.eye}
    return {c: ks for c, ks in seen.items() if len(ks) < len(frames) / 4 and c not in skip}


def blend(loops, spec, warns):
    """G11, loops in --sheet only: a rare colour (in under a quarter of the frames) whose lightness lies between two
    colours it touches is a blend: a per-cell quantise or a resample. A rig that turns parts a fraction makes such
    in-between tones on purpose (an accepted set of rigged creatures held up to 69 in one loop), so rigged loops
    get the rare colours read-out only. A colour in --palette, --glow or the eye is not reported."""
    for a, frames in loops.items():
        if a not in spec.sheets or len(frames) < 4:
            continue
        hits = []
        for c, ks in _rare(frames, spec).items():
            if spec.palette is not None and c in spec.palette:
                continue
            L = spec.lum(c)
            for k in ks:
                f, h, w = frames[k], len(frames[k]), len(frames[k][0])
                if any(min(n) < L < max(n) for n in (
                        [spec.lum(f[y + b][x + d]) for d, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                         if 0 <= x + d < w and 0 <= y + b < h and f[y + b][x + d] not in (None, c)]
                        for y in range(h) for x in range(w) if f[y][x] == c) if n):
                    hits.append((c, ks))
                    break
        if hits:
            warns.append(f"warn: blend: {a} {len(hits)} rare colour(s) lie between the tones round them "
                         f"({', '.join(f'{c} in frames {ks[:4]}' for c, ks in hits[:3])}): a resample or a per-frame "
                         f"quantise; snap to the drawing's ramp, or declare a glow step with --glow")
    return []


def _orphan_mask(a, skip):
    """Drawn cells whose colour matches none of their 8 neighbours (skip's cells left out)."""
    same = np.zeros(a.shape, bool)
    for dy, dx in _N8:
        same |= _sh(a, dy, dx) == a
    return (a > 0) & ~same & ~skip


def orphans(loops, spec, warns):
    """G12. orphans: a frame holding more lone pixels (a colour matching none of the 8 round it; the eye and --glow
    left out) than ORPHAN_X times the loop's usual count (its median, or the --ref drawing's if that is higher) plus
    ORPHAN_PX. speck: a pixel steady in every bob-aligned frame that takes another colour for 1-2 frames once a loop,
    a lone pixel there, while its 8 neighbours keep theirs (no motion passes), and SPECK_DL or more of lightness away
    from its own colour and from every neighbour, and lighter or darker than all of them (a glaring speck, not a
    resampled tone: a tone between its neighbours', such as one between the outline and the fill beside it, reads
    as the edge blending while a part shifts): a blinking speck.
    Both compare the loop with itself: a shrunk texture holds many lone pixels on purpose. Fitted on an accepted set
    of 29 textured creatures: their worst frames held up to 1.75 times their loop's usual count, and the specks left
    by a rig's resampling sit within 60 of a neighbour's lightness or among moving neighbours."""
    skip = {spec.eye} | spec.glow
    for a, frames in loops.items():
        n = len(frames)
        if n < 4:
            continue
        keys = {}
        src = ([spec.ref] if spec.ref is not None else []) + list(frames)
        arrs, _ = _arrays(src, spec, keys)
        cnt = [int(_orphan_mask(x, _key_mask(x, keys, skip)).sum()) for x in arrs]
        own = cnt[1:] if spec.ref is not None else cnt
        base = max(statistics.median(own), cnt[0] if spec.ref is not None else 0)
        k = max(range(n), key=own.__getitem__)
        if own[k] > ORPHAN_X * base + ORPHAN_PX:
            warns.append(f"warn: orphans: {a}[{k}] holds {own[k]} lone pixels against the loop's usual {base:g}: "
                         f"clean the stray pixels a resample or a redraw left")
        keys = {}
        A = np.stack(_arrays(_aligned(frames), spec, keys)[0])
        inv = {v: c for c, v in keys.items()}
        sk = {keys[c] for c in skip if c in keys}
        om = [_orphan_mask(A[k], np.isin(A[k], list(sk))) for k in range(n)]
        h, w = A.shape[1:]
        for y, x in zip(*np.nonzero((A > 0).all(0))):
            seq = A[:, y, x]
            vals, num = np.unique(seq, return_counts=True)
            base_v = vals[int(np.argmax(num))]
            off = [k for k in range(n) if seq[k] != base_v]
            if not 1 <= len(off) <= 2 or (len(off) == 2 and (off[1] - off[0]) % n not in (1, n - 1)):
                continue
            if base_v in sk or any(seq[k] in sk for k in off) or not all(om[k][y, x] for k in off):
                continue
            ring = [(y + dy, x + dx) for dy, dx in _N8 if 0 <= y + dy < h and 0 <= x + dx < w]
            before = (off[0] - 1) % n
            if any(A[k][q] != A[before][q] for k in off for q in ring):
                continue                                  # something moves past it: a resample, not a speck
            L = spec.lum(inv[int(seq[off[0]])])
            near = [spec.lum(inv[int(A[off[0]][q])]) for q in ring if A[off[0]][q]] + [spec.lum(inv[int(base_v)])]
            if min(abs(L - v) for v in near) < SPECK_DL or min(near) < L < max(near):
                continue                                  # close to a neighbour, or a blend between two
            warns.append(f"warn: speck: {a}[{off[0]}] the pixel at ({x}, {y}) takes a lone colour for {len(off)} "
                         f"frame(s) once a loop: a blinking speck")
            break
    return []


def _doubles(a, ink):
    """Outline ink cells beside air with 3+ ink cells among their 8 neighbours (a 2x2 block, an L-clump)."""
    k = np.isin(a, list(ink)) if ink else np.zeros(a.shape, bool)
    air = a == 0
    near = _sh(air, 1) | _sh(air, -1) | _sh(air, 0, 1) | _sh(air, 0, -1)
    nb = sum(_sh(k, dy, dx).astype(int) for dy, dx in _N8)
    return k & near & (nb >= 3)


def doubles(loops, spec, warns):
    """G18: a frame whose outer outline holds more doubled cells (2x2 blocks, L-clumps) than DOUBLES_X times the
    loop's usual count (its median) plus DOUBLES: an outline thickened by the shrink, or a part turned and re-inked.
    Compared with the loop itself, since some drawings ink thick on purpose. A warning only, with a margin: a leg or
    a wing turning at a joint makes and removes L-corners on purpose (on an accepted set of 29 creatures the worst
    frame held up to 1.7 times its loop's usual count)."""
    for a, frames in loops.items():
        if len(frames) < 2:
            continue
        arrs, ink = _arrays(frames, spec)
        d = [_doubles(x, ink) for x in arrs]
        usual = statistics.median(int(x.sum()) for x in d)
        k = max(range(len(d)), key=lambda i: int(d[i].sum()))
        if int(d[k].sum()) > DOUBLES_X * usual + DOUBLES:
            ys, xs = np.nonzero(d[k] & ~_dilate(d[0], 1))
            where = ", ".join(f"({x}, {y})" for y, x in list(zip(ys, xs))[:3])
            warns.append(f"warn: doubles: {a}[{k}] holds {int(d[k].sum())} doubled outline pixels against the loop's "
                         f"usual {usual:g} (new against frame 0 at {where or 'the same places'}): thin the outline "
                         f"to one pixel after the shrink")
    return []


def drift(loops, spec, warns):
    """G23 (with --ref): the idle's pose nearest the approved drawing, after the best shift (feet and centre
    aligned, then +-3 px), still differs on over REF_DRIFT of the drawing: the rest render drifted from it (a part
    cut, a pivot off, a colour snapped differently). The margin is to fit."""
    if spec.ref is None or spec.idle not in loops:
        return []
    frames = loops[spec.idle]
    keys = {}
    arrs, _ = _arrays([spec.ref] + [frames[k] for k, _ in _same_runs(frames)], spec, keys)
    ref, R = arrs[0], 3
    rb = _box(ref)
    if rb is None:
        return []
    hr, wr = ref.shape
    best = None
    for p in arrs[1:]:
        pb = _box(p)
        if pb is None:
            continue
        h, w = p.shape
        H, W = h + 2 * (hr + R), w + 2 * (wr + R)
        canvas = np.zeros((H, W), p.dtype)
        canvas[hr + R:hr + R + h, wr + R:wr + R + w] = p
        oy0 = hr + R + pb[1] - rb[1]
        ox0 = wr + R + round((pb[2] + pb[3]) / 2 - (rb[2] + rb[3]) / 2)
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                oy, ox = oy0 + dy, ox0 + dx
                if oy < 0 or ox < 0 or oy + hr > H or ox + wr > W:
                    continue
                r = np.zeros_like(canvas)
                r[oy:oy + hr, ox:ox + wr] = ref
                mis = int(((canvas != r) & ((canvas > 0) | (r > 0))).sum())
                best = mis if best is None else min(best, mis)
    if best is not None and best > REF_DRIFT * rb[4]:
        warns.append(f"warn: drift: {spec.idle} its nearest pose differs from the approved drawing on {best} px "
                     f"({best / rb[4]:.1%}) after the best shift: the rest render drifted from the drawing (a part "
                     f"cut, a pivot off, a colour snapped differently)")
    return []


def marks(loops, spec, warns, empty_frames=None):
    """The missed defining feature (with --mark): a small high-contrast mark (a gem, a lamp, a lone bright pixel) is
    where the eye goes, and too small for vanish. On every frame each --mark colour must show, and its centroid,
    rounded, must not move 2+ px between consecutive frames (held frames included). Faults in the idle and the
    move; warnings in other loops (an action may turn it away or swing it fast). Skip frames already reported as
    empty and only judge jumps in complete loops."""
    out = []
    for c in spec.marks:
        for a, frames in loops.items():
            missing = (empty_frames or {}).get(a, ())
            lines, pos = [], []
            for k, f in enumerate(frames):
                if k in missing:
                    continue
                pts = [(x, y) for y, r in enumerate(f) for x, v in enumerate(r) if v == c]
                if not pts:
                    lines.append(f"mark: {a}[{k}] has no mark {c}: a defining mark must never vanish")
                    pos = None
                    break
                pos.append((math.floor(sum(p[0] for p in pts) / len(pts) + 0.5),
                            math.floor(sum(p[1] for p in pts) / len(pts) + 0.5)))
            n = len(frames)
            for k in range(n if pos and n > 1 and not missing else 0):
                (x0, y0), (x1, y1) = pos[k], pos[(k + 1) % n]
                if max(abs(x1 - x0), abs(y1 - y0)) >= 2:
                    lines.append(f"mark: {a}[{(k + 1) % n}] the mark {c} jumps {max(abs(x1 - x0), abs(y1 - y0))} px "
                                 f"in one frame (frame {k}): move it with its part, a pixel at a time")
                    break
            if a in (spec.idle, spec.move):
                out += lines
            else:
                warns += ["warn: " + x for x in lines]
    return out


def swap(loops, spec, warns):
    """The missed part continuity (loops in --sheet): a colour group (one colour, the eye and --glow left out, its
    median count VANISH_MIN+ px) whose count on the distinct poses falls under SWAP_LOW of its median, or rises over
    SWAP_HIGH times it, in one step from a usual count (within SWAP_BACK), for 1 to SWAP_POSES poses, and comes back
    in one step: a part switched off or on, as an AI sheet drops a shield for a cell. A wing foreshortening passes
    through the counts between, so it is not caught. A warning only."""
    for a in spec.sheets:
        frames = loops.get(a)
        if not frames or len(frames) < 4:
            continue
        keys = {}
        arrs, _ = _arrays(frames, spec, keys)
        runs = _same_runs(arrs)
        P, m = [arrs[k] for k, _ in runs], len(runs)
        if m < 4:
            continue
        skip = {keys[c] for c in {spec.eye} | spec.glow if c in keys}
        for c, code in keys.items():
            if code in skip:
                continue
            cnt = [int((p == code).sum()) for p in P]
            med = statistics.median(cnt)
            if med < VANISH_MIN:
                continue
            hit = None
            for i in range(m):
                for low in (True, False):
                    odd = (lambda v: v < SWAP_LOW * med) if low else (lambda v: v > SWAP_HIGH * med)
                    usual = (lambda v: v >= SWAP_BACK * med) if low else (lambda v: v <= med / SWAP_BACK)
                    if not (odd(cnt[i]) and usual(cnt[i - 1])):
                        continue
                    L = 1
                    while L <= SWAP_POSES and odd(cnt[(i + L) % m]):
                        L += 1
                    if L <= SWAP_POSES and usual(cnt[(i + L) % m]):
                        hit = (i, L, low)
                        break
                if hit:
                    break
            if hit:
                i, L, low = hit
                warns.append(f"warn: swap: {a} colour {c} {'drops to' if low else 'jumps to'} {cnt[i]} px (usually "
                             f"{med:g}) for {L} pose(s) from frame {runs[i][0]}: a part switched "
                             f"{'off' if low else 'on'} for a cell; keep every part on every cell")
                break
    return []


def _lines(a):
    """Per column of an array the first drawn row (the topline) and the belly: the last row of the drawn run that
    starts at the topline, None where that run reaches the figure's lowest rows (a leg, or the ground). None for an
    empty column."""
    h, w = a.shape
    m = a > 0
    rows = np.nonzero(m.any(1))[0]
    bottom = int(rows.max()) if len(rows) else -1
    top, belly = [None] * w, [None] * w
    for x in range(w):
        ys = np.nonzero(m[:, x])[0]
        if not len(ys):
            continue
        y = top[x] = int(ys[0])
        while y + 1 < h and m[y + 1, x]:
            y += 1
        if y < bottom - 1:
            belly[x] = y
    return top, belly


def _torso(rest, eye, facing):
    """The torso of the rest frame: (its columns, (top row, bottom row) of the body band), or None. The band is the
    run of rows drawn on SPLIT_ROWS of the fullest row's pixels, holding it (legs and the tail's tip are thinner).
    Its columns are those drawn on SPLIT_COLS of the band's rows and on every row of its middle half (a tail or a leg
    leaves that open), whose topline lies in the band's top quarter (no neck, head, ears or raised tail above them),
    the head's side of a line 1.5 head boxes (frozen's) behind the eye left out (a head and neck may turn against
    the body); the longest run of them, SPLIT_MIN columns at least."""
    m = rest > 0
    cnt = m.sum(1)
    if not cnt.max():
        return None
    ok = cnt >= SPLIT_ROWS * cnt.max()
    y0 = y1 = int(cnt.argmax())
    while y0 > 0 and ok[y0 - 1]:
        y0 -= 1
    while y1 < len(ok) - 1 and ok[y1 + 1]:
        y1 += 1
    top, _ = _lines(rest)
    c0, c1 = y0 + (y1 - y0 + 1) // 4, y1 - (y1 - y0 + 1) // 4   # the band's core: a tail or a leg leaves it open
    xs = np.nonzero(m.any(0))[0]
    hr = max(3, round(0.12 * (xs.max() - xs.min())))     # frozen's head box (half its side)
    best, run = [], []
    for x in range(m.shape[1] + 1):
        good = (x < m.shape[1] and m[y0:y1 + 1, x].mean() >= SPLIT_COLS and m[c0:c1 + 1, x].all()
                and top[x] is not None and top[x] >= y0 - max(2, (y1 - y0 + 1) // 4))
        if good and eye is not None:                      # the neck's root too: half a head box further back
            good = x < eye[0] - 1.5 * hr if facing != "left" else x > eye[0] + 1.5 * hr
        if good:
            run.append(x)
        else:
            best, run = (run if len(run) > len(best) else best), []
    return (best, (y0, y1)) if len(best) >= SPLIT_MIN else None


def _torso_dx(a, R, X, band, reach=8):
    """The sideways shift that best lays frame a's torso block (the band's rows, 3 px either side, over the torso's
    columns) on the rest frame's, up to 3 px up or down allowed; the smallest on a tie (a walk in place gives 0)."""
    h = R.shape[0]
    ya, yb, xa, xb = max(0, band[0] - 3), min(h, band[1] + 4), X[0], X[-1] + 1
    ref, best = R[ya:yb, xa:xb], None
    for dx in range(-reach, reach + 1):
        for dy in range(-3, 4):
            s = _sh(a, -dy, -dx)[ya:yb, xa:xb]
            key = (int(((s != ref) & ((s > 0) | (ref > 0))).sum()), abs(dx), abs(dy))
            if best is None or key < best[0]:
                best = (key, dx)
    return best[1]


def _seams(d, X, need, rest_line):
    """The band seams in one pose change: d maps each torso column (rest coordinates) to how far the line moved
    there. A seam is a column c where d changes by 1 px (a joint bent further is no band), with need+ columns moving
    alike on each side of it (each side
    rigid), where the rest line is level (c-1 and c on one row: the step is one the drawing does not have). A
    staircase of 3+ levels, each a 1-px step the same way, is a shear spread over the length: no seam.
    Returns [(c, d behind, d from c on, behind's columns, from c's columns)]."""
    runs = []                                             # (first column, last column, d) of consecutive columns
    for x in X:
        if d.get(x) is None:
            continue
        if runs and runs[-1][1] == x - 1 and runs[-1][2] == d[x]:
            runs[-1][1] = x
        else:
            runs.append([x, x, d[x]])
    big = [r for r in runs if r[1] - r[0] + 1 >= 3]
    lv = [r[2] for r in big]
    if len(set(lv)) >= 3 and all(abs(q - p) == 1 for p, q in zip(lv, lv[1:])) and \
            len({q - p for p, q in zip(lv, lv[1:]) if q != p}) == 1:
        return []
    out = []
    for p, q in zip(runs, runs[1:]):
        c = q[0]
        if (p[1] == c - 1 and abs(q[2] - p[2]) == 1 and p[1] - p[0] + 1 >= need and q[1] - q[0] + 1 >= need
                and rest_line[c] is not None and rest_line[c] == rest_line[c - 1]):
            out.append((c, p[2], q[2], range(p[0], p[1] + 1), range(q[0], q[1] + 1)))
    return out


def _rigid(p, q, cols, dxp, dxq, dy, rows):
    """Whether the block of pose p over cols (rest coordinates) moved dy rows is pose q's block there: under
    SPLIT_BLOCK of their drawn pixels differ (a wing or a leg sweeping through does not move as a block)."""
    h, w = p.shape
    xs = [x for x in cols if 0 <= x + dxp < w and 0 <= x + dxq < w]
    if not xs:
        return False
    a = _sh(p, dy)[rows][:, [x + dxp for x in xs]]
    b = q[rows][:, [x + dxq for x in xs]]
    drawn = int(((a > 0) | (b > 0)).sum())
    return drawn > 0 and int(((a != b) & ((a > 0) | (b > 0))).sum()) <= SPLIT_BLOCK * drawn


def split(loops, spec, warns):
    """The torso cut into bands. The rest frame (--ref, else the idle's first frame) gives the torso (_torso): the
    body band's rows and the columns whose topline is the torso's own. In every loop, each change from one distinct
    pose to the next, both laid on the rest frame by their torso block (_torso_dx), is read along the topline and the
    belly line: per torso column, how far the line moved. Warn when one column parts two sides that each move
    rigidly over 30 % of the torso (SPLIT_RUN) by different amounts, with a 1-px step where the rest line is
    level (_seams): the rear band riding the hips and the front band the shoulders, one a pose after the other.
    A whole-body bob moves every column alike; a shear spread over the length is a staircase; a head turning
    against the body lies outside the torso's columns; legs and a tail are thinner than the band. A flier is not
    read: its back carries its wings. A warning only."""
    if not loops or spec.flier:
        return []
    src = spec.ref if spec.ref is not None else (loops.get(spec.idle) or loops[min(loops)])[0]
    keys = {}
    R = _arrays([src], spec, keys)[0][0]
    if not R.any():
        return []
    got = _torso(R, _eye_at(src, spec), spec.facing)
    if not got:
        return []
    X, band = got
    rt, rb = _lines(R)
    need_t = max(4, round(SPLIT_RUN * len(X)))
    need_b = max(4, round(SPLIT_RUN * sum(1 for x in X if rb[x] is not None)))
    w = R.shape[1]
    mid = (band[0] + band[1]) // 2                        # the block whose line it is: the back down to the band's
    blocks = (slice(max(0, min(rt[x] for x in X) - 2), mid + 1),   # middle, or the middle down to the belly
              slice(mid, max([rb[x] for x in X if rb[x] is not None], default=band[1]) + 3))
    for a, frames in loops.items():
        figs, _ = _arrays(frames, spec, keys)
        if figs[0].shape != R.shape:
            continue
        runs = _same_runs(figs)
        if len(runs) < 2:
            continue
        P = [figs[k] for k, _ in runs]
        L = [_lines(p) for p in P]
        dx = [_torso_dx(p, R, X, band) for p in P]
        hits = []
        for i in range(len(P)):
            j = (i + 1) % len(P)
            for name, line, need, rl in (("topline", 0, need_t, rt), ("belly line", 1, need_b, rb)):
                lp = {x: L[i][line][x + dx[i]] for x in X if 0 <= x + dx[i] < w}
                lq = {x: L[j][line][x + dx[j]] for x in X if 0 <= x + dx[j] < w}
                d = {x: lq[x] - lp[x] for x in X if lp.get(x) is not None and lq.get(x) is not None}
                hits += [(runs[i][0], runs[j][0], name, c, d0, d1) for c, d0, d1, back, front
                         in _seams(d, X, need, rl) if _rigid(P[i], P[j], back, dx[i], dx[j], d0, blocks[line])
                         and _rigid(P[i], P[j], front, dx[i], dx[j], d1, blocks[line])]
        if hits:
            f0, f1, name, c, d0, d1 = hits[0]
            where = ", ".join(f"{a}[{p}]->[{q}] col {c}" for p, q, _, c, _, _ in hits[:4])
            warns.append(f"warn: split: {a} {len(hits)} pose change(s) move the torso's two sides by different "
                         f"amounts with a 1-px step its drawing does not have (first {a}[{f0}]->{a}[{f1}], the "
                         f"{name} at column {c}: {d0:+d} px behind it, {d1:+d} px from it on; {where}): the torso "
                         f"is one piece: bend it over its whole length (a shear or a curve), turn it whole about a "
                         f"pivot, or let a 1-px step fall where the line already slopes")
    return []


def _eye_track(frames, spec):
    """The eye's (row, column) per frame, as _eye_rows follows it; None on a frame with no eye."""
    out, last = [], None
    for f in frames:
        c = _eye_piece(f, spec, last)
        if c is None:
            out.append(None)
            continue
        last = c
        out.append((math.floor(c[0] + 0.5), math.floor(c[1] + 0.5)))
    return out


def _hitches(figs, track, region, need, n):
    """The lone steps of one feature: [(frame, hold, step, change round it, change elsewhere)]. track holds the
    feature's place per frame; region(k, dy, dx) its pixels at frame k and moved by the step. A step counts when the
    place held need+ frames before it, it does not come back within 3 frames (tick's), it changes HITCH_MIN+ px
    round the feature, mostly as the feature moved whole (the frame moved by the step explains all but HITCH_RIGID
    of that change), and the rest of the figure changes under HITCH_ELSE of it."""
    out = []
    for k in range(n):
        q = (k + 1) % n
        if track[q] == track[k]:
            continue
        hold = 1
        while hold < n and track[(k - hold) % n] == track[k]:
            hold += 1
        if hold < need or any(track[(q + j) % n] == track[k] for j in range(1, 4)):
            continue
        dy, dx = track[q][0] - track[k][0], track[q][1] - track[k][1]
        box = region(k, dy, dx)
        ch = figs[k] != figs[q]
        near = int((ch & box).sum())
        rest = int((ch & ~_dilate(box, 2)).sum())
        whole = int(((_sh(figs[k], dy, dx) != figs[q]) & box).sum())
        if near >= HITCH_MIN and whole <= HITCH_RIGID * near and rest <= HITCH_ELSE * near:
            out.append((k, hold, (dy, dx), near, rest))
    return out


def hitch(loops, spec, warns):
    """A big feature stepping alone after a long hold. The eye's track (the head's place), and with --parts each
    part of VOLUME_MIN+ px (its box's corner), per frame. Warn when it holds HITCH_HOLD+ frames (at 30 fps; 0.27 s),
    then steps a pixel or more as one block while little else in the figure changes on that frame (_hitches): the
    step reads as a jerk, not motion. A step back within 3 frames is tick's; a declared action's held key (its
    longest pose hold) may end in a step. A warning only."""
    need = max(2, round(HITCH_HOLD * spec.fps / 30))
    for a, frames in loops.items():
        n = len(frames)
        if n < need + 2:
            continue
        figs, _ = _arrays(frames, spec)
        if not all(f.any() for f in figs):
            continue
        key = None
        if a in spec.actions:
            r = max(_same_runs(figs), key=lambda t: t[1])
            key = {(r[0] + j) % n for j in range(r[1])}
        h, w = figs[0].shape
        found = []
        if spec.eye is not None and a not in spec.glows_eye:
            tr = _eye_track(frames, spec)
            if all(tr) and len(set(tr)) > 1:
                xs = np.nonzero(np.any([f > 0 for f in figs], 0).any(0))[0]
                hr = max(3, round(0.12 * (xs.max() - xs.min())))

                def eye_box(k, dy, dx, tr=tr, hr=hr):
                    b = np.zeros((h, w), bool)
                    ey, ex = tr[k]
                    b[max(0, ey - hr):ey + hr + 1, max(0, ex - hr):ex + hr + 1] = True
                    return b | _sh(b, dy, dx)
                found += [("the head (the eye's track)",) + t for t in _hitches(figs, tr, eye_box, need, n)]
        labels = spec.parts.get(a)
        if labels and len(labels) == n:
            keys = {}
            lab, _ = _arrays(labels, Spec(ink=set()), keys)
            for c, code in keys.items():
                masks = [x == code for x in lab]
                if statistics.median(int(m.sum()) for m in masks) < VOLUME_MIN or not all(m.any() for m in masks):
                    continue
                tr = [(int(np.nonzero(m.any(1))[0][0]), int(np.nonzero(m.any(0))[0][0])) for m in masks]

                def part_box(k, dy, dx, masks=masks):
                    return masks[k] | _sh(masks[k], dy, dx)
                found += [(f"part {c}",) + t for t in _hitches(figs, tr, part_box, need, n)]
        by = {}
        for what, k, hold, (dy, dx), near, rest in found:
            if not (key and key <= {(k - j) % n for j in range(hold)}):
                by.setdefault(what, []).append((k, hold, max(abs(dy), abs(dx)), near, rest))
        for what, hits in by.items():
            k, hold, px, near, rest = max(hits, key=lambda t: t[1])
            at = ", ".join(f"{a}[{t[0]}] after {t[1]}" for t in sorted(hits)[:6])
            warns.append(f"warn: hitch: {a} {what} steps {px} px alone after holding still {hold} frames "
                         f"({hold / spec.fps:.2f} s; the rest of the figure changes {rest} px against its {near}) "
                         f"{len(hits)} time(s) a loop ({at}; frame k is the change to the next): it reads as a jerk; "
                         f"move it with the body on a pose the body moves on (head, neck and trunk together), "
                         f"or move other parts on the same pose")
    return []


def readouts(loops, spec):
    """The later checks' numbers, printed after the tracks (what to read before trusting a warning): per loop the
    update rate against the real-pose rate (boil), the box's height, width and anchor, the rare colours; for the move
    the bob, the leg band and the planted feet's speed; the eye's lag behind the figure's top; per declared action
    its phases and staging; with a part strip each part's area and lag; the move's closing step (last frame to
    first, a 1-px bob forgiven) against its median moving step. That ratio is a read-out, not a warning: the clean
    moves here give 0.78-1.32, a 16-frame walk cut at 13 frames 1.64 and at 11 frames 2.11, too narrow a margin."""
    lines = []
    for a, frames in loops.items():
        n = len(frames)
        figs, _ = _arrays(frames, spec)
        if not all(x.any() for x in figs):
            continue
        if n >= 4:
            runs, flags = _boil(figs)
            changes = len(runs) if len(runs) > 1 else 0
            lines.append(f"{a}: {len(runs)} poses: updates {changes * spec.fps / n:.1f}/s, real poses "
                         f"{(changes - sum(flags)) * spec.fps / n:.1f}/s")
        B = [b for b in (_box(f) for f in figs) if b]
        if B:
            hs, ws = [b[1] - b[0] + 1 for b in B], [b[3] - b[2] + 1 for b in B]
            cx = [(b[2] + b[3]) / 2 for b in B]
            lines.append(f"{a}: box height {min(hs)}-{max(hs)}, width {min(ws)}-{max(ws)}, bottom rows "
                         f"{min(b[1] for b in B)}-{max(b[1] for b in B)}, centre x {min(cx):g}-{max(cx):g}")
        rare = _rare(frames, spec) if n >= 4 else {}
        if rare:
            lines.append(f"{a}: rare colours " + ", ".join(f"{c} ({len(k)} frames)" for c, k in list(rare.items())[:6]))
        if spec.eye is not None and a in (spec.idle, spec.move) and a not in spec.glows_eye and n >= 4:
            ys = _eye_rows(frames, spec)
            if ys and len(set(ys)) > 1:
                tops = [b[0] for b in (_box(f) for f in figs)]
                lines.append(f"{a}: the eye trails the figure's top by {_lag(tops, ys)} frame(s) (a readout)")
        if a == spec.move and n >= 4:                     # the seam: the step that closes the loop
            fg = [[[None if v in spec.effects else v for v in r] for r in f] for f in frames]
            st = [_change(fg[k], fg[(k + 1) % n]) for k in range(n)]
            mv = [s for s in st if s]
            if mv:
                lines.append(f"{a}: the closing step (frame {n - 1} to 0) is {st[-1] / statistics.median(mv):.2f} "
                             f"times the median moving step (clean walks and beats 0.78-1.32; a read-out)")
        tops = _tops(frames, spec) if a == spec.move and not spec.flier and spec.gait and n >= 4 else []
        if tops and None not in tops:
            u = np.any([f > 0 for f in figs], 0)
            rows = np.nonzero(u.any(1))[0]
            H = int(rows.max() - rows.min() + 1)
            band = range(int(rows.max()) - H // 3 + 1, int(rows.max()) + 1)
            widths = []
            for f in figs:
                xs = np.nonzero(f[band.start:band.stop].any(0))[0]
                widths.append(int(xs.max() - xs.min() + 1) if len(xs) else 0)
            _, _, back, nfr = _skate(frames, spec)
            lines.append(f"{a}: bob {max(tops) - min(tops):.1f} px ({(max(tops) - min(tops)) / H:.0%} of the height), "
                         f"{_dom(tops)} wave(s) a loop; legs widest at frame {widths.index(max(widths))}, narrowest at "
                         f"{widths.index(min(widths))}; body lowest at frame {tops.index(max(tops))}, highest at "
                         f"{tops.index(min(tops))}")
            if nfr:
                lines.append(f"{a}: planted feet go back {back / nfr:.2f} px a frame"
                             + (f" (the road scrolls {spec.speed:g})" if spec.speed is not None else ""))
        act = spec.actions.get(a)
        if act and n >= 4:
            st = _strike(frames, spec, act[1]) if act[0] == "strike" else None
            if st:
                med = statistics.median(st["ant"]) if st["ant"] else 0
                lines.append(f"{a}: strike at frame {st['runs'][st['S']][0]}: {st['peak']:.0%} of the figure against "
                             f"the anticipation's median {med:.0%} ({len(st['ant'])} steps, back {st['back']:+.1f} "
                             f"px); recovery steps {[round(s * 100) for s in st['rec']]} %")
            s0 = _sil(frames[0], spec)
            iou = [_iou(_sil(frames[k], spec), s0) for k, _ in _seq_poses(frames)]
            lines.append(f"{a}: the most changed pose keeps {min(iou):.0%} of the rest silhouette (stage)")
        if a in spec.parts and len(spec.parts[a]) == n:
            T = _part_tracks(spec.parts[a])
            got = _part_lags(spec.parts[a]) if n >= 4 else None
            lags = got[1] if got else {}
            lines.append(f"{a}: parts " + "; ".join(
                f"{c} area {min(t[0] if t else 0 for t in tr)}-{max(t[0] for t in tr if t)}"
                + (f" lag {lags[c]}" if c in lags else "") for c, tr in T.items() if any(tr)))
    return lines


# ---- pictures --------------------------------------------------------------------------------------------------
def _img(f, rgb, Z, bg=(74, 66, 84)):
    im = Image.new("RGB", (len(f[0]), len(f)), bg)
    for y, r in enumerate(f):
        for x, v in enumerate(r):
            if v is not None:
                im.putpixel((x, y), rgb(v))
    return im.resize((im.width * Z, im.height * Z), Image.NEAREST)


def fault_frames(lines, loops):
    """{loop: {frame indices}} named in fault lines: "loop[k]", "loop[k0-k1]" (a held pose, every frame of it; k1
    may wrap past the loop's end: "move[15-0]") and "loop ... (frame k)". Frame indices are 0-based; a jump's or a
    snap's "frame k" is the change from frame k to the next, so both frames are named."""
    out = {}
    if not loops:
        return out
    names = "|".join(re.escape(a) for a in sorted(loops, key=len, reverse=True))
    starts = re.compile(rf"^\s*(?:warn: )?\w+: ({names})(?=\[|\s|$)")
    refs = re.compile(rf"(?<!\w)({names})\[(\d+)(?:-(\d+))?\]")
    spot_group = re.compile(r""" the marks (?:'[^'\\]*(?:\\.[^'\\]*)*'|"[^"\\]*(?:\\.[^"\\]*)*")(?= \(\d+ in )""")
    for line in lines:
        if isinstance(line, _PoseFault):
            n = len(loops.get(line.loop, ()))
            if n:
                out.setdefault(line.loop, set()).update((k + i) % n for k, hold in line.runs for i in range(hold))
            continue
        m = starts.match(line)
        text = line
        if m and line.lstrip().startswith("spots:"):
            group = spot_group.match(line, m.end())
            if group:
                text = line[group.end():]                # a quoted group name can itself contain frame syntax
        for name, first, last in refs.findall(text):
            k, k1, n = int(first), int(last or first), len(loops[name])
            if k < n and k1 < n:
                out.setdefault(name, set()).update((k + i) % n for i in range((k1 - k) % n + 1))
        if m:
            a = m[1]
            ks, n = out.setdefault(a, set()), len(loops[a])
            # A loop's own name can contain "frame 12": read "frame k" only outside the name and its "loop[k]" refs.
            tail = refs.sub(" ", line[m.end():] if text is line else text)
            for k in map(int, re.findall(r"\bframe (\d+)", tail)):
                if k < n:
                    ks.add(k)
                    if line.lstrip().startswith(("jump:", "snap:")):
                        ks.add((k + 1) % n)
    return out


def _preview_font():
    for family in ("segoeui.ttf", "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(family, 12)
        except OSError:
            pass
    return ImageFont.load_default()


def _preview_size(width, height, frames=1):
    if max(width, height) > MAX_PREVIEW_SIDE or width * height * frames > MAX_PREVIEW_PIXELS:
        raise ValueError(f"preview needs {width}x{height} pixels over {frames} image(s); use --no-preview "
                         f"or reduce the input (limit {MAX_PREVIEW_PIXELS:,} pixels, {MAX_PREVIEW_SIDE:,} per side)")


def sheet(loops, path, rgb=hexrgb, Z=6, faults=None):
    """Every loop's distinct poses (at most 12, spread over the loop, plus any a fault names), each labelled with the
    frames it holds (0-based: "4-7" is one pose held over frames 4 to 7), and under each the pixels changed from the
    pose just before it (shown or not), in red.
    faults: fault lines (check's result); the tiles of the frames they name are outlined in red."""
    marked = fault_frames(faults or [], loops)
    rows, width, height = [], 0, 0
    gap, head = 8, 28
    for a, frames in loops.items():
        keys = []                                         # [first frame, last frame, the pose]
        for k, f in enumerate(frames):
            if keys and f == keys[-1][2]:
                keys[-1][1] = k
            else:
                keys.append([k, k, f])
        hit = [any(k0 <= m <= k1 for m in marked.get(a, ())) for k0, k1, _ in keys]
        if len(keys) > 12:
            pick = {round(i * (len(keys) - 1) / 11) for i in range(12)} | {i for i, h in enumerate(hit) if h}
            keep = sorted(pick)
        else:
            keep = list(range(len(keys)))
        tile_width = sum(len(keys[i][2][0]) * Z + gap for i in keep) + gap
        width = max(width, tile_width)
        height += 2 * len(keys[0][2]) * Z + head + 10
        rows.append((a, keys, hit, keep))
    _preview_size(width, height)
    out = Image.new("RGB", (width, height), (16, 13, 20))
    d, y0 = ImageDraw.Draw(out), 0
    font = _preview_font()
    for a, keys, hit, keep in rows:
        try:
            d.text((4, y0 + 2), a, fill=(240, 230, 200), font=font)
        except UnicodeEncodeError:                       # legacy Pillow bitmap when no system font is available
            d.text((4, y0 + 2), a.encode("ascii", "backslashreplace").decode("ascii"),
                   fill=(240, 230, 200), font=font)
        x0 = gap // 2
        for i in keep:
            k0, k1, f = keys[i]
            before = keys[i - 1][2]                         # the pose just before it, shown or not
            diff = Image.new("RGB", (len(f[0]), len(f)), (30, 26, 34))
            for y, r in enumerate(f):
                for x, v in enumerate(r):
                    if v != before[y][x]:
                        diff.putpixel((x, y), (230, 60, 60))
                    elif v is not None:
                        diff.putpixel((x, y), (90, 84, 100))
            top = _img(f, rgb, Z)
            label = str(k0) if k0 == k1 else f"{k0}-{k1}"
            d.text((x0, y0 + 15), label, fill=(255, 120, 120) if hit[i] else (170, 160, 150))
            out.paste(top, (x0, y0 + head))
            out.paste(diff.resize(top.size, Image.NEAREST), (x0, y0 + head + 2 + top.height))
            if hit[i]:
                d.rectangle((x0 - 3, y0 + head - 3, x0 + top.width + 2, y0 + head + 4 + 2 * top.height),
                            outline=(255, 70, 70), width=2)
            x0 += top.width + gap
        y0 += 2 * len(keys[0][2]) * Z + head + 10
    out.save(path)


def _preview_span(loops, move, speed):
    """Close every visible cycle when possible within twice the usual preview length."""
    periods = [len(frames) for frames in loops.values()]
    usual = 2 * max(periods)
    if move in loops and speed:
        periods.append((Fraction(str(speed)) / 6).denominator)    # the road repeats every six pixels
    common = 1
    for period in periods:
        common = common // math.gcd(common, period) * period
        if common > 2 * usual:                            # coprime loop lengths can otherwise require hours of frames
            return usual, False
    return max(1, usual // common) * common, True


def gif(loops, path, rgb=hexrgb, fps=30, Z=5, speed=None, move=None, facing="right"):
    """The loops side by side at fps. With speed (the road's scroll, game px a frame), a dashed ground line scrolls
    under the move loop, so a planted foot that slides against the road shows (G2)."""
    names = list(loops)
    W, H = len(loops[names[0]][0][0]), len(loops[names[0]][0])
    n, repeat = _preview_span(loops, move, speed)
    if not math.isfinite(fps) or fps <= 0 or n / fps > MAX_CLIP_SECONDS:
        raise ValueError(f"GIF preview exceeds {MAX_CLIP_SECONDS} seconds at {fps:g} fps; use --no-preview")
    count = min(n, max(1, math.floor(n * 100 / fps + 0.5)))
    _preview_size(len(names) * (W + 6) * Z, (H + 4) * Z, count)
    frames, durations = [], []
    elapsed_cs = 0
    for t in range(n):
        # GIF stores centiseconds. Snap the boundaries so rounding cannot accumulate across the loop.
        end_cs = math.floor((t + 1) * 100 / fps + 0.5)
        if t == n - 1:
            end_cs = max(1, end_cs)                       # even a sub-centisecond clip needs a visible frame
        if end_cs == elapsed_cs:
            continue
        durations.append(10 * (end_cs - elapsed_cs))
        elapsed_cs = end_cs
        im = Image.new("RGB", (len(names) * (W + 6), H + 4), (74, 66, 84))
        for i, a in enumerate(names):
            im.paste(_img(loops[a][t % len(loops[a])], rgb, 1), (i * (W + 6) + 3, 2))
            if speed is not None and a == move:
                off = math.floor(t * speed + 0.5) * (1 if facing != "left" else -1)
                for x in range(W):
                    if (x + off) // 3 % 2 == 0:
                        im.putpixel((i * (W + 6) + 3 + x, H + 2), (170, 160, 140))
        frames.append(im.resize((im.width * Z, im.height * Z), Image.NEAREST))
    playback = {"loop": 0} if repeat else {}
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, **playback)


def tracks(loops, spec):
    """What to read before the GIF (the workflow's look at the motion): per loop, the eye's row runs (level, frames)
    and the per-step change list (pixels changed from frame k to k+1, a 1-px bob forgiven, as a share of the
    figure). A 2-3-frame excursion of the eye, or a long run of zeros followed by a big step, shows here first."""
    lines = []
    for a, frames in loops.items():
        figs, _ = _arrays(frames, spec)
        n, area = len(figs), max(1.0, _area(figs))
        steps = [_chg(figs[k], figs[(k + 1) % n]) / area for k in range(n)]
        lines.append(f"{a}: steps " + " ".join(f"{s * 100:.0f}" for s in steps) + " (% of the figure)")
        if spec.eye is not None and a not in spec.glows_eye:
            ys = _eye_rows(frames, spec)
            if ys:
                lines.append(f"{a}: eye rows {[tuple(r) for r in _runs(ys)] or [(ys[0], n)]}")
    return lines + readouts(loops, spec)


# ---- loading ---------------------------------------------------------------------------------------------------
def _grid(im, key=None):
    """An image as rows of "#rrggbb" or None (air): a pixel under half alpha is air, and so is one of the key colour
    (a "#rrggbb", or None for none). Only that exact colour: a key's anti-aliased fringe stays and must be cleaned
    before."""
    im = im.convert("RGBA")
    out = []
    for y in range(im.height):
        row = []
        for x in range(im.width):
            p = im.getpixel((x, y))
            v = "#%02x%02x%02x" % p[:3]
            row.append(v if p[3] >= 128 and v != key else None)
        out.append(row)
    return out


def hexcol(v):
    """A colour option normalised to the loaded pixels' key: '#rrggbb', lower case ('FFCC33' and '#ffcc33' alike).
    ValueError when it is not six hex digits."""
    t = v.strip().lower()
    t = t if t.startswith("#") else "#" + t
    if len(t) != 7 or any(c not in "0123456789abcdef" for c in t[1:]):
        raise ValueError(f"not a colour (#rrggbb): {v!r}")
    return t


def load(src, frame=None, frames=None, fps=None, key=None):
    """Frames from a strip PNG, a folder of PNGs, or a GIF. A strip is cut by frame (one frame's width) or frames (how
    many it holds); with neither its frames are square (as wide as the strip is tall). ValueError when the strip's
    width is not a whole number of frames: a wrong cut would be checked as a broken animation. A folder is read in
    file-name order (zero-pad the numbers: f00.png, f01.png, ...). For a GIF, round cumulative presentation times
    to game-frame boundaries. Without fps or a stored duration, count one game frame per image. key, a "#rrggbb",
    reads that exact colour as air (a strip with a flat background instead of transparency)."""
    return _load(src, frame, frames, fps, key, _InputBudget())


class _InputBudget:
    def __init__(self):
        self.frames = self.pixels = 0

    def add(self, width, height, count=1):
        self.frames += count
        self.pixels += width * height * count
        if self.frames > MAX_INPUT_FRAMES or self.pixels > MAX_INPUT_PIXELS:
            raise ValueError(f"input exceeds {MAX_INPUT_FRAMES:,} frames or {MAX_INPUT_PIXELS:,} frame-pixels")


def _png_paths(folder):
    return [os.path.join(folder, n) for n in sorted(os.listdir(folder)) if n.lower().endswith(".png")
            and os.path.isfile(os.path.join(folder, n))]


def _image_grid(src, key, budget):
    try:
        with Image.open(src) as im:
            budget.add(*im.size)
            return _grid(im, key)
    except (ValueError, OSError, SyntaxError, Image.DecompressionBombError) as e:
        raise ValueError(f"{src}: {e}") from None


def _load(src, frame, frames, fps, key, budget):
    if os.path.isdir(src):
        return [_image_grid(p, key, budget) for p in _png_paths(src)]
    try:
        with Image.open(src) as im:
            if im.format == "GIF" or getattr(im, "is_animated", False):
                return _load_timed(im, fps, key, budget)
            if frames:
                if im.width % frames:
                    raise ValueError(f"{im.width} px wide does not split into {frames} frames")
                fw = im.width // frames
            else:
                fw = frame or im.height
                if fw <= 0 or im.width % fw:
                    raise ValueError(f"{im.width} px wide is not a whole number of {fw}-px frames"
                                     + ("" if frame else " (square frames assumed): pass --frame W or --frames N"))
            count = im.width // fw
            budget.add(fw, im.height, count)
            return [_grid(im.crop((k * fw, 0, (k + 1) * fw, im.height)), key) for k in range(count)]
    except (ValueError, OSError, SyntaxError, Image.DecompressionBombError) as e:
        raise ValueError(f"{src}: {e}") from None


def _load_timed(im, fps, key, budget):
    out, elapsed_ms, previous_tick, index = [], 0, 0, 0
    decoded = _InputBudget()
    while True:
        try:
            im.seek(index)
        except EOFError:
            break
        index += 1
        decoded.add(*im.size)
        ms = im.info.get("duration") or 0
        elapsed_ms += ms
        if elapsed_ms > MAX_CLIP_SECONDS * 1000:
            raise ValueError(f"image duration exceeds {MAX_CLIP_SECONDS} seconds")
        hold = 1
        if fps and ms:
            if fps >= (MAX_INPUT_FRAMES + 0.5) * 1000 / elapsed_ms:
                raise ValueError(f"timed image expands beyond {MAX_INPUT_FRAMES:,} frames at {fps:g} fps")
            end_tick = math.floor(elapsed_ms * fps / 1000 + 0.5)
            hold = end_tick - previous_tick
            previous_tick = end_tick
        if hold:
            budget.add(*im.size, hold)
            out.extend([_grid(im, key)] * hold)
    if not out:
        im.seek(0)
        budget.add(*im.size)
        out.append(_grid(im, key))
    return out


def _wide_strip(src):
    """A single-image file wider than it is tall: a strip load cuts into frames."""
    if not os.path.isfile(src):
        return False
    with Image.open(src) as im:
        return im.format != "GIF" and getattr(im, "n_frames", 1) == 1 and im.width > im.height


VALUED = {"--loop", "--frame", "--frames", "--eye", "--eye-at", "--facing", "--ink", "--shadow", "--effects", "--allow",
          "--glows-eye", "--idle", "--move", "--out", "--fps", "--name", "--action", "--speed", "--parts", "--squash",
          "--palette", "--glow", "--ref", "--mark", "--sheet", "--key", "--min-rate", "--style", "--spots"}
FLAGS = {"--flier", "--legless", "--no-preview", "--selftest", "--help", "-h"}


def _args(argv):
    """{option: [values]} for the valued options, {flag: [True]} for the flags. ValueError on an unknown option or a
    missing value."""
    got, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a in VALUED:
            if i + 1 >= len(argv):
                raise ValueError(f"{a} needs a value")
            got.setdefault(a, []).append(argv[i + 1])
            i += 2
        elif a in FLAGS:
            got.setdefault(a, []).append(True)
            i += 1
        else:
            raise ValueError(f"unknown argument {a!r}")
    return got


def _and(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _unnamed(loops, spec, idle_given, move_given):
    """The notes for a rest or travel loop missing under its default name (no --idle or --move given): the checks
    tied to that loop then do not run, which would otherwise pass for a clean result. Only the checks that run for
    this kind of body are named (hop, stiff, skate and gait never run on a flier; shallow only on one). Checking an
    action loop alone is fine, so these are notes, not errors."""
    out, legged = [], not spec.flier and spec.gait
    if not idle_given and spec.idle not in loops:
        skip = ["snap"] + (["hop"] if legged else []) + (["shallow"] if spec.flier else []) + ["drift"]
        out.append(f"note: no loop is named '{spec.idle}' (name the rest loop with --idle NAME): {_and(skip)} "
                   f"{'is' if len(skip) == 1 else 'are'} not run, and frozen, tick, reshape, mark and lag do not "
                   f"judge a loop as the idle")
    if not move_given and spec.move not in loops:
        skip = ["still"] + (["stiff", "skate", "gait"] if legged else [])
        judge = ["frozen"] + (["tick"] if spec.flier else []) + ["mark", "lag"]
        rest = (", and shallow judges the idle without a move to compare" if spec.flier
                else ", and ground judges every loop")
        out.append(f"note: no loop is named '{spec.move}' (name the travel loop with --move NAME): {_and(skip)} "
                   f"{'is' if len(skip) == 1 else 'are'} not run, {_and(judge)} do not judge a loop as the move"
                   f"{rest}")
    return out


def _eye_pieces(loops, spec):
    """A note per loop whose first frame shows the eye colour in more than one piece: which piece is read as the eye
    (_eye_piece: the biggest, the frontmost on a tie, or the nearest to --eye-at), so a wrong pick shows before its
    faults are trusted."""
    out = []
    for a, frames in loops.items():
        if spec.eye is None or a in spec.glows_eye or not frames:
            continue
        n = len(_blobs(np.array([[v == spec.eye for v in r] for r in frames[0]])))
        if n > 1:
            y, x = _eye_piece(frames[0], spec)
            how = "the nearest to --eye-at" if spec.eye_at else                 "the biggest, the frontmost on a tie: name another with --eye-at X,Y"
            out.append(f"note: {a}[0] shows the eye colour {spec.eye} in {n} pieces; the eye is read as the one at "
                       f"row {y:g}, column {x:g} ({how}) and followed from there")
    return out


def _preview_folder(out, name, sources):
    root = os.path.realpath(out)
    folder = root
    if any(os.path.isdir(p) and os.path.samefile(root, p) for p in sources if os.path.exists(root)):
        folder = os.path.join(root, "anim-previews")
        if os.path.normcase(os.path.realpath(folder)) != os.path.normcase(folder):
            raise ValueError(f"preview folder {folder} must not redirect to another path")
    inputs = [p for p in sources if not os.path.isdir(p)]
    for src in sources:
        if os.path.isdir(src):
            inputs.extend(_png_paths(src))
    for suffix in ("_check.png", "_check.gif", "_check.json"):
        target = os.path.join(folder, name + suffix)
        resolved = os.path.realpath(target)
        if os.path.normcase(os.path.dirname(resolved)) != os.path.normcase(folder):
            raise ValueError(f"output {target} resolves outside {folder}")
        for source in inputs:
            if (os.path.normcase(resolved) == os.path.normcase(os.path.realpath(source))
                    or os.path.exists(target) and os.path.samefile(target, source)):
                raise ValueError(f"output {target} conflicts with source {source}; choose a different --out or --name")
    if os.path.isdir(os.path.join(folder, name + "_check.json")):
        raise ValueError(f"preview manifest path is a directory in {folder}; choose a different --out or --name")
    return folder


def _replace_manifest(pending, target):
    """Allow a concurrent Windows rename to settle before treating the output as locked."""
    for delay in (0.01, 0.02, 0.04, 0.08, 0.16):
        try:
            os.replace(pending, target)
            return
        except PermissionError as exc:
            if getattr(exc, "winerror", None) not in (5, 32, 33):
                raise
            time.sleep(delay)
    os.replace(pending, target)


def _publish_previews(loops, spec, faults, out, name):
    os.makedirs(out, exist_ok=True)
    generation = tempfile.mkdtemp(prefix=".limberpix-preview-", dir=out)
    png, animated = f"{name}_check.png", f"{name}_check.gif"
    pending = os.path.join(generation, "manifest.json")
    try:
        sheet(loops, os.path.join(generation, png), faults=faults)
        gif(loops, os.path.join(generation, animated), fps=spec.fps, speed=spec.speed, move=spec.move, facing=spec.facing)
        with open(pending, "w", encoding="utf-8") as fh:
            folder = os.path.basename(generation)
            json.dump({"png": f"{folder}/{png}", "gif": f"{folder}/{animated}"}, fh)
    except BaseException:
        shutil.rmtree(generation, ignore_errors=True)
        raise
    try:
        _replace_manifest(pending, os.path.join(out, f"{name}_check.json"))
    except OSError:
        shutil.rmtree(generation, ignore_errors=True)
        raise
    return generation


def main(argv):
    """The command line (see the module's help). Returns the exit code: 0 no fault, 1 faults, 2 a usage error."""
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    try:
        got = _args(argv)

        def opt(name, default=None, many=False):
            vals = got.get(name, [])
            return vals if many else (vals[-1] if vals else default)

        def cols(s):
            return {hexcol(c) for c in s.split(",") if c.strip()} if s else set()

        def count(name):
            v = opt(name)
            if v is None:
                return None
            if not v.isdigit() or int(v) <= 0:
                raise ValueError(f"{name} must be a whole number over 0, not {v!r}")
            return int(v)
        frame, frames = count("--frame"), count("--frames")
        if frame and frames:
            raise ValueError("give --frame or --frames, not both")
        srcs = {}
        for spec_ in opt("--loop", many=True):
            if "=" not in spec_:
                raise ValueError(f"--loop takes NAME=PATH, not {spec_!r}")
            name, src = spec_.split("=", 1)
            if not name:
                raise ValueError(f"--loop needs a name in {spec_!r}")
            if name in srcs:
                raise ValueError(f"duplicate loop {name!r}: {srcs[name]} and {src}")
            if not os.path.exists(src):
                raise ValueError(f"no such file or folder: {src}")
            srcs[name] = src
        if not srcs:
            print(__doc__)
            return 2
        facing = opt("--facing", "right")
        if facing not in ("right", "left"):
            raise ValueError("--facing must be right or left")
        style = opt("--style", "pixel")
        if style not in ("pixel", "redrawn"):
            raise ValueError("--style must be pixel or redrawn")
        allow = {}
        for a in opt("--allow", many=True):
            k, _, v = a.partition("=")
            if not v.isdigit():
                raise ValueError(f"--allow takes LOOP=N, not {a!r}")
            allow[k] = int(v)
        try:
            fps = float(opt("--fps", 30))
        except ValueError:
            raise ValueError(f"--fps must be a number, not {opt('--fps')!r}") from None
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("--fps must be finite and over 0")
        key = hexcol(opt("--key")) if opt("--key") else None
        budget = _InputBudget()
        loops = {name: _load(src, frame, frames, fps, key, budget) for name, src in srcs.items()}
        for name, poses in loops.items():
            if not poses:
                raise ValueError(f"no frames in loop {name!r}")
            if key is None and all(v is not None for f in poses for r in f for v in r):
                raise ValueError(f"loop {name!r} ({srcs[name]}) has no transparent pixel in any frame, so its "
                                 f"background would be read as the figure: export it with a transparent background, "
                                 f"or name the background colour with --key #rrggbb")
        actions = dict(parse_action(t, facing) for t in opt("--action", many=True))
        named = [opt(o) for o in ("--idle", "--move") if opt(o) is not None]
        for a in list(actions) + list(allow) + opt("--glows-eye", many=True) + opt("--sheet", many=True) + named:
            if a not in loops:
                raise ValueError(f"no loop named {a!r} (give it with --loop)")
        part_strips = {}
        sources = list(srcs.values()) + [opt(o) for o in ("--palette", "--ref", "--spots") if opt(o)]
        for t in opt("--parts", many=True):
            a, _, src = t.partition("=")
            if a not in loops or not os.path.exists(src):
                raise ValueError(f"--parts takes LOOP=PATH for a given loop and an existing file, not {t!r}")
            sources.append(src)
            part_strips[a] = _load(src, frame, frames, fps, key, budget)
            if list(map(_frame_size, part_strips[a])) != list(map(_frame_size, loops[a])):
                raise ValueError(f"--parts {a}: the part strip must hold the loop's frames at the loop's size")
        speed = opt("--speed")
        try:
            speed = float(speed) if speed is not None else None
        except ValueError:
            raise ValueError(f"--speed must be a number, not {speed!r}") from None
        if speed is not None and not math.isfinite(speed):
            raise ValueError("--speed must be finite")
        min_rate = opt("--min-rate")
        try:
            min_rate = float(min_rate) if min_rate is not None else None
        except ValueError:
            raise ValueError(f"--min-rate must be a number, not {min_rate!r}") from None
        if min_rate is not None and (not math.isfinite(min_rate) or min_rate <= 0):
            raise ValueError("--min-rate must be finite and over 0")

        def image(name):
            p = opt(name)
            if p is None:
                return None
            if not os.path.isfile(p):
                raise ValueError(f"no such file: {p}")
            return _image_grid(p, key, budget)
        pal = image("--palette")
        ref = image("--ref")
        spot_groups = None
        if opt("--spots"):
            if not opt("--ref"):
                raise ValueError("--spots needs --ref: its marks are placed on the approved drawing")
            if not os.path.isfile(opt("--spots")):
                raise ValueError(f"no such file: {opt('--spots')}")
            try:
                with open(opt("--spots"), encoding="utf-8") as fh:
                    raw = json.load(fh)
                raw = raw.get("groups", raw)
                spot_groups = {str(k): [(float(p[0]), float(p[1])) for p in v] for k, v in raw.items()}
            except (ValueError, TypeError, AttributeError, IndexError, KeyError):
                raise ValueError("--spots takes a JSON file {\"group\": [[row, column], ...], ...} in the "
                                 "approved drawing's pixels") from None
            if not spot_groups or not all(spot_groups.values()):
                raise ValueError("--spots: every group needs one mark or more")
            _validate_spot_coordinates(spot_groups, ref)
        eye = opt("--eye")
        eye_at = None
        if opt("--eye-at"):
            try:
                ex, ey = (int(v) for v in opt("--eye-at").split(","))
            except ValueError:
                raise ValueError(f"--eye-at takes X,Y (a column and a row of the first frame), not "
                                 f"{opt('--eye-at')!r}") from None
            if not eye:
                raise ValueError("--eye-at needs --eye: it says which piece of the eye colour is the eye")
            eye_at = (ex, ey)
        spec = Spec(ink=cols(opt("--ink")) or None, shadow=cols(opt("--shadow")), effects=cols(opt("--effects")),
                    eye=hexcol(eye) if eye else None, flier="--flier" in got, idle=opt("--idle", "idle"),
                    move=opt("--move", "move"), allow=allow, glows_eye=opt("--glows-eye", many=True),
                    gait="--legless" not in got, fps=fps, facing=facing, actions=actions, speed=speed,
                    parts=part_strips, squash=cols(opt("--squash")),
                    palette={v for r in pal for v in r if v is not None} if pal else None,
                    glow=cols(opt("--glow")), ref=ref, marks=sorted(cols(opt("--mark"))),
                    sheets=opt("--sheet", many=True), min_rate=min_rate, style=style, spots=spot_groups,
                    eye_at=eye_at)
        name = opt("--name", "anim")
        if not name or name in (".", "..") or any(c in '/\\:<>"|?*' or ord(c) < 32 for c in name):
            raise ValueError(f"--name must be a file name, not {name!r}")
        out = None if "--no-preview" in got else _preview_folder(opt("--out", "."), name, sources)
        square = not frame and not frames and any(_wide_strip(src) for src in srcs.values())
    except (ValueError, OSError, Image.DecompressionBombError) as e:
        print(f"error: {e}  (--help lists the options)", file=sys.stderr)
        return 2
    if square:
        print("note: strips cut into square frames (no --frame or --frames given)")
    for line in _unnamed(loops, spec, "--idle" in got, "--move" in got) + _eye_pieces(loops, spec):
        print(line)
    warns = []
    faults = _check(loops, spec, warns)
    print(f"{name}: {len(faults)} fault(s)")
    for f in faults + warns:
        print("  " + f)
    if any(f.startswith("size:") for f in faults):
        for a, src in srcs.items():
            if os.path.isdir(src) and len({_frame_size(f) for f in loops[a]}) > 1:
                print(f"  {a}: {src} has differently sized PNGs; move any old contact sheet out of the frame folder")
        return 1                                          # the pictures and motion tracks compare pixels by position
    for line in tracks(loops, spec):                     # read these before the GIF (the eye's rows, the steps)
        print("  " + line)
    if out is not None:
        try:
            generation = _publish_previews(loops, spec, faults, out, name)
        except (OSError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print("sheets:", generation)
    return 1 if faults else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            import pixel_anim_selftest
        except ImportError:
            print("error: --selftest needs pixel_anim_selftest.py beside this file", file=sys.stderr)
            sys.exit(2)
        sys.exit(0 if pixel_anim_selftest.run("--verbose" in sys.argv) else 1)
    sys.exit(main(sys.argv[1:]))
