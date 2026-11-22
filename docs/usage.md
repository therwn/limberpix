# Using Limberpix

The full reference for the two skills and their command-line tools. The [README](../README.md) has the short version.
Every command here runs from the repo root, and each is one line, so it pastes into bash, PowerShell and cmd alike.

- [Requirements](#requirements)
- [Install](#install)
- [In Claude Code](#in-claude-code)
- [pixel-anim-check](#pixel-anim-check)
  - [Command and exit codes](#command-and-exit-codes)
  - [Options](#options)
  - [Inputs: strips, frame folders, GIFs](#inputs-strips-frame-folders-gifs)
  - [Faults](#faults)
  - [Example runs](#example-runs)
  - [The showcase creatures](#the-showcase-creatures)
  - [Sample output, explained](#sample-output-explained)
  - [From code](#from-code)
- [pixel-animate tools](#pixel-animate-tools)
  - [body_parts.py](#body_partspy)
  - [creature_map.py](#creature_mappy)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Requirements

- Python 3.8 or newer (CI runs 3.8 on Ubuntu 22.04, and 3.9 and 3.12 on Ubuntu and Windows).
- numpy >= 1.21 (1.x and 2.x) and Pillow >= 9: `python -m pip install -r requirements.txt`.
- Claude Code, if you want Claude to use the skills. The scripts also run on their own.

Both skills work with any engine or art tool: they read and write plain PNGs and GIFs.

## Install

> **Not yet published.** Until the `therwn/limberpix` repository and its v0.1.0 release are public, the GitHub
> commands below (and the README's badges) do not resolve. Meanwhile, install from a local copy of this folder:
> `/plugin marketplace add <path to this folder>`, then `/plugin install limberpix@limberpix`.

**1. As a Claude Code plugin (recommended).** Inside Claude Code:

```
/plugin marketplace add therwn/limberpix
/plugin install limberpix@limberpix
```

Plugin skills are namespaced, so they show up as `limberpix:pixel-animate` and `limberpix:pixel-anim-check`.

**2. As plain skills.** Copy the skill folders into your personal skills folder, or into one project's:

```bash
git clone https://github.com/therwn/limberpix
cp -r limberpix/skills/* ~/.claude/skills/          # every project
# or: cp -r limberpix/skills/* <your project>/.claude/skills/
```

On Windows PowerShell: `Copy-Item -Recurse limberpix\skills\* $HOME\.claude\skills\`.

**3. Only the command-line tools.** Clone the repo and run the scripts with Python:

```bash
git clone https://github.com/therwn/limberpix
cd limberpix
python -m pip install -r requirements.txt
python skills/pixel-anim-check/pixel_anim_check.py --selftest
```

## In Claude Code

You do not need the commands. Ask for the work, for example "animate this fox's idle and walk from fox.png", or
"check walk.png before I put it in the game". Claude loads the right skill, runs the scripts and looks at the
pictures they write.

- **pixel-animate** is a written method, not a generator. It covers how to plan the loops before drawing, how to cut
  the reference into parts (a rig), and how to pose the parts at full size and shrink every frame on one fixed grid.
  It also sets out the motion principles that read in pixels: whole-pixel steps, holds against crawl, the moving
  hold, lift without ticks, wings, legs, snakes, heads, chains and seams. A section covers sprite sheets with few
  drawings (hand-drawn or AI-made), and every loop ends with pixel-anim-check. Claude uses it when you ask it to make
  or remake a sprite animation, to choose how a creature attacks, or when you say an animation looks stiff, broken,
  or unlike its drawing. The method itself is in [`skills/pixel-animate/SKILL.md`](../skills/pixel-animate/SKILL.md).
- **pixel-anim-check** runs `pixel_anim_check.py` on every loop of a creature and reports faults by name. It also
  prints two read-outs, the per-step change list and the eye's row track, and writes a contact sheet and a GIF. The
  skill then has Claude inspect them by eye for what numbers cannot see: likeness, seams, life in every part, and
  rhythm. Claude uses it whenever a sprite animation is made or changed, and before one is shown to anyone. The
  steps are in [`skills/pixel-anim-check/SKILL.md`](../skills/pixel-anim-check/SKILL.md).

## pixel-anim-check

### Command and exit codes

```
python skills/pixel-anim-check/pixel_anim_check.py --loop NAME=SRC [--loop NAME=SRC ...] [options]
python skills/pixel-anim-check/pixel_anim_check.py --selftest
python skills/pixel-anim-check/pixel_anim_check.py --help
```

**Exit code:** 0 no fault, 1 one fault or more, 2 a usage error (a bad option, a missing file, a strip that does not
cut into whole frames).

### Options

| Option | Meaning |
|---|---|
| `--loop NAME=SRC` | a loop: a horizontal strip PNG, a folder of frame PNGs, or a GIF |
| `--frame W` / `--frames N` | a strip's frame width, or its frame count (with neither, square frames; a strip that does not cut evenly is refused) |
| `--eye #rrggbb` | the eye's colour: checked on every frame, its row track printed |
| `--flier` | it flies: its shadow must not slide, its body height is read for ticks |
| `--shadow #hex,...` | a flier's ground-shadow colours (required for a flier with a shadow) |
| `--ink #hex,...` | the outline colours (default: every colour darker than lightness 40) |
| `--effects #hex,...` | colours of effects drawn apart from the figure on purpose |
| `--allow LOOP=N` | pieces up to N px may sit apart from the figure in that loop (a thrown coin) |
| `--glows-eye LOOP` | the eye is recoloured by a glow in that loop, so it is not checked there |
| `--idle NAME --move NAME` | which loops are the rest and the travel loop (default `idle`, `move`) |
| `--legless` | a snake or slug: no body rise asked of its move |
| `--facing right\|left` | which way the head faces (default right) |
| `--fps N` | the rate the game plays the loops at (default 30; a decimal is allowed) |
| `--out DIR` | where `<name>_check.png` and `<name>_check.gif` go (default `.`, the current folder) |
| `--name NAME` | the stem of the written files (default `anim`) |
| `--action NAME[:KIND[:DIR]]` | that loop is an action: one key may be held up to 13 frames. `strike` (with a direction) has its phases judged; `jump` is not asked to keep to the ground |
| `--speed PX` | the road's scroll in game px a frame: the planted feet's speed is printed beside it, and the GIF scrolls a ground line under the move |
| `--parts LOOP=PATH` | a part strip for that loop (the same frames, each rig part one flat colour): per-part volume and lag are judged on it |
| `--squash #hex,...` | part colours whose area changes on purpose (wings, a squashed body) |
| `--palette PATH` | the approved drawing: every frame must keep to its colours |
| `--ref PATH` | the approved drawing at game size: the idle's nearest pose must match it |
| `--glow #hex,...` | colours shown in some frames on purpose (glow steps, glints, blink lids) |
| `--mark #hex,...` | small defining marks (a gem, a lamp): on every frame, never jumping 2 px in one frame |
| `--sheet LOOP` | that loop was drawn as a sheet or by AI: a part switched off for one cell is looked for |

Colours are `#rrggbb` in any case, the `#` optional.

### Inputs: strips, frame folders, GIFs

Every frame of every loop must be the same size, with the figure kept in place rather than trimmed per frame.

- **A strip** is one horizontal PNG. Give `--frame W` or `--frames N`; with neither, square frames are assumed.
- **A frame folder** is read in file-name order, so zero-pad the numbers (`f00.png`, `f01.png`, ...): otherwise
  `f10.png` comes before `f2.png`. `--frame` and `--frames` do not apply to it.
- **A GIF** is read at its own timing. The checker rounds elapsed playback time to game frames at `--fps`.
  Ten 50 ms poses cover 15 frames at 30 fps. To judge one
  image per game frame regardless of its duration, give a strip or a frame folder instead.

### Faults

`size`, `empty`, `apart`, `eye`, `outline`, `ground`, `jump`, `still`, `shimmer`, `frozen`, `stiff`, `choppy`,
`uneven`, `lurch`, `snap`, `tick`, `hop`, `vanish`, `shallow`, `reshape`, and with their options `palette` and
`mark`. Warnings (`warn:` lines) add `skate`, `gait`, `boil`, the action checks, `split` (the torso moved as two
bands with a 1-px step between them), `hitch` (the head or a part stepping 1 px alone after a long hold) and more;
`--help` lists them all.
Each fault, with its usual cause and fix, is
in the table in [`skills/pixel-anim-check/SKILL.md`](../skills/pixel-anim-check/SKILL.md#2-what-each-fault-means-and-the-usual-fix).

### Example runs

The files in [`examples/`](../examples) are small creatures drawn by `examples/make_examples.py`. The walker's frames
are 34 px wide, the flier's 30 px, and both have the eye `#ffcc33`.

The clean walker:

```
python skills/pixel-anim-check/pixel_anim_check.py --loop idle=examples/walker_idle.png --loop move=examples/walker_move.png --frame 34 --eye "#ffcc33" --out out --name walker
```

It prints `walker: 0 fault(s)`, exits 0, and writes `out/walker_check.png` and `out/walker_check.gif`.

The same walker with one move frame knocked 4 px sideways:

```
python skills/pixel-anim-check/pixel_anim_check.py --loop idle=examples/walker_idle.png --loop move=examples/broken_move.png --frame 34 --eye "#ffcc33" --out out --name broken
```

It prints two `jump` faults around frame 8 and exits 1.

The flier, which casts a ground shadow:

```
python skills/pixel-anim-check/pixel_anim_check.py --loop idle=examples/flier_idle.png --loop move=examples/flier_move.png --frame 30 --eye "#ffcc33" --flier --shadow "#2b2430" --out out --name flier
```

It prints `flier: 0 fault(s)`. A flier's shadow colours must be given with `--shadow`, or the shadow counts as a
stray piece: without it the same run reports 41 faults (40 `apart` and one `vanish`).

### The showcase creatures

[`examples/showcase/`](../examples/showcase) holds the three creatures in the README's pictures, each made by the
pixel-animate method and passing the check with 0 faults and 0 warnings: a young wolf (`beast`, a four-legged
walker), a kingfisher-like diver (`bird`, a flier) and a chameleon-like lizard (`lizard`, a low walker with a tongue
strike). Each folder has the drawing as data (`creature.py`, every pixel placed by hand, each moving part its own
layer), the rig that poses the parts (`*_rig.py`, with `bird_wings.py` and `bird_heads.py` for the bird's drawn keys
and `lizard_legs.py` for the lizard's legs), `animate.py`, which rebuilds the strips, the drawing at 8x
(`*_art_8x.png`) and three loops at 30 fps, every pose held 2 frames:

| Creature | Frame | Idle | Move | Attack | Road speed |
|---|---|---|---|---|---|
| beast | 93x53 | 72 frames | 32 frames | 39 frames, a lunge and a bite | 1.0 px a frame |
| bird | 86x69 | 72 frames | 32 frames | 56 frames, a dive strike | 1.0 px a frame |
| lizard | 113x40 | 64 frames | 32 frames | 34 frames, a tongue strike | 0.5 px a frame |

The move is drawn in place, to be shown over a road scrolling at the road speed (`ROAD_SPEED` in each `animate.py`):
a planted foot goes back at that speed (the check prints the two side by side). `animate.py` also writes the check's other inputs into the
creature's `check/` folder: a part strip for each loop (each rig part one flat colour), the drawing at game size and
its palette. Each `animate.py` docstring ends with the creature's full check command. The beast's, from the repo
root:

```
python skills/pixel-anim-check/pixel_anim_check.py --loop idle=examples/showcase/beast/beast_idle.png --loop move=examples/showcase/beast/beast_move.png --loop attack=examples/showcase/beast/beast_attack.png --frame 93 --eye "#f2aa3c" --ink "#120f19,#191a2e,#242844,#323a5c,#404e78,#566594" --effects "#fff9e6,#ffd25e,#c3cdf0,#7d89b8" --action attack:strike:right --speed 1.0 --parts idle=examples/showcase/beast/check/beast_idle_parts.png --parts move=examples/showcase/beast/check/beast_move_parts.png --parts attack=examples/showcase/beast/check/beast_attack_parts.png --squash "#8c8c8c,#208040,#909020" --palette examples/showcase/beast/check/beast_palette.png --ref examples/showcase/beast/check/beast_art.png --out out --name beast
python skills/pixel-animate/body_parts.py examples/showcase/beast/beast_art_8x.png examples/showcase/beast/marks.json --out out --name beast
```

The first prints `beast: 0 fault(s)` and exits 0. Each option has a reason:

- `--ink` names the outline colours. The wolf's top and left edges carry a lit line of its fur ramp instead of ink,
  and those tones are lighter than the default ink threshold: with only `--frame` and `--eye` the same loops report
  149 faults (143 `outline`, 6 `apart`).
- `--effects` names the attack's flash, sparks, speed lines and dust. With `--ink` but without it, they are 12 faults
  (6 `apart` and 6 `outline`, on the strike's frames).
- `--action attack:strike:right` has the attack's anticipation, strike and recovery judged, `--speed 1.0` prints
  the planted feet's speed beside the road's, and `--parts`, `--squash`, `--palette` and `--ref` add the part
  volumes, the colours of the drawing and the likeness of the rest pose (the neck stretches and the far legs pass
  behind the near ones on purpose, hence `--squash`).

The second cuts the wolf into eleven parts from the bones in `examples/showcase/beast/marks.json` and exits 0:

```
torso          torso      share 0.339 pieces 1 bbox [130, 150, 453, 317]
tail           tail       share 0.132 pieces 1 bbox [32, 160, 137, 376]
neck           neck       share 0.165 pieces 1 bbox [376, 73, 560, 296]
head           head       share 0.073 pieces 1 bbox [485, 72, 624, 189]
jaw            jaw        share 0.015 pieces 1 bbox [521, 137, 592, 170] inside head
ear_far        ear        share 0.010 pieces 1 bbox [464, 40, 512, 84]
ear_near       ear        share 0.017 pieces 1 bbox [497, 32, 550, 88]
hind_near      leg        share 0.075 pieces 1 bbox [144, 273, 241, 424]
hind_far       leg        share 0.062 pieces 1 bbox [207, 276, 296, 424]
front_near     leg        share 0.068 pieces 1 bbox [389, 286, 480, 424]
front_far      leg        share 0.042 pieces 1 bbox [360, 289, 413, 424]
moved: torso: a strip of 515 working px along neck, joined to torso only at one end, given to neck
moved: tail: a strip of 204 working px along torso, joined to tail only at one end, given to torso
```

Each leg's bone starts at its joint (the hip line, the elbow), so each leg starts there: the torso runs whole from
rump to chest, and the near hind leg stops at the ink line between it and the far one. The jaw lies within the
head's box, so it is `inside head`: the overlay shows it hatched inside the head. The `moved:` lines are strips
handed back: the rump's edge down the gap beside the tail, which the tail had reached round the gap, and the ruff's
lower edge, which goes with the neck.

`examples/showcase/make_showcase.py` draws the README's pictures from these files (see [Development](#development)).

### Sample output, explained

The broken walker's run, first lines (read-outs such as the box size and the bob follow). The clean walker prints
the same lines without the two faults and the warning, and its move reads `28 21` where this one reads `103 94`:

```
broken: 2 fault(s)
  jump: move a change of 272 px against a mean of 75 (frame 7)
  jump: move[8] is knocked 4 px sideways out of step
  warn: skate: move a planted foot slides 1 px forward (frame 9; 1 slide(s)): a planted foot stays on its world pixel; drawn in place it goes back the same amount each pose
  idle: steps 0 0 13 0 6 0 0 4 0 18 0 5 0 13 0 0 5 0 0 5 0 4 13 6 (% of the figure)
  idle: eye rows [(8, 7), (7, 4), (6, 9), (7, 4)]
  move: steps 21 18 5 32 25 8 20 103 94 15 6 30 24 9 21 27 (% of the figure)
  move: eye rows [(6, 1), (7, 1), (8, 2), (7, 1), (6, 2), (5, 1), (6, 1), (7, 1), (8, 2), (7, 1), (6, 2), (5, 1)]
```

- **Frame numbers are 0-based.** `move[8]` is the move's ninth frame. "(frame 8)" in a `jump` or `snap` is the
  change from frame 8 to frame 9.
- **Faults** come first, one per line, as `kind: where and how much`. Warnings, if any, are `warn:` lines. They point
  at things an action may do on purpose (a jaw opened in an attack). Look at them, but they do not count as faults.
- **The per-step change list** (`steps`) gives the share of the figure that changes from each frame to the next, with
  a 1-px bob forgiven. Its k-th number is the change from frame k to frame k+1 (the last one wraps to frame 0). Here
  `103 94` against neighbours of 5-30 is the frame knocked out and back; the knocked frame also moves a planted
  foot, hence the `skate` warning. Other shapes to look for: a long run of
  zeros and then a big step (a dead stop, then a lurch), one doubled hold among even ones (a dropped update), and
  steps alternating big and small (a lurch).
- **The eye's row track** (`eye rows`) lists runs of `(row, frames)`. In the idle every level should last 4 or more
  frames at an extreme. A level reached for 2 or 3 frames and left again is a *tick*, the 1-px twitch that makes an
  idle look nervous.
- **The contact sheet** (`<name>_check.png`) shows each distinct pose zoomed (at most 12 a loop, spread over it, plus
  every pose a fault names). Each tile is labelled with the frames it holds: `5-7` is one pose held over frames 5 to
  7. Under it, the pixels changed from the pose just before are drawn in red. The tiles of the frames a fault names
  are outlined in red: here frames 8 and 9, whose whole bodies light up red, once going out and once coming back.
- **The GIF** (`<name>_check.gif`) plays the loops side by side at `--fps`. It repeats where all loops and any
  scrolling road line up. If that takes more than four cycles of the longest loop, it plays through twice the
  longest loop's duration and stops. Look at it zoomed and at 1x.

### From code

A project with its own pipeline can skip the PNGs and import the module:

```python
import pixel_anim_check as pac

loops = {"idle": pac.load("idle.png", frame=34), "move": pac.load("walk.gif", fps=30)}
spec = pac.Spec(eye="#ffcc33")             # also: flier=True, shadow={...}, gait=False (= --legless), fps=12, ...
warns = []
faults = pac.check(loops, spec, warns)     # fault lines; warnings go into warns
for line in pac.tracks(loops, spec):       # the two read-outs
    print(line)
pac.sheet(loops, "fox_check.png", faults=faults)   # the contact sheet, faulted frames outlined
pac.gif(loops, "fox_check.gif", fps=30)
```

A frame is a list of rows, and each pixel is a colour key or `None` (transparent). `load` gives `"#rrggbb"` keys.
If your keys are something else, pass two functions to `Spec`, and `rgb` to `sheet` and `gif`:
`lum(key)` returns the key's luma, 0-255 (`0.299 r + 0.587 g + 0.114 b`; the outline default is under 40), and
`rgb(key)` returns `(r, g, b)`. For example, with `(r, g, b)` tuples as keys:

```python
spec = pac.Spec(eye=(255, 204, 51), lum=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2], rgb=lambda c: c)
pac.sheet(loops, "fox_check.png", rgb=spec.rgb)
```

Without them, non-hex keys raise a `TypeError`.

## pixel-animate tools

The method is [`skills/pixel-animate/SKILL.md`](../skills/pixel-animate/SKILL.md). Two scripts sit beside it.

### body_parts.py

Cuts a drawing into rig parts from a few rough bones placed by eye, along the drawing's own ink lines.

```
python skills/pixel-animate/body_parts.py <drawing.png> --grid [--step 50] [--out DIR] [--name NAME]
python skills/pixel-animate/body_parts.py <drawing.png> <landmarks.json> [--out DIR] [--name NAME]
python skills/pixel-animate/body_parts.py --selftest
```

- `--grid` writes `<name>_grid.png`, a copy of the drawing with a labelled grid. Use it to read coordinates for the
  landmarks.
- With a landmarks file it cuts the drawing into parts. Each part has a rough *bone* down its middle, placed by eye.
  A bone is 1 to 4 points. A `null` in a bone starts a new piece: use it for a part seen in pieces (a staff above
  and below the hand, a cape on both sides of the legs). Each piece is 1 to 4 points. `examples/marks.json` is a
  working landmarks file for `examples/figure.png` and uses both. The file's format and how to place bones are in
  [the skill, section 1b](../skills/pixel-animate/SKILL.md#1b-map-the-body-first-body_partspy-landmarks-by-eye-edges-by-measure).
- The cut follows the drawing's own ink lines and colour edges. It writes `<name>_parts.png` (an overlay of the
  parts), `<name>_patches.png`, `<name>_parts.json` (per part: kind, parent, pivot, area share, bounding box and
  label) and `<name>_labels.png`. Cut the original drawing wherever the label image equals the part's JSON `label`
  (its one-based position for older files). Zero is background. This preserves disconnected pieces and holes.
  The `bbox` is the tight crop of the full-size label, with exclusive right and bottom coordinates.
  The JSON `poly` is a simplified outline of the largest piece for display. `--out` defaults to the
  drawing's folder and is made if missing; `--name` to the drawing's file name.
- Each part grows from its bone; where the drawing gives no edge (one fur from back to paw), the joints decide. A
  part that hangs from a parent starts at its bone's first point: put it AT the joint (a leg at the hip line, not up
  in the rump). Shading, a lightness step within one hue, is no edge.
- A part within its parent's box (a jaw in the head) is marked `inside PARENT` on its line and in the json, and the
  overlay shows it hatched inside its parent.
- It prints one line per part. Its `pieces` count is every fragment of the part, however small, and is no fault by
  itself: the example prints `pieces 5` for the staff, which is broken by `null` on purpose and drawn behind the
  hand. A `CHECK:` line is printed only for a real problem: a bone point off the figure, a bone wholly off it, a
  part with no pixels, a part whose second piece is 12 px or more *and* 8 % or more of the part (parts with
  `null`-broken bones are not judged), a bone that ended up in a neighbour, a part mostly of colours not under its
  bone, an `eye` point outside every head part, and figure pixels no part reached. A `moved:` line names a thin strip
  a part reached round a gap, along another part's edge, and gave back to it.
- Exit code: 0 a clean cut (or the grid written), 1 a cut with `CHECK:` lines, 2 a usage error.

Example, on the figure in `examples/` (a person with a staff and a cape):

```
python skills/pixel-animate/body_parts.py examples/figure.png examples/marks.json --out out --name figure
```

It writes `out/figure_parts.png` and the other files, and exits 0.

### creature_map.py

```
python skills/pixel-animate/creature_map.py <drawing.png> [--eye #rrggbb | --eye-at X,Y] [--floating] [--out DIR] [--name NAME]
python skills/pixel-animate/creature_map.py --selftest
```

- It guesses a body plan from the silhouette alone: spine, head end, limbs and pivots. It is a **first look only**
  (see [Limitations](#limitations)). It takes one drawing, not a strip of frames.
- Exit code: 0 done, 1 no body found in the drawing, 2 a usage error.

Run on the example figure, `python skills/pixel-animate/creature_map.py examples/figure.png --out out`, it reads the
person with a staff and a cape as `serpent or worm`: a wrong plan, which is the limitation below.

## Limitations

- **The thresholds are fitted, not derived.** `choppy`, `snap`, `tick`, `hop`, `vanish`, `shallow` and `reshape` were
  fitted to a private calibration set: 39 animated creatures, with 15 accept or reject judgements on them by one
  reviewer. That set is not included. No published source gives a pixel threshold for judder. Each function's
  docstring states its margins. Expect false alarms or misses on styles far from that set, and rerun your approved
  animations whenever you change a threshold.
- **The check does not judge taste.** It cannot see likeness, appeal or whether an attack reads. That is why the skill
  ends with a look by eye.
- **`creature_map.py` is a first look only.** It reads the silhouette, and a silhouette cannot tell a bow from an arm
  or a cape from a tail. On a second private set, 38 hand-drawn reference drawings (humanoids, quadrupeds, fliers,
  serpents, insects and others; not included), it got 13 body plans right and named most parts wrong. The example
  figure comes out as a serpent. Use `body_parts.py`, with bones placed by eye, for the actual cut (it was looked at
  by eye on the same 38 drawings).
- **The method is written for side-view sprites** of creatures, from small pets to large beasts. Top-down and
  isometric sprites are not covered.
- **The scripts can be copied alone,** as the skills do, but `--selftest` needs its test file beside the script
  (`pixel_anim_selftest.py`, `body_parts_selftest.py`, `creature_map_selftest.py`).

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Exit 2, a strip that does not cut into whole frames | Give the real `--frame W` or `--frames N`. Without either, frames are taken as square. |
| A flier reports many `apart` faults (40 on the example) | Its ground shadow counts as stray pieces. Name the shadow colours with `--shadow`. |
| A `size` fault | The checker stops before rendering previews. Give every frame the same canvas and keep the figure anchored when cropping all loops to one union box. |
| A frame folder plays out of order | Files are read in name order. Zero-pad the numbers: `f00.png`, `f01.png`, ... |
| A GIF's holds look longer than its images | Each image is held for its stored duration at `--fps`. Give a strip or a folder to judge one image per frame. |
| An effect (a spark, a thrown coin) reported as `apart` | Name its colours with `--effects`, or allow small pieces with `--allow LOOP=N`. |
| `eye` faults in a loop where a glow recolours the eye | Pass `--glows-eye LOOP`. |
| `TypeError` from the module | Your pixels are not `"#rrggbb"` keys. Pass `lum` and `rgb` to `Spec` (see [From code](#from-code)). |
| `--selftest` says its test file is missing | Copy the matching `*_selftest.py` beside the script. |
| `creature_map.py` names the parts wrong | Expected on real art. Use `body_parts.py` with bones placed by eye. |
| `body_parts.py` prints `CHECK:` lines | Each names a bone or part to fix. Make a `--grid`, move the bone, and run again. |

## Development

```
python skills/pixel-anim-check/pixel_anim_selftest.py
python skills/pixel-animate/body_parts_selftest.py
python skills/pixel-animate/creature_map_selftest.py
python examples/make_examples.py --verify
```

`pixel_anim_selftest.py --verbose` also prints the numbers behind its special clean cases.
`python examples/showcase/make_showcase.py` redraws the README's pictures in `docs/img` from the showcase creatures:
it first checks every loop of every creature with that creature's full check options and stops on any fault, then
writes `hero.gif`, `check.png` and `parts.png`, leaving a picture whose pixels and timing are unchanged as it is.
After changing a creature, run its `animate.py` first. `make_examples.py --verify` checks the examples still match the selftests' creatures; without `--verify` it rewrites only the files
whose pixels differ, and `--docs` also refreshes `docs/img` and the plugin icon. See
[CONTRIBUTING.md](../CONTRIBUTING.md). Changes are listed in [CHANGELOG.md](../CHANGELOG.md).
