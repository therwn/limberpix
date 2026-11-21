# Changelog

All notable changes to this project are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

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
- `examples/showcase/`: three original creatures (a fox, a bird and a lizard) drawn as data and animated by the
  skills' rules, each with an idle and a move that pass pixel-anim-check. `make_showcase.py` builds the README's
  pictures from them.
- A short README; the full reference is in `docs/usage.md`.
- Rules and checks learned from public pixel-art animation guides (sources in each skill's REFERENCES.md):
  action phases (anticipation, strike, recovery), jumps and landings, planted feet that do not slide, walk bobs,
  follow-through lag, smears, arcs, staging, layered idle periods, effect timing. New faults `palette` and `mark`;
  `jump` now catches a pose held on twos knocked sideways; new warnings `skate`, `gait`, `boil`, `counter`,
  `strike`, `recover`, `stage`, `piston`, `gravity`, `squash`, `volume`, `lag`, `blend`, `orphans`, `speck`,
  `doubles`, `drift` and `swap`, with options `--action`, `--speed`, `--parts`, `--squash`, `--palette`, `--ref`,
  `--glow`, `--mark` and `--sheet`.
- CI on Ubuntu and Windows with Python 3.9 and 3.12, Python 3.8 on Ubuntu 22.04, and a NumPy 2 job that treats
  deprecation warnings as errors.

[0.1.0]: https://github.com/therwn/limberpix/releases/tag/v0.1.0
