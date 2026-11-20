---
name: pixel-anim-check
description: Check a pixel-art sprite animation (idle, walk, attack or any loop of a character or creature) for faults that make sprite motion look broken. Takes sprite strips, frame folders or GIFs plus the eye colour. Reports size mismatches, stray specks, a lost eye, open outlines, feet off the ground, pops, texture shimmer, a frozen head, choppy or uneven timing, dead stops, 1-px ticks, hops, vanishing parts, shallow wing beats and a redrawn face; writes a contact sheet and a GIF for a look by eye. Use whenever a sprite animation is made or changed, and before showing or shipping one.
---

# Pixel-art animation check

Run this before an animation is shown to anyone or put into a game: the run should report **0 faults**, and the
inspection by eye below should find nothing. A reviewer's time is best spent on taste, not on defects a script can
find, so catch those first.

The check is itself tested (step 4). A check that is run only for show, or that cries wolf, is worse than none.

**Paths.** The scripts sit next to this file. Inside Claude Code, `${CLAUDE_SKILL_DIR}` is that folder; outside
Claude Code, read `${CLAUDE_SKILL_DIR}` as the folder holding this SKILL.md. Python 3.8+ with numpy and Pillow.

## Terms

- **On ones, twos, threes:** a new drawing every frame, every 2nd frame, every 3rd. At 30 fps, twos are 15 pictures a
  second and threes 10.
- **Hold:** how many frames one drawing stays on screen. A **moving hold** is a pose that looks still but keeps a
  small motion (a breath, a blink) so it never freezes.
- **Game px vs reference px:** a game pixel is one pixel of the sprite as the game shows it. A reference pixel is
  one pixel of the larger drawing the animation was made from. Thresholds here are in game px unless they say
  otherwise.
- **Contact sheet:** one image with every distinct pose side by side, zoomed, so poses can be compared at a glance.
- **Rig:** a pipeline that poses cut-out parts by numbers (angles, offsets) before rendering frames.
- **Lint:** a check run on the rig's pose numbers alone, without rendering, to catch a cause the frames cannot show.

## 1. Run it

The script is `pixel_anim_check.py`; its tests are in `pixel_anim_selftest.py`.

```
python -I ${CLAUDE_SKILL_DIR}/pixel_anim_check.py --loop idle=idle.png --loop move=walk.png --frame 32 \
       --eye "#ffcc33" [--flier --shadow "#2b2430"] [--effects "#fff4c8,#ffd27a"] [--allow attack=12] \
       [--glows-eye attack] [--idle idle --move move] [--facing left] [--legless] [--fps 30] \
       --out check --name fox
```

- A loop is a horizontal strip PNG, a folder of frame PNGs, or a GIF.
  - For a strip give `--frame W` (one frame's width) or `--frames N` (how many frames it holds). Without either,
    square frames are assumed, and a strip whose width is not a whole number of its height is refused.
  - A folder is read in file-name order: zero-pad the numbers (`f00.png`, `f01.png`, ...).
  - A GIF is read at its own timing: each image is held for its duration at `--fps` (130 ms at 30 fps is 4 frames).
    Exporters store a held pose as one image with a longer duration, so this keeps the holds the check judges.
- Every frame of every loop must have one size, with the figure kept in place, not trimmed per frame.
- Colours are given as `#rrggbb` (any case, the `#` optional).
- A flier's ground-shadow colours must be given with `--shadow`, or the shadow counts as a stray piece (`apart`).
- The outline is every colour darker than lightness 40, unless `--ink` names it.
- `--facing left` for a creature whose head faces left (where `reshape` reads the face); `--legless` for a snake or
  slug (no body rise asked of its move, and `hop` judges every loop); `--fps` the rate the game plays the loops at.
- In a project with its own pipeline, call `pixel_anim_check.check(loops, Spec(...))` from a small adapter.
  - Pixels may be any colour key; pass `lum` and `rgb` to read them.
  - Import the module from the skill folder, or vendor a copy of `pixel_anim_check.py` and `pixel_anim_selftest.py`
    (the selftest needs both). If you vendor them, make changes in one place first and copy them over, so the
    copies do not drift apart.

It prints the faults, then warnings (`warn:` lines: the eye tick and `reshape` outside the
idle, where an action may jump or open its jaw on purpose; look at them, they do not count), then per loop the
**per-step change list** (the share of the figure changed from each frame to the next, a 1-px bob forgiven) and the
**eye's row track** (runs of `(row, frames)`). The exit code is 0 for no fault, 1 for one or more, 2 for a usage
error. Frame numbers are 0-based: `move[3]` is the move's fourth frame, and "frame k" in a `jump` or `snap` is the
change from frame k to the next. It writes:
- `<name>_check.png`: the contact sheet, each distinct pose zoomed (at most 12 a loop, plus any a fault names) and
  labelled with the frames it holds (`4-7`), and under each the pixels changed from the pose before, in red. The
  poses a fault names are outlined in red.
- `<name>_check.gif`: the loops side by side, at `--fps`.
- In code: `check(loops, spec, warns)` fills the list `warns`; `tracks(loops, spec)` returns the two read-outs.

## 2. What each fault means and the usual fix

| Fault | Meaning | Usual cause, fix |
|---|---|---|
| `size` | frames differ in size | trimmed per frame: crop every loop to one union box |
| `apart` | a piece apart from the figure | a cut part's leftover edge, a thin joint lost when shrinking, loose bits (embers, hair) that blink in and out: keep the main piece, or `--allow` what is thrown on purpose |
| `eye` | the eye gone on a frame | the eye not moved with its part (the head), or a glow recolouring it (`--glows-eye` that loop) |
| `outline` | coloured edge pixels with no ink | two drawings put together: ink the seam |
| `ground` | a walker's feet leave the ground line outside the move; a flier's shadow slides | a lift applied to the whole figure; a limb turned about its hip pushes the toes through the floor: shift it back up, or shear instead of turning |
| `jump` | one change far over the loop's mean, or one frame knocked sideways | a pose out of order, a stray offset, a part stepping two levels at once |
| `still` | the move changes under 1.5 % of the figure a frame | amplitudes too small for the sprite's size |
| `shimmer` | pixels flipping to another tone for one frame and back, often | texture redrawn each frame (AI frames), or a part scaled or turned a fraction every frame and resampled: hold small motions two frames a step and in whole steps (whole pixels, 1.5° turns). A sub-pixel in-between (an edge's mid tone stepping monotonically into a 1-px move) is not counted; switching a few pixels on and off is |
| `stiff` | a walker's body never rises or falls in the move (not asked of a `--legless` crawler) | legs stepping under a board: raise the body (not the feet) a whole pixel as the legs pass under it, twice a stride; fill the hips with an overlap |
| `choppy` | a continuous loop (4+ moves, no rest of a third of the loop) updating under 10 times a second however small its steps, or dropping one update (median hold 3+ and one hold twice it); give `--fps` | a few drawings each held long (a big animal's idle stepping one part every 6 frames: 5/s), or two quantised ticks running on one pose (a 3-frame cadence with one 6-frame hold). Give a new pose at least every 0.1 s: at 30 fps hold every pose 2 frames (15/s; 3 is the floor, never 4+ inside a cycle), at 12 fps 1 frame; put all parts on one clock (`k // 2 * 2`) with phases staggered 0.4-1.2 rad so something changes on every tick; or draw in-betweens. Never lower the pose rate to silence `uneven` |
| `uneven` | the holds between moves jump in turn (1, 3, 1, 3) in a cycle of 4+ moves | parts rounded on their own (each part's turn rounded separately lands on different frames), or a sequence of mixed holds: put every part on one beat (`k // 3 * 3`) and hold every pose alike. Ease doubling the hold at a sway's turns is fine |
| `lurch` | a held cycle (6+ moves) whose moves alternate big and small | a whole-body bob on its own step between small leg steps, with frames held between: give the legs a new pose every frame and let the bob ride them; or a sine sampled so two poses running fall on one angle (sin 60 = sin 120): sample it half a step off |
| `frozen` | the head (round the eye) hardly moves against the body in the idle or the move | a living creature with a mask for a head: nod it on the steps, let it look about in the idle, flick the ears |
| `snap` | the idle stands dead still a third of a second or more, then changes a quarter of the figure in one step | an idle built from one long-held drawing and a burst of walk drawings: never stop dead (a breath, a blink, a glint at least every 12 frames: the moving hold); ease a big change in and out (holds 3, 2, 2, 3, each step under 25 %), or drop it. An action's held anticipation is not judged |
| `tick` | a whole-pixel level left and regained within a few frames: the eye's row in the idle (an extreme held under 3 frames, under 4 in a two-level square wave; a cluster of 3+ short runs, a sniff, is exempt), or a flier's whole-body height in its idle or move (the shortest excursion under 0.18 of its share of the loop) | a lift peaking 0.5-0.9 px: only the curve's top rounds up, for 2 frames. Use no lift (peak under 0.5 px) or a whole one (1-1.2 px: up a third of the beat), written as `px * round(max(0, sin))` and checked after the rig's rounding; keep a neck or head turn's travel at the eye under 0.5 px or over 1. Read the eye track |
| `hop` | a grounded body leaves its contact: the columns resting on the lowest row shrink under half the usual, or 60 %+ of a big step is the whole body shifted (the idle of any non-flier; every loop of a `--legless` body) | a lift or a seat step that moves a whole layer or frame (the belly row stays while all above it rises): pin the body where it lies on the ground, move only the parts above it (neck, head, arches), never translate a frame |
| `vanish` | a piece of 8+ px switches off (or on), its place stays empty 3+ frames, while the rest is nearly still (the piece over 1.1 times the mean change while it is gone) | a far wing hidden at the turn of a shallow stroke (an edge-hidden rule firing where the stroke is slowest): hide a part only while it crosses edge-on, for at most 5 frames; otherwise keep 25-30 % of it showing. A part hidden behind others is not seen here: lint the rig's hide rule (see below) |
| `shallow` | a flier's idle puts under 0.3 times as much of its change in the lower half of the figure as its move does (with no move: under 80 % of its rows or 60 % of its pixels ever change) | a wing squeezed about its own lower edge only shortens from the top: beat the same wing more slowly, not less far (depth 0.7+, crossing the shoulder line: edge-on, then under the belly) in the idle too; turn spread wings about the shoulder point. Walkers are not judged: a standing idle rightly keeps its legs still |
| `reshape` | the face window (from 1 px behind the eye forward; `--facing`), aligned on itself, changes class (air, ink, colour) on over 10 % of its pixels per pose change on average, in the idle (a warning elsewhere) | a sheet or AI drawings redrawing the head in every cell, or block lines read per cell that merge a narrow snout column: draw the head once and paste one approved head at each drawing's place (placed by the eye), re-ink the seam; read every cell on one shared grid. A jaw opened on purpose in an action is a warning only |

A whole-figure bob of a pixel, a glow's pulse, a limb sweeping past, a wing coming back at the end of its stroke,
and tones too alike to tell apart are motion on purpose. The check aligns or ignores them. If one is reported, fix
the check, not the art (step 4).

## 3. Look at it yourself

First read the two tracks the run printed, before the GIF. A fault shows there before it shows in a GIF:
- **The eye's row track** (`(row, frames)` runs): a level reached for 2-3 frames and left (a tick), or a square wave
  dwelling under 4 frames. Each level the eye takes should last 4+ frames at an extreme (3 on a smooth path).
- **The per-step change list**: a long run of zeros followed by a big step (a dead stop, then a lurch); a lone
  doubled hold among even ones (a dropped update); steps alternating big and small (a lurch).

If your pipeline has a rig, also lint its pose curves, where the frame grid cannot see the cause: for example a
squeezed wing that never crosses 0 in its idle (a shallow stroke), a part hidden at a turn rather than while
crossing edge-on, a lift whose rounded peak falls in 0.5-0.9 px, and a seat or ground step that translates a whole
frame. These lints are checks to write in your own pipeline; this skill does not ship them.

Then open the contact sheet and the GIF, zoomed and at 1×, and look for:

- **Likeness:** it still looks like its approved drawing: shape, colours, eye, what it carries.
- **Seams:** where parts meet there is no gap, no doubled outline, no hard straight edge, no flat patch of fill.
- **Life everywhere:** each part moves, and in a chain.
  - The head nods and looks; ears and tails follow a beat late.
  - A tail bends along its length, not only at its tip and root.
  - In the idle the creature *stands*: it is not caught mid-stride.
- **Motion reads at 1×:**
  - Wings seen from the side beat by foreshortening, not by turning like a door. Spread wings seen from the front
    turn about the shoulder.
  - The foot swinging forward lifts.
- **Each loop does its job:** the idle is calm, the move travels, the action says what the creature does.
- **Glow and effects:**
  - They light the creature's own light only, in a colour that stands out from what it lights.
  - Effects sit where they belong.
  - Their shapes carry no symbols you did not intend.
- **Rhythm:** nothing jerks, and nothing crawls.

## 4. When the check itself changes

Run `python -I ${CLAUDE_SKILL_DIR}/pixel_anim_check.py --selftest`.
- It draws a small walker and a small flier that animate well. They must pass with no false alarm.
- A third clean case, a walker breathing a pixel with a sub-pixel tone leading each step, must pass too (`shimmer`
  must not count the in-between).
- It then breaks them on purpose: a speck, a lost eye, an opened outline, a hop off the ground, a sliding shadow, a
  frame knocked sideways, a frozen walk, a crawling texture (alternating, random, and on a beating wing), a frozen
  head, a body that never rises in the walk, a few drawings held long, an idle stepped every 6 frames, a dropped
  update, a dead stop then a burst, a 2-frame 1-px blip, a body lifted off its feet's row, a far wing switched off
  at the bottom of its stroke, a wing squeezed from its top only, a snout cut on every other pose, uneven holds, a
  lurching bob, a narrowed frame. Each must be caught by its own fault.
- The thresholds of `choppy`, `snap`, `tick`, `hop`, `vanish`, `shallow` and `reshape` were fitted to a private
  calibration set: 39 animated creatures, with 15 accept or reject judgements on them by one reviewer (the margins
  are in each function's docstring). That set is not included here. No source gives a pixel threshold for judder (see
  [REFERENCES.md](REFERENCES.md)), so treat the thresholds as tested defaults, and keep them honest with your own
  accepted animations as below.

A new check comes with its own case in `pixel_anim_selftest.py`. After the selftest, rerun the check on every
animation already accepted in your project:
- A new fault there is either a real one, which you report to whoever owns the art, or a false alarm, which you fix
  in the check.

## 5. When showing it

Say in one line what was checked (the run's result and the inspection by eye) and what is still doubtful. Never say
"checked" for something not run. If the project has a review step (an art lead, a client, the person you are
working with), show the GIF and the contact sheet there before the animation goes into the game.
