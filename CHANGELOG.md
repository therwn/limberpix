# Changelog

All notable changes to this project are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **pixel-animate** `shrink.py`: brings a frame posed at the reference's resolution down to game size, the step the
  skill named but did not specify. A game pixel is drawn on coverage, the contour is read apart so a thin line stays
  whole and one pixel wide, and the fill is voted after every reference pixel is snapped to the palette; a cell is
  never averaged. `--colours N` makes the rest frame's palette, which every other frame then takes. With
  `shrink_selftest.py`, a CI step, and the measurements and sources in the skill's `REFERENCES.md`. Documented in
  `docs/usage.md` and the README.
- **pixel-animate** section 2 now opens with the choice of way: a drawing already at game size is posed at that
  size (whole-pixel places, limbs bent row by row between joints, the body moved whole or stretched in column steps,
  turns by three shears, the outline drawn last), as `examples/showcase/` does; a large painted reference is posed
  at its own resolution and shrunk.
- **pixel-anim-check** `seam` warning: the pose at a loop's seam held longer than every other, all alike (the first
  pose repeated at the end). A read-out gives the move's closing step against its median moving step.
- **pixel-anim-check** `--key #rrggbb`: the background colour of a strip with no transparency, read as air in the
  loops, `--parts`, `--ref` and `--palette`. Without it, a loop with no transparent pixel in any frame is a usage
  error (exit 2).
- **pixel-anim-check** `eye` also faults the eye jumping out of its head's box in one frame in the idle or the move
  (a warning elsewhere): a mirrored or misplaced cell, or the eye lost while its colour shows elsewhere. A `note:`
  names the piece read as the eye when the first frame shows the colour in several.
- **pixel-anim-check** `ground` warns when a legged walker's lowest drawn row moves in the move (a whole-figure
  lift; a run leaves the ground on purpose, so it is not a fault).

### Changed

- **pixel-anim-check** `jump`: the step ratio is now read against the loop's usual step, the mean of its moving
  steps with the two biggest left out, since a pose out of order makes two big steps. Before, a loop of 6 moving
  steps or fewer could never fire, and one of 8 only at 12 times its other steps. A declared jump's launch and
  landing are left out first, like a strike's own step. With under 4 usual steps a change must also reach a quarter
  of the figure. `JUMP` goes from 3.2 to 3.6, fitted on this repo's 13 clean loops and its broken example only; the
  message reads `against a usual N`.
- **pixel-anim-check** `shimmer` counts a pixel only when it flips at least 3 times a loop, and the eye `tick`'s
  dwell (3 and 4 frames at 30 fps) scales with `--fps`. A clean loop thinned to every 2nd frame at 15 fps, or every
  3rd at 10, no longer fails `shimmer`.
- **pixel-anim-check** `--idle NAME` or `--move NAME` naming no given loop is a usage error (exit 2). With no loop of
  the default name and no option given, a `note:` line says which checks do not run.
- **pixel-animate** `body_parts.py` checks the landmarks file before cutting: a part that is not an object, a bone
  missing, empty or of nulls, a point that is not two numbers, a kind that is not text, a parent naming no other
  part, or an eye that is not two numbers or null is a usage error (exit 2) naming the part, not a traceback.
- The three scripts name the fix when numpy or Pillow cannot be imported (`python -I` does not see a
  `pip install --user`); the SKILL.md files, the README and `docs/usage.md` explain it.
- **pixel-anim-check** `shimmer` reads each pixel's runs of one tone: a tone shown 0.1 s at most and gone back
  counts, so a texture crawling on drawings held on twos or threes is caught (it was not). The stroke-turn exception
  is read on the distinct poses.
- **pixel-anim-check** `choppy` leaves a rest (a hold of a third of the loop) out and judges the rest of the loop;
  before, any rest excused the whole loop.
- **pixel-anim-check** one eye finder for every check (`frozen`, `reshape` and the action checks took the mean of
  every pixel of the eye colour): the colour used elsewhere no longer moves the head's box.
- Thresholds added or changed in this release were measured on this repo's loops only, not on the private
  calibration set: rerun them there before release.
- Docs: `MOTION.md` gives the road's speed as the planted foot's travel over its planted frames (the stride over
  the loop's frames); the hold rule is about the tempo (a usual hold of 4+), with one longer hold only where the
  motion stops; the bird and bat wing-drawing rule is set apart from insects; the closing-step rule is for
  continuous loops, with the measured range. pixel-anim-check's SKILL.md and `docs/usage.md` say what the check
  does not see (a texture redrawn at random on twos, one 4-frame hold among twos, a walk pose out of order, a bob
  drawn upside down).
- Docs: corrected numbers in `MOTION.md` (a chain's 1-3 frames are 10-30° of a 36-frame loop; 0.17 at A = 0.58;
  the strike against the median anticipation step) and in the docstrings of `tick`, `frozen`, `split`,
  `ink_lines` and `spine`; `tick`'s SKILL.md row says which lift peaks its body check lets through.

## [0.1.0] - 2026-11-21

First public release.

### Added

- **pixel-animate** skill: a method for animating pixel-art creatures from one approved drawing. It covers planning
  the loops, cutting a rig, posing at full size on one fixed grid, motion that reads in pixels, sprite sheets with few
  drawings, and checking before showing.
  - `body_parts.py`: cuts a drawing into rig parts from rough bones placed by eye, following its own ink lines and
    colour edges. Writes an overlay, a JSON of parts with pivots and outlines, and a label image. `--grid` writes a
    labelled grid for reading coordinates. A `null` in a bone breaks it into pieces. Exits 1 when it prints
    `CHECK:` lines. Made sound on real art before release: a dark body tone close to the background stays figure
    (background must also touch the border); the labels are grown back over every figure pixel at full size; a
    colour patch shared by two parts is no longer voted wholly to one; dark cloth is not taken for an ink line.
    Joints and shading: a part never grows behind its joint (its bone's first point) or sideways along it past its
    own width, and a parent never crosses into a child past it, wherever the drawing gives no edge; a lightness step
    within one hue is shading, not an edge; a thin strip a part reached round a gap along another part's edge goes
    back to that part (a `moved:` line); a part's width stops at an ink line and it does not reach far past it (a
    near leg keeps off the far one, a jaw off the throat); a part inside its parent (a jaw in the head) is marked
    `inside` and drawn hatched inside it; an eye point outside every head part is a `CHECK:`. The selftest adds a
    shaded beast and a hand with thin fingers, as placed and with careless bones.
  - `creature_map.py`: a first look at a body plan from the silhouette alone. Refuses a strip of frames.
  - Selftests for both tools.
- **pixel-anim-check** skill: `pixel_anim_check.py` finds 20 kinds of animation fault (size, empty, apart, eye,
  outline, ground, jump, still, shimmer, frozen, stiff, choppy, uneven, lurch, snap, tick, hop, vanish, shallow,
  reshape). It prints the per-step change list and the eye's row track, and writes a contact sheet (each pose
  labelled with its frames, the faulted ones outlined) and a GIF. It reads strips, frame folders and GIFs (at their
  own timing). Exit codes: 0 no fault, 1 faults, 2 a usage error.
  `pixel_anim_selftest.py` breaks a clean walker and flier in every one of those ways and checks that each break is
  caught.
- Claude Code plugin and marketplace manifests (`/plugin marketplace add therwn/limberpix`).
- `examples/` with clean and broken strips and a body_parts figure, all generated from the selftests' creatures.
- `examples/showcase/`: three original creatures (a young wolf, a kingfisher-like bird and a chameleon-like lizard)
  drawn by hand as data, with hue-shifted ramps, form shading and texture, and animated by the skills' rules from
  their one drawing: an idle, a move to be shown over a road scrolling at each one's `ROAD_SPEED`, and an attack (a
  lunge and bite, a dive strike, a tongue strike), all passing pixel-anim-check with 0 faults and 0 warnings under
  the full options (`--action`, `--parts`, `--palette`, `--ref`). `make_showcase.py` checks them and builds the
  README's pictures from them, all text in its own pixel font.
- A short README; the full reference is in `docs/usage.md`.
- Rules and checks learned from public pixel-art animation guides (sources in each skill's REFERENCES.md):
  action phases (anticipation, strike, recovery), jumps and landings, planted feet that do not slide, walk bobs,
  follow-through lag, smears, arcs, staging, layered idle periods, effect timing. New faults `palette` and `mark`;
  `jump` now catches a pose held on twos knocked sideways; new warnings `skate`, `gait`, `boil`, `counter`,
  `strike`, `recover`, `stage`, `piston`, `gravity`, `squash`, `volume`, `lag`, `blend`, `orphans`, `speck`,
  `doubles`, `drift`, `swap`, `split` (a torso moved as two bands with a 1-px step between them) and `hitch` (a
  head or part stepping 1 px alone after a long hold), with options `--action`, `--speed`, `--parts`, `--squash`, `--palette`, `--ref`,
  `--glow`, `--mark` and `--sheet`.
- CI on Ubuntu and Windows with Python 3.9 and 3.12, Python 3.8 on Ubuntu 22.04, and a NumPy 2 job that treats
  deprecation warnings as errors.

[0.1.0]: https://github.com/therwn/limberpix/releases/tag/v0.1.0
