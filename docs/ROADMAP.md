# Roadmap

## What Limberpix is for

An image model draws a pixel character's sprite sheet, say a 10-frame idle, and it does not hold the character
from frame to frame: in frames 2 and 9 the mouth is gone, in another a hat speck, an eye or a stretch of outline.
Limberpix finds those losses and repairs them, so the sheet can go into a game.

It is a quality and repair layer on top of any generator (ChatGPT image generation, SpriteCook, PixelLab,
Autosprite, a video model). It runs locally, gives the same answer for the same input, spends no credits, and says
which frame lost what and what it changed.

A rule is kept because it helps find or repair such a loss, not because it is already there.

## Where it stands

| | Done | Missing |
|---|---|---|
| **Finding** | `pixel-anim-check --style redrawn`: `lostmark` (a mark inside a patch, such as a mouth, gone in some poses), `spots` (marks placed on the approved drawing), `gaps`, `apart`, `eye`, `palette`, `mark`, `vanish`. On a generated wizard idle it names the mouthless poses (9, 10, 13, 15) and the hat's lost specks exactly as the viewer did. Motion checks only warn in this style | Finding a loss without a reference or hand-placed marks; scale, colour and anchor drift as faults; a part changing sides; machine-readable output; a quieter report (one `outline` warning a frame today) |
| **Repairing** | Prototypes outside the skills: keying out, one scale, anchoring by the feet, one palette, marks painted back from the drawing, outline gaps closed, boots locked | All of it as a tool in the skill |
| **Measuring** | One labelled sample (the generated wizard idle, 32 per-frame judgements) | A set of sheets with known losses, run in CI |

## 1. Purpose and rules

- [x] In `--style redrawn`, how the body moves (`stepped`, `frozen`, `stiff`, `snap`, `tick`, `hop`, `shallow`,
  `still`) is a warning. The faults are the frames that lose the character.
- [ ] README and both SKILL.md files lead with the generated-sheet workflow: a sheet and the approved frame in,
  the faulty frames and a repaired sheet out. Posing one drawing (`pixel-animate`) stays as the second route.
- [ ] Every remaining rule is reviewed against the purpose. A rule that neither finds nor repairs a loss moves to an
  opt-in motion profile.
- [ ] One warning a loop where today there is one a frame (`outline`), and no `drift` reading that every pixel
  of a redrawn pose differs.

## 2. Finding without a reference

- [x] **The frames vote** for marks inside a patch (`lostmark`): when 8 of 10 frames show a mouth and 2 do not,
  the 2 are named. No approved drawing or hand-placed marks needed.
- [ ] The same vote for features not closed in by one patch (an accessory, a hand, a part on the silhouette's
  edge), and checked against the drawing when one is given.
- [ ] Losses read: a feature gone or added (mouth, eye, mark, accessory), colour drift, height and scale drift,
  anchor drift (feet, body centre), a part changing sides, outline gaps, stray specks, a background fringe, a part
  cut by the cell's edge.
- [x] **What must stay, and what may come and go.** A spark leaving a staff, a twinkle or a glow is meant to vanish;
  the mouth, the eyes, a hat's marks and the outline are not. Today only colours can be declared transient
  (`--effects`), which fails when an effect shares a colour with the body (a gold spark and gold trim), and an
  undeclared spark off the body is an `apart` fault in every frame it shows. The check should build a keep list
  from the approved drawing and the vote (features most frames have), show it numbered on the drawing for the user
  to confirm, and take transient regions or features, not only colours. Only the keep list is judged.
  Done: `--features`, `--keep`, `transient` boxes.
- [ ] Follow a kept feature on its own part. It is looked for near its place moved with the whole figure, so a
  mark on a cape swinging on its own is lost from view.
- [ ] Read marks on a painted drawing (thousands of colours, no one-colour patch), and propose fewer shading and
  texture marks.
- [x] `--json` and `findings()`: each finding with its rule, loop, frames and text; a lost mark's place and size.
- [ ] A region (a mask or a box) for every rule, not only `lostmark` and `spots`.

**Done when** a sheet with a feature removed from chosen frames has exactly those frames found, with no
reference.

## 3. Repair

- [ ] `repair_sheet.py` in the skill: split the sheet into cells (the grid found, or given), key out the
  background and its fringe, one scale, one anchor, one palette.
- [ ] Region repair: a lost feature is taken from the nearest sound frame or the drawing, placed where that frame's
  head (or part) is, and its seam re-inked.
- [ ] Sound frames are never touched. Every change is logged, with a before-and-after sheet.
- [ ] A frame that cannot be repaired here is named, with a prompt to regenerate that frame alone.

**Done when** the sheet from step 2 comes back with the feature on every frame and the other frames
pixel-identical.

## 4. One workflow

- [ ] One command: sheet, check, repair, check again, a GIF and a contact sheet.
- [ ] The skills tell the agent to show the faulty frames framed in red, repair them, and hand over a GIF to play.
- [ ] A prompt guide for image models that keeps the losses down from the start.

## 5. Measuring

- [ ] Built cases in CI: sound sheets with features removed, recoloured, moved or scaled in chosen frames. Each
  must be found in exactly those frames and repaired.
- [ ] Real sheets from image models, each frame labelled by a person ("frame 9: no mouth"). Measured: losses missed,
  false alarms, and repairs the person accepts when the loop plays.
