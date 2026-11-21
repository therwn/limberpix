# Limberpix

[![selftest](https://github.com/therwn/limberpix/actions/workflows/selftest.yml/badge.svg)](https://github.com/therwn/limberpix/actions/workflows/selftest.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Two Claude Code skills for pixel-art sprite animation: animate a creature from one drawing so it moves like a living
thing, and check every loop for broken motion before anyone sees it.

![Three pixel-art creatures animated with pixel-animate, a young wolf, a kingfisher-like bird and a chameleon-like lizard, each playing its idle, then its move over a scrolling road, then its attack: a lunge and bite, a dive and a tongue strike](docs/img/hero.gif)

Three original creatures, each drawn once as data and animated from that drawing alone: an idle, a move over a road
scrolling at the creature's own speed (a walker's planted feet keep pace with it) and an attack. Every loop
passes pixel-anim-check with 0 faults; their sources are in [`examples/showcase/`](examples/showcase).

**Requirements:** Python 3.8+ with numpy and Pillow (`python -m pip install -r requirements.txt`); Claude Code to use
the skills.

## Install

> **Not yet published:** until the GitHub repo is public, use `/plugin marketplace add <path to this folder>`.

**Plugin** (inside Claude Code):

```
/plugin marketplace add therwn/limberpix
/plugin install limberpix@limberpix
```

**Plain skills:** copy `skills/*` into `~/.claude/skills/` (or a project's `.claude/skills/`).

**Command-line tools only:** `git clone https://github.com/therwn/limberpix`, then run the scripts with Python.

## Quick start

From the repo root, on the files in [`examples/`](examples):

```
python skills/pixel-anim-check/pixel_anim_check.py --loop idle=examples/walker_idle.png --loop move=examples/walker_move.png --frame 34 --eye "#ffcc33" --out out --name walker
python skills/pixel-anim-check/pixel_anim_check.py --loop idle=examples/walker_idle.png --loop move=examples/broken_move.png --frame 34 --eye "#ffcc33" --out out --name broken
python skills/pixel-animate/body_parts.py examples/figure.png examples/marks.json --out out --name figure
```

The first prints `walker: 0 fault(s)`; the second finds two `jump` faults around frame 8 and exits 1; the third writes
`out/figure_parts.png`. Each check also writes a contact sheet and a GIF to `out/`.

In Claude Code you can skip the commands: ask "animate this fox's idle and walk from fox.png" or "check walk.png
before I put it in the game".

## The skills

**[pixel-animate](skills/pixel-animate/SKILL.md)** is a written method, not a generator: cut the approved drawing
into parts, pose them at full size, shrink every frame on one fixed grid, with the motion rules that read in pixels
(whole-pixel steps, holds, wings, legs, tails, heads). Claude uses it to make or remake a sprite animation, or when
one looks stiff, broken or unlike its drawing. `body_parts.py` cuts the drawing into parts.

![body_parts.py on the wolf's drawing: rough bones placed by eye, and the eleven parts it cut along the drawing's own ink and colour edges, each tinted and named](docs/img/parts.png)

**[pixel-anim-check](skills/pixel-anim-check/SKILL.md)** measures every loop and names its faults: specks, a lost
eye, open outlines, feet off the ground, pops, shimmer, choppy timing, 1-px ticks, a frozen head and more. It writes
a contact sheet and a GIF for a look by eye. Claude uses it whenever an animation is made or changed, and before one
is shown.

![pixel-anim-check on the wolf's walk: with the eye painted over on frames 6-7 it prints two eye faults and exits 1; the walk as drawn prints 0 faults and exits 0](docs/img/check.png)

## Docs

[docs/usage.md](docs/usage.md): every option, the sample output explained, use from code, limitations,
troubleshooting and development.

## Licence

[MIT](LICENSE), copyright (c) 2026 therwn.
