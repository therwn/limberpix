# Contributing

Thanks for helping. Issues and pull requests are welcome. Bug reports with a small strip that shows the problem are
the most useful kind.

## Ground rules

1. **Every check ships with a selftest case.** A new fault, or a change to an existing one, comes with a case in
   `skills/pixel-anim-check/pixel_anim_selftest.py`. The case breaks the clean walker or flier in exactly that way and
   asserts that the new fault, and not some other fault, catches it. The same goes for `body_parts.py` and
   `creature_map.py` and their selftests.
2. **Clean creatures stay clean.** The selftest's clean walker, clean flier and the breathing walker must pass with
   no false alarm. So must every example in `examples/` marked clean. A check that cries wolf is worse than none. If
   a change makes a clean case fail, fix the check, not the case.
3. **Say what data a threshold was fitted on.** Many thresholds here have no published source. When you add or move
   one, write in the function's docstring what it was fitted on (how many animations, of what kind, judged by whom)
   and the margin it keeps on each side. "Looked right to me on one sprite" is honest and allowed. An unexplained
   number is not.
4. **No new dependencies.** Python 3.8+, numpy and Pillow only. The scripts must stay single files that can be
   copied into another project's folder and run there (their `--selftest` needs the matching `*_selftest.py`
   beside them, and says so when it is missing).
5. **Keep the API stable.** Projects import `pixel_anim_check` from their own adapters. Do not rename or remove
   `check`, `cadence`, `tracks`, `sheet`, `gif`, `load`, `fault_frames`, `main` or the `Spec` fields. Add new
   parameters with defaults.

## Before you open a pull request

```bash
python -m pip install -r requirements.txt
python skills/pixel-anim-check/pixel_anim_selftest.py
python skills/pixel-animate/body_parts_selftest.py
python skills/pixel-animate/creature_map_selftest.py
python skills/pixel-animate/shrink_selftest.py
python examples/make_examples.py --verify
```

If you changed what the selftests draw, regenerate the examples and the README's pictures:

```bash
python examples/make_examples.py --docs
```

## Writing

The SKILL.md files are read by Claude as instructions, so write them as plain, direct guidance. Give the reason for
every rule ("hold small motions two frames, because single-frame 1-px moves read as shimmer"). Do not write "we
decided" or a history of reviews. Keep each SKILL.md under 500 lines and move long reference material into a file
beside it.
