# Using Limberpix

The full reference for the two skills and their command-line tools. The [README](../README.md) has the short version.
Every command here runs from the repo root, and each is one line, so it pastes into bash, PowerShell and cmd alike.

- [Requirements](#requirements)
- [Install](#install)
- [In Claude Code](#in-claude-code)
- [In Codex](#in-codex)
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
  - [shrink.py](#shrinkpy)
- [Limitations](#limitations)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Requirements

- Python 3.11 or newer, NumPy 1.24.3 or newer, and Pillow 13.0.0 or newer. Install with
  `python -m pip install -r requirements.txt`.
- CI tests the exact dependency minimums with Python 3.11 and resolves current compatible releases with Python 3.12
  on Ubuntu and Windows. It checks the installed NumPy and Pillow releases against PyPI advisories.
- Claude Code or Codex, if you want an agent to use the skills. The scripts also run on their own.

Both skills work with any engine or art tool: they read and write plain PNGs and GIFs.

## Install

**1. As a Claude Code plugin (recommended).** Inside Claude Code:

```
/plugin marketplace add therwn/limberpix
/plugin install limberpix@limberpix
```

Plugin skills are namespaced, so they show up as `limberpix:pixel-animate` and `limberpix:pixel-anim-check`.

**2. As Codex skills.** In Codex, ask its skill installer for the two folders, then start a new turn:

```
$skill-installer install https://github.com/therwn/limberpix/tree/main/skills/pixel-animate and https://github.com/therwn/limberpix/tree/main/skills/pixel-anim-check
```

They land in `~/.codex/skills/` (or `$CODEX_HOME/skills`). Or copy them there yourself:
`mkdir -p ~/.codex/skills && cp -R limberpix/skills/pixel-animate limberpix/skills/pixel-anim-check ~/.codex/skills/`.

**3. As plain skills.** Copy the skill folders into your personal skills folder, or into one project's:

```bash
git clone https://github.com/therwn/limberpix
skills_dir="$HOME/.claude/skills"                  # or "$PWD/your-project/.claude/skills"
mkdir -p "$skills_dir"
cp -R limberpix/skills/pixel-animate limberpix/skills/pixel-anim-check "$skills_dir/"
```

On Windows PowerShell, from the folder that holds `limberpix`:

```powershell
$skillsDir = Join-Path $HOME '.claude/skills'
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
Copy-Item -Recurse -Force -Path 'limberpix/skills/pixel-animate', 'limberpix/skills/pixel-anim-check' -Destination $skillsDir
```

Check for `pixel-animate/SKILL.md` and `pixel-anim-check/SKILL.md` under that target folder.

A copied skill does not update itself: copy again after every pull.

**4. Only the command-line tools.** Clone the repo and run the scripts with Python:

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

## In Codex

The same two skills, read from the same `SKILL.md` files. Ask for the work in words, or name a skill with `$`:
`$pixel-animate animate this fox's idle and walk from fox.png`, `$pixel-anim-check check walk.png`. Each skill
folder carries `agents/openai.yaml` (the name, the one-line description and the starting prompt Codex shows). The
commands in the skills write the scripts' folder as `${CLAUDE_SKILL_DIR}`, which only Claude Code fills in: in Codex
it is the folder the skill was installed to, `~/.codex/skills/<skill>`. Both skills pass Codex's own skill validator
(`quick_validate.py`); their descriptions stay under its 1024 characters.

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
| `--eye-at X,Y` | the eye's column and row on each loop's first frame, when the eye colour is used elsewhere too: the piece nearest that place is the eye (without it, the biggest piece, and a `note:` says which) |
| `--idle NAME --move NAME` | which loops are the rest and the travel loop (default `idle`, `move`). A name given here must match a `--loop`, or it is a usage error. With no loop of the default name, a `note:` line says which checks do not run: `snap`, `hop`, `shallow` and `drift` need the idle; `still`, `stiff`, `skate` and `gait` need the move; and without a move a walker's `ground` judges every loop |
| `--legless` | a snake or slug: no body rise asked of its move |
| `--facing right\|left` | which way the head faces (default right) |
| `--fps N` | the rate the game plays the loops at (default 30; a decimal is allowed). It sets the GIF's speed and how a GIF input is sampled, and scales `choppy`, `boil`'s rates, `snap`, `hitch`, the eye `tick`'s dwell and an action's held keys |
| `--out DIR` | preview location (default `.`). If it is also a frame input folder, previews go in `anim-previews` inside it |
| `--name NAME` | the stem of the written files (default `anim`) |
| `--no-preview` | run the same checks and print the same diagnostics and tracks without writing a PNG or GIF |
| `--features` | list what must stay, checking nothing: the marks of the approved drawing (`--ref`, else the first frame: eyes, a mouth, studs; kept) and the small pieces apart from it (sparks, motes; not kept), numbered on `<name>_features.png` and written to `<name>_features.json` in `--out`. Edit the list with the user: names, `keep`, and `transient` boxes for what comes and goes on purpose |
| `--keep PATH` | that list, confirmed: `keep` names each kept feature in every frame it is missing from (in place of `lostmark`; an eye-coloured one may blink), and a piece wholly inside a transient box is no `apart` fault |
| `--json PATH` | also write the findings as JSON: each fault and warning with its rule, its loop, the 0-based frames it names and its text; `lostmark` adds the lost mark's place and size, `spots` its group. `findings(loops, Spec(...))` returns the same from Python |
| `--action NAME[:KIND[:DIR]]` | that loop is an action: up to two keys (a wind-up and a follow-through) may be held, each up to 13 frames. `strike` (with a direction) has its phases judged; `jump` is not asked to keep to the ground |
| `--spots PATH` | (with `--ref`, the approved drawing at the loops' scale) a JSON file `{"group": [[row, column], ...]}` naming the drawing's small marks by eye (a hat's specks, a mouth): `spots` names every pose of a loop other than an action showing fewer of a group's marks at their place. A mark that changed colour or became a pinhole still counts |
| `--style pixel\|redrawn` | how the frames were made (default `pixel`: one drawing moved by whole pixels). `redrawn`: every pose a new drawing of the whole figure (frame by frame, or generated). Its faults are the frames that lose the character; how the body moves (`stepped`, which replaces `choppy`, `uneven` and `lurch` and asks the whole body to move 6 times a second, and `frozen`, `stiff`, `snap`, `tick`, `hop`, `shallow`, `still`) only warns; `lostmark` (a mark inside a patch, such as a mouth on a face, that most poses keep and some drop, even one frame: the poses vote, no reference needed; an `--eye`-coloured mark gone once or twice is a blink) and `gaps` (an outline broken in short stretches; give every outline colour with `--ink`) are run; `shimmer` is off; `reshape` and `outline` warn only |
| `--min-rate R` | `choppy`'s floor for the idle and the move, in updates a second (a number over 0), for a style held longer than the fitted floors allow. Without it the floor is 10, 5.2 for a move whose every pose change is big (a new drawing of the stride), and 2.5 for an idle whose every pose moves the body |
| `--speed PX` | the road's scroll in game px a frame: the planted feet's speed is printed beside it, and the GIF scrolls a ground line under the move |
| `--parts LOOP=PATH` | a part strip for that loop (the same frames, each rig part one flat colour): per-part volume and lag are judged on it |
| `--squash #hex,...` | part colours whose area changes on purpose (wings, a squashed body) |
| `--palette PATH` | the approved drawing: every frame must keep to its colours |
| `--ref PATH` | the approved drawing at game size: the idle's nearest pose must match it |
| `--glow #hex,...` | colours shown in some frames on purpose (glow steps, glints, blink lids) |
| `--mark #hex,...` | small defining marks (a gem, a lamp): on every frame, never jumping 2 px in one frame |
| `--sheet LOOP` | that loop was drawn as a sheet or by AI: a part switched off for one cell is looked for |
| `--key #rrggbb` | the background colour of strips with no transparency, read as air in the loops, `--parts`, `--ref` and `--palette`. That exact colour only: clean a key's fringe first. Without it, a loop with no transparent pixel in any frame is a usage error |

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
bands with a 1-px step between them), `hitch` (the head or a part stepping 1 px alone after a long hold), `seam`
(the first pose repeated at the loop's end), `ground` in a legged walker's move (the lowest drawn row moving: a
whole-figure lift) and more; `--help` lists them all.

The eye is found one way by every check: one piece of the eye colour, the biggest on a loop's first frame (the
frontmost on a tie), then on each frame the piece nearest its last place. So the same colour used elsewhere (a gem,
a glint on the flank) is not taken for the eye, and a `note:` before the faults says which piece was read when the
first frame shows several. An `eye` fault is the eye missing on a frame, or in the idle or the move its place
jumping out of its head's box in one frame (a cell mirrored or off its anchor, or the eye lost while its colour
shows elsewhere); in other loops that jump is a warning.
Each fault, with its usual cause and fix, is
in the table in [`skills/pixel-anim-check/SKILL.md`](../skills/pixel-anim-check/SKILL.md#2-what-each-fault-means-and-the-usual-fix).

### Example runs

The files in [`examples/`](../examples) are small creatures drawn by `examples/make_examples.py`. The walker's frames
are 34 px wide, the flier's 30 px, and both have the eye `#ffcc33`.

The clean walker:

```
python skills/pixel-anim-check/pixel_anim_check.py --loop idle=examples/walker_idle.png --loop move=examples/walker_move.png --frame 34 --eye "#ffcc33" --out out --name walker
```

It prints `walker: 0 fault(s)`, exits 0, and prints the folder holding `walker_check.png` and `walker_check.gif`.
Read `out/walker_check.json` for the two paths relative to `out`.

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
(`*_art_8x.png`) and three loops at 30 fps. Frame and pose counts include the wrap from the last frame to the first:

| Creature | Frame | Idle | Move | Attack | Road speed |
|---|---|---|---|---|---|
| beast | 93x52 | 60 frames, 24 poses | 32 frames, 32 poses | 40 frames, 20 poses, a lunge and a bite | 1.0 px a frame |
| bird | 86x69 | 72 frames, 31 poses | 32 frames, 16 poses | 54 frames, 27 poses, a dive strike | 1.0 px a frame |
| lizard | 113x40 | 60 frames, 24 poses | 32 frames, 16 poses | 34 frames, 18 poses, a tongue strike | 0.5 px a frame |

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
  138 faults (132 `outline`, 6 `apart`).
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

`examples/showcase/make_showcase.py` draws the README's pictures from these files (see [Development](#development)),
and `examples/showcase/make_gallery.py` draws the gallery's loop GIFs, the animated walkthrough of the rig and check,
and four faults the check names. [examples/README.md](../examples/README.md) shows every example with its pictures.

[`examples/fighter/`](../examples/fighter) holds a fighter in a stance, drawn at game size (48x64) from a skeleton by
`fighter.py`, and its idle built the Pixelblog 52 way: one bounce of 8 poses held 3 frames over the rise and the top
and 2 on the drop, the torso moving on every pose, the limbs further from the body moving more, the head holding at
the turns and the headband's tails a pose behind it. `python examples/fighter/fighter.py OUT_DIR` writes the
drawing, the strip, its part strip and a GIF; the check command in its docstring (the lit-side ink declared with
`--ink`) gives 0 faults and 0 warnings, which CI checks.

### Sample output, explained

The broken walker's run, first lines (read-outs such as the box size and the bob follow). The clean walker prints
the same lines without the two faults and the warning, and its move reads `28 21` where this one reads `103 94`:

```
broken: 2 fault(s)
  jump: move a change of 272 px against a usual 49 (frame 7)
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

Each CLI run renders both files in its own directory and prints that directory after `sheets:`. Scripts that used
the old `<name>_check.png` and `<name>_check.gif` paths directly under `--out` can read `<name>_check.json` once and
resolve its `png` and `gif` paths relative to the manifest. The checker replaces the manifest only after both
images are ready, so concurrent runs and failed renders leave a complete pair available. Earlier generations stay
on disk for readers that already resolved their paths. When `--out` is also a frame input directory, the manifest
and generations go under `anim-previews/`. If a flat contact sheet from an older run still sits among the frames,
move it out of the frame directory. An explicitly supplied PNG is read regardless of its filename.

Use one name per loop and give `--name` as a filename stem. If an output would overwrite a source, choose another
`--out` or `--name`. For batch jobs, `--no-preview` keeps the checks, diagnostics and motion tracks and skips image
rendering and publication.

The checker accepts up to 2,048 frames and 8 million frame-pixels per CLI run, including part strips, palette and
reference inputs. A frame-pixel counts once per game frame, including held frames expanded from a GIF. Timed
inputs and GIF previews are limited to 120 seconds. Each preview is capped at 80 million rendered pixels across
its images and 32,768 pixels per side. The showcase's largest input set uses under 2 million frame-pixels. Its
largest GIF needs about 73 million at the default zoom. Use `--no-preview` when only preview size is exceeded.

### From code

A project with its own pipeline can import the module. Run this example from the repository root:

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd() / "skills" / "pixel-anim-check"))
import pixel_anim_check as pac

loops = {name: pac.load(f"examples/walker_{name}.png", frame=34) for name in ("idle", "move")}
spec = pac.Spec(eye="#ffcc33")             # also: flier=True, shadow={...}, gait=False (= --legless), fps=12, ...
warns = []
faults = pac.check(loops, spec, warns)     # fault lines; warnings go into warns
for line in pac.tracks(loops, spec):       # the two read-outs
    print(line)
out = Path("out")
out.mkdir(exist_ok=True)
pac.sheet(loops, out / "walker_check.png", faults=faults)
pac.gif(loops, out / "walker_check.gif", fps=30)
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

### fix_sheet.py

The two tools below and the check in one command, for a sheet an image model drew:

```sh
python skills/pixel-anim-check/fix_sheet.py sheet.png --ref drawing.png --features --out out --name idle
python skills/pixel-anim-check/fix_sheet.py sheet.png --ref drawing.png --keep out/idle_features.json --fps 8 --out out --name idle
```

`--features` prepares the sheet and writes the keep list's candidates (off the drawing when it is pixel art with 64
colours or fewer, else off the first frame), and stops. With `--keep` (or neither) it prepares the sheet
(`<name>_strip.png`), repairs it (`<name>_fixed.png`, `<name>_repair.json`, `<name>_repair.png`) and runs the check
on the fixed strip in `--style redrawn`, with its contact sheet and GIF. `--grid`, `--eye`, `--ink`, `--effects`,
`--shadow` and `--fps` are passed on. The exit code is the check's.

### prepare_sheet.py

Brings a sheet an image model drew (a grid of poses on a flat background, at its own size) onto the approved
drawing's pixel grid.

```sh
python skills/pixel-anim-check/prepare_sheet.py sheet.png --ref drawing.png [--grid CxR] [--colours N] [--cover 0.42] --out out --name idle
```

1. **Background:** transparency, or the corners' colour within 90 (summed over the channels), and a green key's
   greenish fringe.
2. **Cells:** `--grid CxR`, or found from the empty rows and columns between poses (gaps of 0.5 % of the sheet; a
   spark alone in a gap joins its nearest pose).
3. **One scale** from the poses' heights against the drawing's; a pose more than 8 % off keeps its own.
4. **One anchor:** the lowest row and the middle of the lowest quarter on the drawing's.
5. **By vote** onto the drawing's grid: every pixel snapped to one palette first (the drawing's colours when it has
   64 or fewer, else `--colours` tones cut from the sheet and 16 from its vivid pixels), a game pixel drawn when
   `--cover` of its cell is figure, in the colour with the most area.

Out: `<name>_strip.png` and `<name>_prepare.json` (background, cells, scales, palette); the check command is
printed. Exit 0 done, 2 a usage error.

### repair_sheet.py

Draws back a mark (a mouth, an eye, a stud) that `lostmark` or `keep` finds missing in some frames of a generated
sheet, from the nearest frame that has it, and leaves every other frame as it is.

```sh
python skills/pixel-anim-check/repair_sheet.py idle.png --frame 64 [--keep LIST.json] [--eye "#rrggbb"] [--ink C,...] [--effects C,...] [--shadow C,...] [--key "#rrggbb"] [--fps N] --out out --name idle
```

- **Where it goes:** the donor's other marks beside it (the eyes beside a mouth), found again in the frame, give
  the shift; with none, the pixels around the mark are matched over every shift within reach of the figure's move.
  It is drawn only over the patch's own pixels, never over air or an outline.
- **What it will not do:** draw a mark that moved within its patch (it is a few pixels off, not lost), or keep a
  drawing the check still reads as lost (it is undone).
- **Out:** `<name>_repaired.png`, `<name>_repair.json` (repairs, skips, the faults before and after) and
  `<name>_repair.png` (before and after). Exit 0 nothing left to repair, 1 a mark still missing, 2 a usage error.
- **Limits:** a mark that moved onto its patch's edge may be drawn twice, so look at `<name>_repair.png`; a lost
  piece apart from the figure, an outline gap and colour, scale or anchor drift are not repaired yet.

## pixel-animate tools

The method is [`skills/pixel-animate/SKILL.md`](../skills/pixel-animate/SKILL.md). Three scripts sit beside it.

Read the result manifest once to open a complete set from the same run. The three manifests are
`<name>_parts_manifest.json`, `<name>_map_manifest.json` and `<name>_shrink_manifest.json`. Each maps a filename
such as `figure_labels.png` to its path relative to the manifest. This replaces the old lookup by filename directly
under `--out`. The CLI publishes the manifest after all files are ready. Earlier result directories stay available
to readers that already resolved their paths. `body_parts --grid` writes its single image directly under `--out`.

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
  part with no pixels, a part whose second piece in the full-size mask is 12 px or more *and* 8 % or more of the part (parts with
  `null`-broken bones are not judged), a bone that ended up in a neighbour, a part mostly of colours not under its
  bone, an `eye` point outside every head part, and figure pixels no part reached. A `moved:` line names a thin strip
  a part reached round a gap, along another part's edge, and gave back to it.
- Exit code: 0 a clean cut (or the grid written), 1 a cut with `CHECK:` lines, 2 a usage error.

Example, on the figure in `examples/` (a person with a staff and a cape):

```
python skills/pixel-animate/body_parts.py examples/figure.png examples/marks.json --out out --name figure
```

It writes `out/figure_parts_manifest.json` with the four output paths and exits 0.

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

### shrink.py

Brings one frame posed at a large reference's resolution down to game size. Use it on the painted-reference path
(pixel-animate section 2, step 5); a drawing already at game size is posed at that size and never shrunk.

```
python skills/pixel-animate/shrink.py REF.png --size W,H --colours N [--out DIR] [--name NAME]
python skills/pixel-animate/shrink.py REF.png --size W,H --palette REST.png --rest REST.png [--out DIR] [--name NAME]
python skills/pixel-animate/shrink.py --selftest
```

The first line shrinks the rest frame once and makes the palette from it. Use its printed `shrunk:` path as
`REST.png` in the second line so every loop shares one palette and ties fall the same way on every frame.

| Option | Meaning |
|---|---|
| `REF.png` | one frame at the reference's resolution, cropped to the box every pose of every loop fits in (one box and one size for every frame keep still parts on the same game pixels) |
| `--size W,H` | the game size of that box |
| `--scale S` | in place of `--size`: S reference px to a game px (S need not be whole) |
| `--colours N` | make the palette from REF: N - 1 tones of the fill and one for the contour (10-12 for a busy texture, 16-18 for a plain one) |
| `--palette PATH` | the palette: every opaque colour of that image (the rest frame already shrunk, or the approved drawing at game size) |
| `--rest PATH` | the shrunk rest frame: a tie goes to its colour at that game pixel |
| `--cover F` | the share of a cell that must be figure for the pixel to be drawn (default 0.42; about 0.3 for a narrow wing or a thin tail joint) |
| `--contour V` | contour pixels are those with red + green + blue under V (default 70) |
| `--no-contour` | read the contour with the fill, not apart |
| `--key #rrggbb` | an opaque background colour read as air (default: transparency is air) |
| `--out DIR` / `--name NAME` | where the files go and their stem (default REF's folder and file name) |

Each game pixel is drawn when `--cover` of its cell is figure. Contour ink fills a cell if it covers over half of
the cell, or at least 0.12 at the crest across a stroke. An end on the same crest can extend into a cell below
`--cover`. Cells filled by dark hatching keep the ink as their fill. Two cells straddling the same narrow stroke
can share one contour pixel. For the fill, snap contributing source pixels to the palette and take the colour
with the most area in the cell. A tie goes to the rest frame's colour there, or else to the first tied colour in
the palette's order.

- **Out:** `<name>_shrunk.png` (game size, palette colours only) and, with `--colours`, `<name>_palette.png` (one
  pixel a colour, dark to light).
- **Exit code:** 0 done, 2 a usage error (a bad option, a missing file, an image with no transparency and no
  `--key`, a rest frame of another size).
- **Limits:**
  - Small moves: see Limitations below.
  - It takes one frame at a time: a strip cannot be cut safely when a cell is fractional.
  - Putting back the eye and small marks, dropping a pixel left with no neighbour, and drawing the outline are not
    its job (pixel-animate's step 5 does them after it).
  - Its numbers were measured by one person, and one person looked at the pictures (sources and measurements in
    [`skills/pixel-animate/REFERENCES.md`](../skills/pixel-animate/REFERENCES.md)).
  - CI runs the check on Python 3.11 with the pinned minimums and on Python 3.12 with current compatible dependencies.

## Limitations

- **The thresholds are fitted, not derived.** `choppy`, `snap`, `tick`, `hop`, `vanish`, `shallow` and `reshape` were
  fitted to a private calibration set: 39 animated creatures, with 15 accept or reject judgements on them by one
  reviewer. That set is not included. No published source gives a pixel threshold for judder. Each function's
  docstring states its margins. Expect false alarms or misses on styles far from that set, and rerun your approved
  animations whenever you change a threshold.
- **Some margins still count frames,** set at 30 fps, and `--fps` does not scale them: `vanish` asks a piece to stay
  gone 3+ frames, `speck` looks for a blink of 1-2 frames, `hitch` leaves a step that comes back within 3 frames to
  `tick`, and `mark` faults a jump of 2 px in one frame. At another rate the same count is another length of time
  (3 frames are 0.1 s at 30 fps and 0.25 s at 12), so on a 12 or 15 fps loop read their reports, and their silence,
  with that in mind.
- **A walk pose out of order is not caught.** Every walk step already changes 35-40 % of the figure, so a misplaced pose
  reads 1.3-1.5 times the usual step against `jump`'s 3.6, and the test tried (how much better a pose fits elsewhere in
  the loop) gave 0.58-0.62 on the clean bird and 0.16-0.59 on broken walks: find it by eye on the contact sheet, where
  each pose should fall between its neighbours.
- **A texture redrawn at random on twos or threes is not caught.** One alternating between two tones is caught on ones,
  twos and threes, but a random one changes half or a third as often there, so each pixel's flips stay under `shimmer`'s
  3 a loop: watch the GIF at full speed for it.
- **One 4-frame hold among twos is not caught.** A lost update is seen only at the loop's seam (`seam`) or where the
  usual hold is 3 or more (`choppy`), and the measure tried (how far the motion carries through a hold) read an accepted
  flier idle's turns as worse than broken loops: check the rig's pose list for two identical ticks outside a turn
  (pixel-animate, section 5) and look for the stall in the GIF.
- **A bob drawn upside down (the body up while the legs are spread) is not caught.** With part strips (each leg part's
  centre against the body part's top row) the clean walks read +0.53 (the selftest walker), -0.03 (the lizard) and -0.24
  (the beast) against -0.71 for the walker turned upside down, and without them (the lower band's width) +0.71, +1.0 and
  -0.33 against -0.75, since a four-legged walk's legs do not follow one step: read the `legs widest ... body lowest
  ...` read-out and the GIF.
- **`shrink.py` cannot make a small move clean.** Even its best method changes a third of the pixels when the drawing
  moves a fifth of a cell, so parts are moved by whole game pixels: look at the shrunk frames side by side.
- **The check does not judge taste.** It cannot see likeness, appeal or whether an attack reads. That is why the skill
  ends with a look by eye.
- **A fault count is not a score of the motion.** On one character judged by one viewer (a cloaked wizard: a
  hand-drawn sheet, and cut-out loops made from its first frame; the partly lined drawing gives `outline` on every
  frame of all of them) the count did not follow the verdict: a cut-out idle with no other fault was judged worse
  than the hand-drawn idle, which adds a `choppy` at the rate it was watched at; a second cut-out idle, closer to
  the hand-drawn one by pixel difference, added a `jump` and was judged worse still; and in `--style redrawn` all
  three get `stepped` alike.
- **A cut-out cannot show what the drawing does not show.** On that same character, 16 % of each hand-drawn idle
  frame's pixels (30 % at the deepest pose) matched no part of the first frame however shifted, and thirteen parts
  fitted to each frame by pixel difference left 29-39 % of the pixels wrong at the deepest poses: the cloak opens on
  a lining, the legs bend, the walk and the attack are other poses. pixel-animate suits a rigid body with limbs, a
  tail or wings; cloth that changes shape and a body that turns need new drawings.
- **Every loop is read as a cycle.** A one-shot that does not end where it began (a death) gets a `jump` and a
  `vanish` at its last-to-first step. There is no option to say a loop plays once.
- **`choppy` and `stepped` need the real frame rate.** They are counted in time. A sheet that comes with no rate has
  none to check: one hand-drawn 10-frame idle gets `stepped` at 8.3 and at 10 fps and passes at 12.
- **A drawing lined only in places fails `outline` on every frame** in the default style, the approved drawing with
  it; there is no switch for a partly lined style short of `--style redrawn`, where it only warns.
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
| Exit 2, `has no transparent pixel in any frame` | The strip has a flat background and no alpha, so the whole frame would read as the figure (a run gives an `outline` fault on every frame). Export it with a transparent background, or name the background with `--key #rrggbb`. `--key` removes that exact colour only: an anti-aliased fringe round the figure must be cleaned first. |
| An effect (a spark, a thrown coin) reported as `apart` | Name its colours with `--effects`, or allow small pieces with `--allow LOOP=N`. |
| `eye` faults in a loop where a glow recolours the eye | Pass `--glows-eye LOOP`. |
| A `note:` says the eye colour shows in several pieces, and names a piece that is not the eye | Give the eye's place on the first frame with `--eye-at X,Y`. Until then the eye track, `frozen`, `tick` and `reshape` follow the wrong piece. |
| `apart` on every frame after naming `--effects` | A colour named there is one the figure wears too, so its own parts are taken for effects. Name only colours the figure does not use, and use `--allow LOOP=N` for the rest. |
| A session follows rules or misses options this page describes | The skills were copied into `~/.claude/skills/` and the copy is older than the repo. Copy `skills/*` again after every pull. |
| `TypeError` from the module | Your pixels are not `"#rrggbb"` keys. Pass `lum` and `rgb` to `Spec` (see [From code](#from-code)). |
| `No module named 'numpy'` (or `'PIL'`) though both are installed | The skills run the scripts with `python -I`, isolated mode: it leaves the script's own folder, `PYTHON*` variables (such as a `PYTHONPATH` into the project) and the user's site-packages off the import path, so a stray file named like a standard module (`json.py`) cannot shadow it. Packages from `pip install --user` (where pip also falls back when it cannot write elsewhere) are not seen then. Install numpy and Pillow in a virtual environment or for the whole system, or run the command without `-I`. |
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
