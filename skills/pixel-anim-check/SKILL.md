---
name: pixel-anim-check
description: Check a pixel-art sprite animation (idle, walk, attack or any loop of a character or creature) for faults that make sprite motion look broken. Takes sprite strips, frame folders or GIFs plus the eye colour. Reports size mismatches, stray specks, a lost eye, open outlines, feet off the ground, pops and held poses knocked sideways, texture shimmer, a frozen head, choppy or uneven timing, dead stops, 1-px ticks, hops, vanishing parts, shallow wing beats, a redrawn face, colours off the palette and lost marks; warns on sliding feet, walk bobs, a repeated pose at a loop's seam, outline boil, action timing (anticipation, strike, recovery, jumps), part volume and lag, a torso split into bands, a head stepping alone after a long hold, blends, orphan pixels, doubled outlines and drift from the approved drawing; writes a contact sheet and a GIF for a look by eye. Use whenever a sprite animation is made or changed, and before showing or shipping one.
---

# Pixel-art animation check

Run this before an animation is shown to anyone or put into a game: the run should report **0 faults**, and the
inspection by eye below should find nothing. A reviewer's time is best spent on taste, not on defects a script can
find, so catch those first.

The check is itself tested (step 4). A check that is run only for show, or that cries wolf, is worse than none.

**Paths.** The scripts sit next to this file. Inside Claude Code, `${CLAUDE_SKILL_DIR}` is that folder; outside Claude
Code, read `${CLAUDE_SKILL_DIR}` as the folder holding this SKILL.md. Python 3.8+ with numpy and Pillow. The commands
use `python -I` (isolated mode): it leaves the script's own folder, `PYTHON*` variables (such as a `PYTHONPATH` into
the project) and the user's site-packages off the import path, so a stray file named like a standard module
(`json.py`) cannot shadow it. It also hides packages installed with `pip install --user`: on `No module named 'numpy'`
(or `'PIL'`), install numpy and Pillow in a virtual environment or for the whole system, or drop the `-I`.

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
       [--action bite:strike:right] [--speed 0.5] [--parts move=move_parts.png --squash "#ff0000"] \
       [--palette approved.png] [--ref approved.png] [--glow "#fff4c8"] [--mark "#5ad1e0"] [--sheet move] \
       [--key "#ff00ff"] --out check --name fox
```

- A loop is a horizontal strip PNG, a folder of frame PNGs, or a GIF.
  - For a strip give `--frame W` (one frame's width) or `--frames N` (how many frames it holds). Without either,
    square frames are assumed, and a strip whose width is not a whole number of its height is refused.
  - A folder is read in file-name order: zero-pad the numbers (`f00.png`, `f01.png`, ...).
  - GIF timing follows the stored delays. Elapsed time is rounded to game frames at `--fps`, so ten 50 ms poses
    cover 15 frames at 30 fps. A pose shorter than a game frame may fall between samples.
- Keep the figure in a fixed-size frame across every loop. On a size mismatch the CLI reports `size` and exits
  before comparing motion or rendering previews.
- Colours are given as `#rrggbb` (any case, the `#` optional).
- Air is read from transparency. A strip with a flat background and no transparency (common in AI sheets) would be
  checked as one solid figure, so it is refused unless `--key #rrggbb` names the background colour; `--key` also
  applies to `--parts`, `--ref` and `--palette`. It removes that exact colour only: clean a key's anti-aliased fringe
  before, or the fringe reads as specks and open outline.
- A flier's ground-shadow colours must be given with `--shadow`, or the shadow counts as a stray piece (`apart`).
- The outline is every colour darker than lightness 40, unless `--ink` names it.
- `--facing left` for a creature whose head faces left (where `reshape` reads the face); `--legless` for a snake or
  slug (no body rise asked of its move, and `hop` judges every loop); `--fps` the rate the game plays the loops at.
- Name the rest and travel loops `idle` and `move`, or give `--idle NAME --move NAME`. Several checks are tied to
  those two loops (`snap`, `hop`, `shallow` and `drift` to the idle; `still`, `stiff`, `skate` and `gait` to the
  move), so under other names they do not run and the result looks cleaner than it is. The run prints a `note:` line
  for each missing name, naming the checks that apply to that body; a name given with `--idle` or `--move` that
  matches no loop is a usage error.
- `--action NAME[:KIND[:DIR]]` declares an action loop. Every declared action may hold one key (a wind-up or a
  contact) for up to 13 frames at 30 fps outside `choppy` and `uneven`; its other frames keep every rule. KIND
  `strike` judges its phases (DIR the way it strikes: right, left, up or down; default the facing). KIND `jump` may
  leave the ground (`ground` is not asked). Any other word (`breath`, `spit`, `bell`) is a gesture: no phase checks,
  since a breath or a bell has no counter-move.
- `--speed PX` is the road's scroll in game px a frame, for a walker drawn walking in place. The planted feet's speed
  is printed beside it, and the GIF scrolls a ground line under the move. The road may ease, so it is a read-out.
- `--parts LOOP=PATH` gives a part strip: the same frames with each rig part filled in one flat colour (the cut's
  labels). Per-part `volume` and `lag` are read from it. `--squash` names the part colours whose area changes on
  purpose (wings, a squashed body).
- `--palette PATH` (the approved drawing at game size) makes any colour outside it a fault; `--ref PATH` compares the
  idle with it (`drift`); `--glow` names colours that show in some frames on purpose (glow steps, glints, blink lids).
- `--mark` names small defining marks (a gem, a lamp, a lone bright pixel) that must show on every frame and never
  jump 2 px in one frame. `--sheet LOOP` says a loop was drawn as a sheet or by AI (`swap` looks for a part switched
  off for a cell).
- In a project with its own pipeline, call `pixel_anim_check.check(loops, Spec(...))` from a small adapter.
  - Pixels may be any colour key; pass `lum` and `rgb` to read them.
  - Import the module from the skill folder, or vendor a copy of `pixel_anim_check.py` and `pixel_anim_selftest.py`
    (the selftest needs both). If you vendor them, make changes in one place first and copy them over, so the
    copies do not drift apart.

It prints the faults, then warnings (`warn:` lines: the eye tick, `reshape` and `mark` outside the idle, where an
action may jump or open its jaw on purpose, and the later checks of section 2b; look at them, they do not count),
then per loop the **per-step change list** (the share of the figure changed from each frame to the next, a 1-px bob
forgiven), the **eye's row track** (runs of `(row, frames)`), and the later read-outs: the update rate against the
real-pose rate, the box's height, width and anchor (a sheet's scale drifting shows here), rare colours, the move's
bob and leg band and planted-foot speed, the eye's lag behind the figure's top, each action's phases and staging,
and each part's area and lag. The exit code is 0 for no fault, 1 for one or more, 2 for a usage
error. Frame numbers are 0-based: `move[3]` is the move's fourth frame, and "frame k" in a `jump` or `snap` is the
change from frame k to the next. It writes:
- `<name>_check.png`: the contact sheet, each distinct pose zoomed (at most 12 a loop, plus any a fault names) and
  labelled with the frames it holds (`4-7`), and under each the pixels changed from the pose before, in red. The
  poses a fault names are outlined in red.
- `<name>_check.gif` plays the loops side by side at `--fps`. It repeats at a shared cycle boundary, including
  the scrolling road. When the cycles take too long to align, the preview plays once.
- In code: `check(loops, spec, warns)` fills the list `warns`; `tracks(loops, spec)` returns the two read-outs.

## 2. What each fault means and the usual fix

| Fault | Meaning | Usual cause, fix |
|---|---|---|
| `size` | frames differ in size | trimmed per frame: crop every loop to one union box |
| `apart` | a piece apart from the figure | a cut part's leftover edge, a thin joint lost when shrinking, loose bits (embers, hair) that blink in and out: keep the main piece, or `--allow` what is thrown on purpose |
| `eye` | the eye gone on a frame, or in the idle or the move (a warning elsewhere) the eye's place jumping out of its head's box in one frame (2 × the box's half side + 1 px or more, along a row or a column). The eye is one piece of its colour: the biggest on the first frame (the frontmost on a tie), then the piece nearest its last place, so the same colour elsewhere on the body is not taken for it; a `note:` says which piece was read when the first frame has several | the eye not moved with its part (the head), or a glow recolouring it (`--glows-eye` that loop); a jump is a cell mirrored or placed off its anchor, or the eye lost while its colour shows elsewhere (the track then jumps to that patch) |
| `outline` | coloured edge pixels with no ink | two drawings put together: ink the seam. A figure cut by the cell edge shows here too (the border counts as open): size the cell from the farthest reach of every loop, with 1 px of air |
| `ground` | a walker's feet leave the ground line outside the move; a flier's shadow slides. In a legged walker's move the lowest drawn row moving is a warning, not a fault: a run, a gallop or a hopping gait leaves the ground on purpose (not asked of a move declared `--action ...:jump`) | a lift applied to the whole figure (in the walk: raise the body, not the feet); a limb turned about its hip pushes the toes through the floor: shift it back up, or shear instead of turning |
| `jump` | one change over 3.6 times the loop's usual step, or one pose knocked 2+ px sideways out of step. The usual step is the mean of the moving steps with the two biggest left out: a pose out of order makes two big steps (into it and out of it), and with them in the mean a loop of 6 moving steps or fewer could never fire, and one of 8 only on a step 12 times the others. A declared strike's own step and a declared jump's launch and landing are left out first, as big on purpose. With under 4 usual steps (a sparse idle) the change must also reach a quarter of the figure, so one ear flick among small blinks is not a jump; with under 2 (3 moving steps or fewer) only the sideways test runs. A pose held on twos or threes is one pose: it is compared with the distinct poses either side of the hold, and every frame of it is named (`move[6-7] (a held pose)`) | a pose out of order, a stray offset, a part stepping two levels at once, a sheet cell placed off its anchor |
| `still` | the move changes under 1.5 % of the figure a frame | amplitudes too small for the sprite's size |
| `shimmer` | pixels taking another tone for 0.1 s at most (3 frames at 30 fps, scaled with `--fps`) and going back to the tone before, often: on a sixth of the frames and at least three times a loop (a two-step walk passes a leg over a pixel twice, so two flips are not counted). Each pixel is read by its own runs of one tone, so a texture redrawn on drawings held on twos or threes is seen too | texture redrawn each frame (AI frames), or a part scaled or turned a fraction every frame and resampled: hold small motions two frames a step and in whole steps (whole pixels, 1.5° turns). A sub-pixel in-between (an edge's mid tone stepping monotonically into a 1-px move) is not counted; switching a few pixels on and off is |
| `stiff` | a walker's body never rises or falls in the move (not asked of a `--legless` crawler) | legs stepping under a board: raise the body (not the feet) a whole pixel as the legs pass under it, twice a stride; fill the hips with an overlap |
| `choppy` | a loop (4+ moves) updating under 10 times a second however small its steps, or dropping one update (median hold 3+ and one hold twice it); give `--fps`. A rest (a hold of a third of the loop or more) is left out and the frames left must still update at 10/s; a rest with under 3 other holds (a blink) is a gesture. A declared `--action` leaves out its single longest hold (up to 13 frames): the rest must still update at 10/s. Not seen: one 4-frame hold among twos in the middle of a motion, a lost update the rate hides; check the rig's pose list for two identical ticks outside a turn (pixel-animate, section 5) | a few drawings each held long (a big animal's idle stepping one part every 6 frames: 5/s), or two quantised ticks running on one pose (a 3-frame cadence with one 6-frame hold). Give a new pose at least every 0.1 s: at 30 fps hold every pose 2 frames (15/s; 3 is the floor), at 12 fps 1 frame. What fails is the tempo: a usual hold of 4+ frames (under 10 updates a second) reads as a low frame rate. One longer hold belongs only where the motion stops: a sway's turn (a 1-2 frame base doubled, 4 at most), an idle's rest, an action's held key; in a running motion it is a lost update; put all parts on one clock (`k // 2 * 2`) with phases staggered 0.4-1.2 rad so something changes on every tick; or draw in-betweens. Never lower the pose rate to silence `uneven` |
| `uneven` | the holds between moves jump in turn (1, 3, 1, 3) in a cycle of 4+ moves | parts rounded on their own (each part's turn rounded separately lands on different frames), or a sequence of mixed holds: put every part on one beat (`k // 3 * 3`) and hold every pose alike. Ease doubling the hold at a sway's turns is fine |
| `lurch` | a held cycle (6+ moves) whose moves alternate big and small | a whole-body bob on its own step between small leg steps, with frames held between: give the legs a new pose every frame and let the bob ride them; or a sine sampled so two poses running fall on one angle (sin 60 = sin 120): sample it half a step off |
| `frozen` | the head (round the eye) hardly moves against the body in the idle or the move | a living creature with a mask for a head: nod it on the steps, let it look about in the idle, flick the ears |
| `snap` | the idle stands dead still a third of a second or more, then changes a quarter of the figure in one step | an idle built from one long-held drawing and a burst of walk drawings: never stop dead (a breath, a blink, a glint at least every 12 frames: the moving hold); ease a big change in and out (holds 3, 2, 2, 3, each step under 25 %), or drop it. An action's held anticipation is not judged |
| `tick` | a whole-pixel level left and regained within a few frames: the eye's row in the idle (an extreme held under 3 frames, under 4 in a two-level square wave; these counts are for 30 fps, 0.1 s and 0.13 s, and scale with `--fps`; a cluster of 3+ short runs, a sniff, is exempt), or a flier's whole-body height in its idle or move (the shortest excursion under 0.18 of its share of the loop). That 0.18 fails only a lift peaking up to about 0.59 px (a rounded 1-px sine is up (π − 2·asin(0.5/A)) / 2π of the beat: 0.178 at A = 0.59, 0.313 at A = 0.9), so a peak of 0.6-0.9 px passes here though it still ticks: catch it with the rig's lift lint (section 3) | a lift peaking 0.5-0.9 px: only the curve's top rounds up, for 2 frames. Use no lift (peak under 0.5 px) or a whole one (1-1.2 px: up a third of the beat), written as `px * round(max(0, sin))` and checked after the rig's rounding; keep a neck or head turn's travel at the eye under 0.5 px or over 1. Read the eye track |
| `hop` | a grounded body leaves its contact: the columns resting on the lowest row shrink under half the usual, or 60 %+ of a big step is the whole body shifted (the idle of any non-flier; every loop of a `--legless` body) | a lift or a seat step that moves a whole layer or frame (the belly row stays while all above it rises): pin the body where it lies on the ground, move only the parts above it (neck, head, arches), never translate a frame |
| `vanish` | a piece of 8+ px switches off (or on), its place stays empty 3+ frames, while the rest is nearly still (the piece over 1.1 times the mean change while it is gone) | a far wing hidden at the turn of a shallow stroke (an edge-hidden rule firing where the stroke is slowest): hide a part only while it crosses edge-on, for at most 5 frames; otherwise keep 25-30 % of it showing. A part hidden behind others is not seen here: lint the rig's hide rule (see below) |
| `shallow` | a flier's idle puts under 0.3 times as much of its change in the lower half of the figure as its move does (with no move: under 80 % of its rows or 60 % of its pixels ever change) | a wing squeezed about its own lower edge only shortens from the top: beat the same wing more slowly, not less far (depth 0.7+, crossing the shoulder line: edge-on, then under the belly) in the idle too; turn spread wings about the shoulder point. Walkers are not judged: a standing idle rightly keeps its legs still |
| `palette` | (with `--palette`) a frame holds a colour outside the approved drawing's, `--effects`, `--shadow` and `--glow` | a resample or a per-cell quantise: map the whole sheet to one palette, clearing key fringe first; sub-pixel mid tones must come from the drawing's ramp; declare glow steps |
| `mark` | (with `--mark`) a mark missing on a frame, or its centroid jumping 2+ px in one frame, in the idle or the move (a warning elsewhere) | a small gem or lamp lost below `vanish`'s 8 px, or not moved with its part: paste it with its part, a pixel at a time |
| `reshape` | the face window (from 1 px behind the eye forward; `--facing`), aligned on itself, changes class (air, ink, colour) on over 10 % of its pixels per pose change on average, in the idle (a warning elsewhere) | a sheet or AI drawings redrawing the head in every cell, or block lines read per cell that merge a narrow snout column: draw the head once and paste one approved head at each drawing's place (placed by the eye), re-ink the seam; read every cell on one shared grid. A jaw opened on purpose in an action is a warning only |

A whole-figure bob of a pixel, a glow's pulse, a limb sweeping past, a wing coming back at the end of its stroke,
and tones too alike to tell apart are motion on purpose. The check aligns or ignores them. If one is reported, fix
the check, not the art (step 4).

## 2b. The later checks (warnings until fitted)

These were added from a review of animation guides (see [REFERENCES.md](REFERENCES.md)). Most margins are first
guesses from those sources; those of `orphans`, `speck`, `doubles` and `blend` were widened after a run on a set of
accepted textured creatures, whose own variation they had flagged. So they print `warn:` lines and never fail a
run. Rerun them on your accepted set, and raise a margin rather than redraw an accepted loop for one of them.

| Warning | Meaning | Usual cause, fix |
|---|---|---|
| `boil` | 2+ steps change only the outline (80 %+ inside the 1-px edge band, under a quarter of the median step) and come back a pose or two later, and they are a quarter of the updates or hide a real-pose rate under 10/s | AI or sheet frames redrawing every edge: a frame that changes only the outline is not a pose. Drop it, or thin a generated clip evenly (every 2nd or 3rd frame). A sub-pixel lead is small and edge-only too, but it settles into the move and never reverts, so it is not counted |
| `seam` | the pose at the loop's seam (the run crossing from the last frame to the first) held longer than every other pose, while all the others are held alike | the first pose copied to the end: a repeated last pose doubles a hold where the loop closes. Drop the last frame. A loop whose holds differ is not judged (an idle's rest may fall on the seam) |
| `skate` | in the move, a planted foot (a run of cells on the lowest row, matched pose to pose by overlap) slides 1+ px forward, or one foot's steps while planted differ by over 2 px | drawn walking in place, a planted foot goes back the same amount every pose until it lifts: the road's speed: the distance it goes back while planted divided by the frames it is planted, which equals the stride's length divided by the loop's frames. A foot drawn at a sine of the phase goes back, then forward again while planted. Near and far feet merge on small sprites: a contact with another within 2 px in either pose (feet splitting apart or merging) is not judged; judge per foot with `--parts` |
| `gait` | the move's body-top track does not bob twice a loop, or the move has an odd number of poses | a two-step walk rises and sinks once a step; an odd pose count cannot mirror its two halves. The bob's size is printed as a share of the height (sources give 3-8 %; a whole pixel is enough on a small sprite). Only a clear wave count is judged (every other count under 0.7 of it): a top row shifting a pixel at uneven times, as on a many-legged crawler, has none |
| `counter` | a declared strike: nothing (the eye or the leading edge) moves 1+ px against the strike before it | a still anticipation has no force: wind up the other way over 2-5 small poses |
| `strike` | the strike step (the biggest step carrying the lead forward; a second forward step over half of it joined) is under 3 times the anticipation's median step | the strike spread over even steps: strike in 1-2 frames, after small eased ones |
| `recover` | after a strike, or after a jump's landing, under 2 steps back to rest, or one over half the strike (the loop's biggest step for a jump) | snapping back: follow through, then return over 2-5 poses, steps growing then shrinking; a small overshoot is fine |
| `stage` | the strike's contact pose keeps 90 %+ of the rest pose's filled silhouette (effects included) | the key does not read: push it (a longer reach, a lower crouch). Every action prints its most changed pose's share as a read-out |
| `piston` | from the rest pose to the contact, the eye (or with `--parts` the farthest-travelling part's tip) strays under 1 px from a straight chord of 4+ px, over 3+ poses | a straight A-to-B slide: move the lead on an arc (the head rises, then drops into the bite) |
| `gravity` | an action whose figure's bottom rises 2+ px: airborne steps (px a frame) speeding up toward the apex, or a fall at an even pace | a jump spaced evenly: steps shrink on the way up, two drawings near the apex, steps grow on the fall |
| `squash` | in such an action, a pose changing height by 10 %+ narrows as it squashes (or widens as it stretches), changes its area by over 15 %, or stays deformed on the ground 3+ poses | squash wider, stretch narrower, keep the mass; a squash lasts 1-2 frames |
| `volume` | (with `--parts`) a part of 40+ px whose area leaves its median by over max(10 %, 2 px); `--squash` parts left out | a part scaled or cut differently per frame. Small parts are left out: a turned ear changes area by rasterising alone |
| `lag` | (with `--parts`) in the idle or the move, every part riding the body (off the ground, moving 0.75+ px, with the body's wave count) moves on the body's own frame, or one trails it by over a quarter of the loop | no follow-through: let the head, ears or tail come a pose late (one pose is enough at sprite scale). Without parts the eye's lag behind the figure's top is a read-out only: a whole-figure lift rightly gives 0 |
| `blend` | (a `--sheet` loop) a colour shown in under a quarter of the frames whose lightness lies between two tones it touches | a per-cell quantise or a resample: snap to the drawing's ramp, or declare a glow step with `--glow`. A rig turning parts a fraction makes such tones on purpose, so rigged loops get only the rare-colours read-out |
| `orphans` | a frame holds more lone pixels (matching none of the 8 round them; the eye and `--glow` left out) than twice the loop's usual count (its median, or the `--ref` drawing's if higher) plus 3 | stray pixels from a resample or a redraw. Compared with the loop itself: a shrunk texture holds many on purpose, and accepted loops vary up to 1.75 times |
| `speck` | a pixel steady in every bob-aligned frame takes a lone colour for 1-2 frames once a loop, while its 8 neighbours keep theirs, 60+ of lightness from its own colour and every neighbour, and lighter or darker than all of them (a tone between two neighbours, as between an outline and its fill, is an edge blending) | a glaring blinking speck (`shimmer` needs a flip on a sixth of the frames): clean it |
| `doubles` | a frame's outer outline holds more doubled cells (2x2 blocks, L-clumps) than twice the loop's usual count plus 2; the new places are named | an outline thickened by the shrink or re-inked on a turned part: thin it to one pixel. A leg or wing turning at a joint makes some on purpose |
| `drift` | (with `--ref`) the idle's nearest pose, after the best shift, differs from the approved drawing on over 2 % of it | the rest render drifted from the drawing: a part cut, a pivot off, a colour snapped differently |
| `swap` | (a `--sheet` loop) a colour group of 8+ px drops under 30 % of its median, or doubles, in one step for 1-3 poses and comes back in one step | an AI sheet dropping a shield or moving a sword across for a cell: keep every part on every cell. A foreshortening wing passes through the counts between and is not caught |
| `split` | from one pose to the next, the torso's topline or belly line moves by different amounts on the two sides of one column, each side rigidly over 30 %+ of the torso, with a 1-px step where the drawing's line is level. The torso is the band of the fullest rows, the columns filling it with nothing above them, the head and neck's end left out; a flier is not read | the rear band riding the hips and the front band the shoulders, a pose apart: keep the torso one piece; bend it over its whole length (a shear or a curve), turn it whole about a pivot, or let a 1-px step fall where the line already slopes |
| `hitch` | the head (the eye's track), or a `--parts` part of 40+ px, holds still 10+ frames at 30 fps, then steps a pixel or more as one block while the rest of the figure changes under half as much on that frame. A step back within 3 frames is `tick`'s; an action's held key may end in a step | a head nodded in slow whole-pixel steps with nothing else moving: carry it on the neck as a chain (neck first, the head a pose later, the ears after), on the body's beat with a short period; turn it a little so the change spreads; or move other parts on the same pose |

Not checked, on purpose: smears (an option, and good strikes exist without one), the figure touching the cell edge
(a loop cropped to one union box touches it in some frame; a cut reach shows as `outline`), footfall order (diagonal
pairs land together in a trot, and contacts merge on small sprites), a flier's rise and fall timing (wing pixels
change on both strokes), hit reactions (one source, nothing to fit on) and effect timing (a spark starts at full
size on purpose; a breath of fire lasts long on purpose).

## 3. Look at it yourself

First read the two tracks the run printed, before the GIF. A fault shows there before it shows in a GIF:
- **The eye's row track** (`(row, frames)` runs): a level reached for 2-3 frames and left (a tick), or a square wave
  dwelling under 4 frames. Each level the eye takes should last 4+ frames at an extreme (3 on a smooth path).
- **The per-step change list**: a long run of zeros followed by a big step (a dead stop, then a lurch); a lone
  doubled hold among even ones (a dropped update); steps alternating big and small (a lurch).
- **The later read-outs**: a real-pose rate well under the update rate (boil); a box whose height or anchor swings
  more than 1 px with no design behind it (a sheet's cells scaled or anchored apart: anchor walkers by the feet,
  fliers by the body's centre); the planted feet's speed against the road's (`--speed`).
- **The closing step** (the move's step from its last frame to its first, against its median moving step): clean
  walks and wing beats here read 0.78-1.32; a 16-frame walk cut at 13 frames reads 1.64, at 11 frames 2.11. Over
  about 1.5 the loop's end does not meet its start (cut short, or a pose missing at the seam). It is a read-out, not
  a warning, since the margin is narrow; an idle may close on an accent and read higher.
- **The bob against the legs** (`legs widest at frame ..., body lowest at frame ...`): in a two-legged walk or a
  trot the body is lowest about where the legs are widest (the contact) and highest where they are narrowest (the
  passing pose). The two the other way round is a bob drawn upside down. A four-legged lateral walk's leg band does
  not follow the step, so there read the GIF instead.
- **A walk pose out of order** is not caught: every walk step already changes a third of the figure or more, so a
  misplaced pose does not stand out from its neighbours (`jump` reads 1.3-1.5 against 3.6), and no measure tried
  told it apart from a clean loop whose wing passes the same drawings down and up. Find it on the contact sheet:
  the poses should progress, each between its neighbours.

If you have a part strip, look at it first, at 1x: the motion should read on the flat colours before the texture
goes on. With `--speed`, watch the move over the GIF's scrolling ground line: a planted foot must not slide on it.

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
- For the later checks it passes, with no fault and no warning of theirs: the walker on twos and on threes, its
  idle swaying 2 px over 12 poses, a bite (a strike on threes with one 9-frame key) and a leap (a jump with one
  6-frame key) declared as actions, the walker with its part strip, against its palette and its drawing, with a gem,
  and with a patch read as a sheet, and the flier read as a sheet. It then breaks them: a held pose knocked 3 px on
  twos and 2 px on threes, a planted foot nudged forward, the bite left undeclared (`choppy`), a bite with no
  wind-up, one spread over even steps, one snapping back, one barely changing shape, one on a straight line, a leap
  falling evenly, one narrowing as it lands, one landing straight to rest, a boiled sheet, one bob a loop, an odd
  pose count, a head riding the body with no lag, a part shrinking a row, a torso cut into two bands, a head stepping alone after a long hold, a stray colour, a blend, a blinking speck,
  scattered lone pixels, a doubled outline, a drawing with its snout cut, a gem lost and a gem jumping, a patch
  dropped for a cell. Each must be reported as its own fault or warning.
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
