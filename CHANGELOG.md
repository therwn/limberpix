# Changelog

All notable changes to this project are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Codex.** Both skills now carry `agents/openai.yaml` (name, one-line description, starting prompt) and say how
  Codex reads the scripts' folder; they pass Codex's skill validator as they are. The README and docs/usage.md give
  the install line for Codex's skill installer and the folder for a plain copy.
- **A gallery.** `examples/showcase/make_gallery.py` builds `docs/img/gallery/`: each showcase loop and each
  selftest creature as its own GIF, pixel-animate's four steps on the wolf (the drawing, the cut, a pose as parts,
  the frame), and four faults made by breaking the wolf's frames, each with the line the check printed.
  `examples/README.md` shows every example with its pictures and commands, and the README opens with them.

- **pixel-anim-check** `--eye-at X,Y`: the eye's place on each loop's first frame, for a sprite whose eye colour is
  used elsewhere too. The eye was taken as the biggest piece of its colour; on a hand-drawn wizard sheet two eyes a
  pixel apart are two 1-px pieces and a 2-px bead on the staff won, so the eye track, `frozen` and `reshape` followed
  the bead. The note naming the piece now says how to name another. With a selftest case.
- **Docs, from a test against a hand-drawn sheet** (a cloaked wizard; cut-out loops made from its first frame and
  judged by one viewer against the sheet's own): both skills now say that a fault count is not a verdict on the
  motion; pixel-animate says to check first whether the drawing holds what the loop needs (cloth that changes shape
  and a body that turns need new drawings) and how to mark a hand gripping a prop; pixel-anim-check says what
  `--effects` does to a colour the figure wears, that a one-shot is read as a cycle, that `choppy` and `stepped` turn
  on the assumed frame rate, that a partly lined drawing fails `outline` on every frame, and that a hand-drawn idle
  its viewer accepted gets `stepped`. docs/usage.md lists these under Limitations and Troubleshooting, and the README
  says a copied skill does not update itself.
- **README** laid out as the repo's front page: a header with the icon and badges, the two skills side by side at a
  glance, the faults in one folded table, and a section on what the method suits and what it does not. The "not yet
  published" note is gone: the plugin install lines need the repo public.

- **pixel-anim-check** `--style redrawn`, for animations whose every pose is a new drawing of the whole figure (frame
  by frame, or generated). `stepped` replaces `choppy`, `uneven` and `lurch`: the whole body must move at least 6
  times a second, a new pose changing 40 % of the figure's tiles. `shimmer` is off and `reshape` and `outline` only
  warn. The margin is a first guess from three idles of one character judged by playing them (a generated idle
  accepted, two cut-out idles rejected as slow and stepped); the default style is unchanged. Two faults for
  generated frames run in this style: `lostmark`, marks closed in by a patch of one colour (a mouth on a face) gone in
  3 or more separate runs of poses, which named exactly the four poses the reviewer saw without a mouth; and `gaps`,
  an outline broken in short stretches. Neither fires on the 21 other loops in the repo and the trials when their
  outline colours are given. With selftest cases. A first `flicker` warning (a mark both neighbouring poses draw,
  missing in this one) was dropped: it marked none of the places the reviewer saw.
- **pixel-anim-check** `--spots PATH` (with `--ref`): small marks of the approved drawing placed by eye in groups (a
  hat's specks, a mouth), looked for at their place in every pose of every loop but an action; the `spots` fault
  names the poses showing fewer of a group's marks than the drawing. A mark that turned another colour or into a
  pinhole still counts. On the reviewed generated idle it named exactly the poses the reviewer saw lose a hat speck
  and the mouth (32 judgements of 32), where `lostmark` could not see the specks. With selftest cases.

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

- **pixel-anim-check** `--min-rate R` (`Spec.min_rate`): `choppy`'s floor for the idle and the move, in updates a
  second, for a style held longer than the fitted floors allow (the blog's 8-16 px sprites hold a pose 200-800 ms).
  A value that is no number over 0 is a usage error.

### Changed

- docs/usage.md: the showcase table had frame counts and a frame height the strips no longer have (beast 60/32/40 at
  93x52, bird 72/32/54, lizard 60/32/34); the "not yet published" note is gone.

- **Showcase** re-timed for smooth motion. The idles were a ripple of 1-px steps, one part a pose after another (the
  trunk, then the neck, then the muzzle, then the ears), so they read as clicks. Each idle is now one breath of 8
  poses held 3 frames over the rise and the top and 2 on the drop (Pixelblog 52), the trunk, neck and head moving as
  one piece and the follow-through going to a free tip (the tail). The wolf walks on ones, its planted paws moving a
  pixel a frame with the road. The bird's feet tuck behind the belly a stage a pose instead of vanishing, and its far
  wing leads the upstroke, so the two wings are never hidden at once. The lizard's far legs are its near legs a
  value step darker, standing just behind them, instead of two legs drawn between them. In the attacks the wolf's
  neck no longer bends row by row when the head is carried off (its ruff slid over the shoulder as a light stripe):
  it moves whole with the head over its own fur at rest, the near foreleg's bare pixels kept over it, and the
  wound-up head sinks with the body; the lizard's held key no longer settles its back alone under a still neck.
- **pixel-animate** method: a new MOTION.md 3.0, after Slynyrd's Pixelblog (the text of its 91 posts read, animation
  taught in about 25; the GIFs of 20 measured): the body's mass moves on every pose and no small part steps alone;
  further from the body, more pixels a pose; parts joined by a seam move as one piece at 1-px steps, the lag going to a
  free tip; ease by timing (slow over the top, quick on the drop) and by step size; a planted foot moves with the ground
  every frame; hold lengths and frame counts as measured. SKILL.md's default rules say the same; 3.3 and 3.10 no longer
  ask for a part to move while the body holds; 3.5 keeps the two wings from thinning at once and tucks feet in stages.
  Sources in REFERENCES.md.
- **pixel-anim-check** rules that forced the clicking: `frozen` reads the frames as drawn (a head carried whole on the
  body's rise moves); `hop` counts a whole-body shift only when air opens above the contact (legs stretching under a
  risen trunk are a breath); `uneven` and `lurch` no longer judge an idle that breathes (its body moving whole, its
  other pose changes small; a breath is eased on purpose); `lag`'s "no follow-through" warning asks for it only where
  the body steps 1.5 px or more; `choppy` lets an idle whose every pose moves the whole body (the top of 80 %+ of its
  columns shifting) update 2.5 times a second and hold one pose twice the others, as Slynyrd's idles do (200, 200, 400
  ms). Judged on this repo's showcase by one person; not rerun on the private calibration set.
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
- **pixel-anim-check** `choppy` lets a move whose every pose change is big (8 %+ of the figure, a new drawing of the
  stride) update 5.2 times a second: Slynyrd's walks hold a pose 100-280 ms (25 and 50, 8 × 140 ms; 50's six poses 200,
  180, 180 ms, measured from the GIFs), and four clean walks of the selftest at 120-200 ms a pose failed before. The
  private set rejected four walk drawings held 6 frames (5 a second), so the margin is narrow (5.0 to 5.4). A move
  stepping one part over a still body keeps 10.
- **pixel-anim-check** a declared action may hold two keys (the wind-up and the follow-through), each up to 13
  frames at 30 fps, the second at least twice the other holds' median; `jump` forgives a whole-figure 1-px step
  sideways in a declared action (the overshoot: the rest pose a pixel back for a frame). Slynyrd 56's sword, spear
  and hammer (100-300 ms holds, 20 fps) faulted `jump`, `uneven` and `choppy`; they are now clean of faults. Their
  `counter`, `strike`, `recover`, `stage` and `piston` warnings stay: the strike checks ask for the multi-pose
  pattern, and pixel-anim-check's SKILL.md says why they show.
- **pixel-anim-check** `uneven` and `lurch` judge an idle again unless it breathes: an idle whose body stands while
  its head and tail step at 1 and 3 frames in turn is `uneven` (it passed after the idle was let off). The five
  checks relaxed for the showcase each state in their docstring what they no longer catch, and the selftest's
  `relaxed_bounds` holds both sides: a head pasted in place while the body moves (`frozen`), an idle moving its
  whole body 2 times a second (`choppy`), a body lifted off its feet's row (`hop`), a walk bobbing 2 px with every
  part on one frame (`lag`, a warning) are still caught.
- **pixel-animate** attributions: every rule credited to the blog says whether its number is in the post's text or
  measured from its GIF. Five claims first read off the GIFs were measured again, part by part by colour: 24's cherry
  bob (0, -1, -3, -5, -6 px at 80 ms), 37's bat (each wing pose 160 ms while it moves 2 px every 40 ms) and 60's dummy
  (head and torso two poses at each level, the legs changing every pose) held; 25's dog moves its tail with the hips on
  the same poses (it trails only sideways, a pose later), 25's bird's wing tip travels 23 px, and 8's plume drops with
  the body and rises one or two poses after it. A tail root lagging a pose and damped, and a tip coming down late, are
  this repo's preference. 60's 8 × 90 ms loops are the run, not the 60 ms of the text. The rule "the body moves on every
  pose, never a small part alone" and the seam rule are credited to this repo's showcase (one person's judgment), the
  blog doing otherwise in places (55's hair, 33's leaves, 39's still idle). The steps that staged a move part after part
  (3.8's idle layers, SKILL.md's heads and ears, the `hitch` advice) are rewritten to carry the part with the body.
- **pixel-animate** MOTION.md gains Slynyrd's attack pattern beside the multi-pose one (one held anticipation
  frame, a 1-3 frame smear, the follow-through held, one recovery frame, the overshoot) with the sword, spear and
  hammer timings and when to use which; no anticipation on a jump the player controls (60); quadruped footfall
  (25, 64) beside the existing order; a walk's four poses (50, 60); the wave rule (33); the blog's idle options
  (8, 36, 39: "an idle never stops dead" is this repo's choice); effect timings (36, 45, 48); noise (58), linked
  from `shimmer`. These thresholds were not rerun on the private 39-creature set; rerun it before a release.
- **pixel-anim-check** `jump`'s sideways test (`_best_dx`) shifts frames with air let in at the edge (`_sh`), no
  longer wrapping round: a band touching both edges with its scales scrolling 2 px a pose gave 8 false `jump` faults
  and now gives none, while the same band with a pose pushed 4 px sideways is still caught (the selftest's
  `edge_band`). Nothing else in the selftest, the examples or the showcase changes.
- **Examples** `examples/fighter/`: a fighter drawn at game size from a skeleton and its idle built the Pixelblog 52
  way; it checks clean (0 faults, 0 warnings), and CI checks that.
- Docs: what the check does not catch, and is looked for by eye, is written once with its measured numbers, in
  `docs/usage.md`'s Limitations and pixel-anim-check SKILL.md section 2b: a walk pose out of order, a texture redrawn
  at random on twos or threes, one 4-frame hold among twos, a bob drawn upside down (tried again with part strips:
  the clean walks read +0.53, -0.03 and -0.24 against -0.71 upside down, so no check was added) and `shrink.py`'s
  small moves. REFERENCES.md describes Astropulse's K-Centroid from its own page (k-means per tile, 2 centroids and
  3 iterations by default).

### Changed (pixel-anim-check)

- **`--style redrawn` warns on motion, and faults on lost character.** `stepped`, `frozen`, `stiff`, `snap`, `tick`,
  `hop`, `shallow` and `still` are warnings in this style; the faults are the frames that lose the character
  (`lostmark`, `spots`, `gaps`, `eye`, `apart`, `palette`, `mark`, `vanish`, a pose knocked sideways or off the
  ground). The motion a model gave is judged by playing the loop, and no repair here changes it.
  docs/ROADMAP.md says where this goes: finding and repairing what generated sheets lose.

### Fixed

- **pixel-anim-check** `vanish` no longer depends on the loop's first frame. A whole-figure lift was taken out
  against frame 0, so a loop started inside a far wing's hidden stretch was aligned against the gap and the vanish
  went unseen (an idle of 19 frames: missed from 6 of its starts). The lift is now taken out against the pose the
  loop shows most often. A part going and coming back, read as two events of equal weight, is reported going, so
  the start no longer picks which. A vanish at the last-to-first step names frame 0, not frame n, and the contact
  sheet frames it.
- **pixel-anim-check** a loop's name holding "frame 12" no longer marks frame 12 on the contact sheet drawn from
  `check()`'s lines.
- **pixel-anim-check** an empty frame no longer hides the loop's other poses from `--spots`: they are still read,
  and a mark outside the approved drawing is still refused. Selftest cases for all three.

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
