---
name: pixel-animate
description: Animate side-view pixel-art characters and creatures from an approved drawing. Use for idles, walking or flying, actions and attacks, or to fix stiff motion or a lost likeness in a side-view sprite. Top-down and isometric animations are outside this method's scope.
---

# Animating pixel-art creatures

The goal is an animation that keeps the approved drawing's look and moves like a living thing. Do not redraw the
creature. A redrawn one that moves well but no longer looks like itself reads as a different creature, and a
faithful one that moves like a cut-out reads as paper. Work from the approved drawing.

**Paths.** The scripts sit next to this file. Claude Code fills `${CLAUDE_SKILL_DIR}` with that folder. Codex and
any other agent that leaves it as written read it as the folder this SKILL.md was loaded from (in Codex,
`~/.codex/skills/pixel-animate`). Python 3.11+ with NumPy 1.24.3+ and Pillow 13.0.0+. The commands
use `python -I` (isolated mode): it leaves the script's own folder, `PYTHON*` variables (such as a `PYTHONPATH` into
the project) and the user's site-packages off the import path, so a stray file named like a standard module
(`json.py`) cannot shadow it. It also hides packages installed with `pip install --user`: on `No module named 'numpy'`
(or `'PIL'`), install numpy and Pillow in a virtual environment or for the whole system, or drop the `-I`. Sources
named below are linked in [REFERENCES.md](REFERENCES.md).

**Terms.** *Game px*: one pixel of the sprite as the game shows it; *reference px*: one pixel of the larger drawing
the animation is made from. *On twos*: a new drawing every 2nd frame (a *hold* of 2); *threes*: every 3rd. A
*moving hold* is a pose that looks still but keeps a small motion. A *rig* poses cut-out parts by numbers before
rendering; a *lint* checks those numbers without rendering. A *contact sheet* shows every pose side by side. In an
action, a *key* is an extreme pose; the *anticipation* is the counter-move before it, the *strike* the frame or two
that deliver it, the *recovery* the way back to rest.

## 1. Before drawing a frame

- **Read what the creature is and does.** Its role (what its action means in play), its nature (bird, lizard,
  golem, fox), and what it carries. Each loop has a job:
  - the idle is calm and alive;
  - the move travels in the creature's own gait;
  - the action says what it does.
- **Ask whoever owns the art what should change, if anything.** Treat their notes on earlier animations as rules for
  the next ones.
- **Plan the loops' lengths and the frame rate the game plays them at.** The motion must read at 1×, at that rate.
- **Look at the silhouette first.** Fill the approved drawing in one flat colour and view it at 1× beside the sprites
  it will stand with, in the smallest view the game has. Where the limbs merge with the body, the motion will not
  read either. Separate the interior (a tone step, an ink line) only where a limb crosses the body.
- **Every key pose of an action changes that silhouette.** Filled flat, with its effects, a key (the strike, the
  crouch, the apex) overlaps the rest pose by under 90 % (IoU). Push a key that fails: a longer reach, a lower
  crouch, a higher jump, about 30 % past what feels right. An idle keeps its silhouette.
- **Check that the drawing holds what the loop needs, and say so first when it does not.** This method moves the
  drawing's own pixels: it cannot show a side the drawing does not show. A figure drawn standing, turned to the
  viewer, has no side-on stride and no arm raised overhead in it; a closed cloak has no lining to show when it
  opens. Such a loop needs new drawings (section 4), and no amount of posing the cut makes them. Tell whoever asked
  before building, and offer what the cut can do (a breath, a sway, a lean) or key poses drawn or generated anew.
  - What this cost when it was skipped (one character, a cloaked wizard with a staff, against the hand-drawn sheet of
    the same figure): in the hand-drawn 10-frame idle, 16 % of each frame's pixels on average, 30 % at the deepest
    pose, matched no part of the first frame however it was shifted; thirteen cut parts fitted to every frame by
    pixel difference (a whole-pixel shift and a row shear each) still left 29-39 % of the pixels wrong at the
    deepest poses; and the cut-out walk and attack were nowhere near the drawn ones, whose poses the first frame
    does not hold. Three cut-out versions were judged worse than the hand-drawn loops by the one viewer who played
    them.
  - Cloth that changes shape (a cloak opening, a robe swinging round the legs) and a body that turns are the usual
    cases. A rigid body with limbs, a tail and wings (the showcase's creatures) is what the cut suits.

## 1b. Map the body first: `body_parts.py` (landmarks by eye, edges by measure)

A silhouette alone cannot tell what a shape is. A held bow and an arm, a quiver and a wing, hair and a fin, a cape
and a tail, a staff's head and an ear are the same to a skeleton. On a private set of 38 hand-drawn reference
drawings (humanoids, quadrupeds, fliers, serpents, insects and others; not included), the automatic map below got the
body plan of only 13, and even those had most parts named wrong (a bow called an ear, a cape a fin, a tail on a
human). So the work is split:

- **Recognise, by eye (coarse):** for each part, a *bone*: 1 to 4 points down its middle, in the drawing's pixels.
  Examples: crown and chin; shoulder, elbow and hand; hip, knee, ankle and toe; a cape's collar and hem; a bow's
  tip, grip and tip. A rough line is enough: it only has to lie inside the part, clear of its edges. One end is
  exact: a part that hangs from a parent starts AT its joint, where it leaves the parent (a leg at the hip line,
  not up in the rump; a head where the neck meets it; a finger at its knuckle).
- **Measure, by the tool (exact):** it finds the drawing's dark ink lines and flat colour patches, and grows every
  part from its bone over the figure along the cheapest path. Crossing ink, a colour edge or a patch border costs;
  entering a colour unlike any under the part's own bone costs per pixel. So parts meet where the drawing draws
  them apart, and a leg does not flood the cape behind it. Shading (a lightness step within one hue) is no edge.
  Where the drawing gives none (one fur from back to paw), the joints decide: a part never grows behind its joint
  or sideways along it, and a parent never crosses into a child past it.
- **Look at the cut** (`NAME_parts.png`) before rigging from it: each limb starts at its joint, the torso runs
  whole from rump to chest, the head holds the skull, a tail keeps off the rump's edge, a near leg stops at the ink
  line before the far one. A part inside its parent (a jaw in the head) shows hatched inside it. A wrong cut is a
  joint marked in the wrong place; move it and run again.

```
python -I ${CLAUDE_SKILL_DIR}/body_parts.py drawing.png --grid --out DIR    # a labelled grid, to read coordinates
python -I ${CLAUDE_SKILL_DIR}/body_parts.py drawing.png marks.json --out DIR --name NAME
python -I ${CLAUDE_SKILL_DIR}/body_parts.py --selftest
```

- **marks.json:** `{"parts": {"arm_near": {"kind": "arm", "parent": "torso", "bone": [[x, y], ...]}, ...}}`.
  - The bone's first point is the pivot, where the part joins its parent.
  - A `null` in a bone breaks it. Use it for a part seen in pieces: a staff above and below the hand that holds it,
    a cape seen on both sides of the legs. **Every visible piece of a part needs a bone piece**, or a neighbour
    takes it.
  - `kind` is free text, copied into the output for your own code (the cut does not read it). Common words: head,
    neck, torso, pelvis, arm, hand, leg, foot, tail, wing, fin, ear, horn, antenna, jaw, hair, mane, cloth, prop,
    pack, shell, tentacle, crest.
  - Name what the drawing shows: no tail on a person, no ears in a hood. Held and worn things are their own parts
    (prop, pack, cloth), parented to what holds them, because they move apart from the body.
- **How to place bones:** make the grid, read each part's middle from it, and zoom crops where parts crowd (hands,
  feet, a far leg). A thin part (a bowstring) drawn in ink alone may have its bone on the ink: the tool keeps it on
  ink.
  - **A long body in colour bands** (a snake's dark back and pale belly) split into segments: a bone only along the
    middle splits the segments lengthwise along the bands. Add a short piece across the body at each segment's
    ends, so the seams run across.
  - **A thin strap or cord:** put its bone on its own colour, measured, not by eye. Otherwise it floods the dark
    shapes it lies on.
  - **A body part with no ink between it and the next** (head and chest in one black, a whale's head and back):
    the line is placed by eye, where the colour or the form changes. Add a bone piece on each side near the line.
  - **Near and far** come from shading, overlap and size: the brighter, overlapping, larger limb is near.
  - **A hand gripping a prop:** a prop's bone run through the fist takes the fingers with it, and they part from the
    arm as soon as the two move differently. Carry the arm's bone on to the fingers and break the prop's bone
    (`null`) across the grip. On a wizard's staff hand this moved all 24 hand pixels to the arm, where 10 had gone
    to the staff.
- **Out:**
  - `<name>_parts.png`: each part tinted, with its outline, bone and name;
  - `<name>_patches.png`: the patches and ink the cut follows;
  - `<name>_parts.json` gives each part's kind, parent, pivot, area share, bbox, piece count and numeric label.
    Its `poly` field sketches the largest piece for the overlay.
  - `<name>_labels.png` is the cutting mask at drawing resolution. Background is 0. Each part's pixels have its
    JSON `label` value (in older exports, its position in the parts list, counting from 1).
- **Checks it prints** (`CHECK:` lines; the exit code is then 1), each a thing to fix and run again:
  - a bone point off the figure (snapped when near), or a bone wholly off it;
  - a part with no pixels, or in pieces whose second is 12 px or more and 8 % or more of the part (a part whose bone
    is broken by `null` is meant to be in pieces; the `pieces` count on each part's line counts every fragment and
    is no fault by itself);
  - a bone whose own pixels ended in another part (the bone strays over a neighbour);
  - a part much of whose area is a colour not under its bone (a piece of another part with no bone of its own);
  - pixels apart from the body with no bone, given to the nearest part (sparks, embers).
- **Then look at the overlay, zoomed,** part by part, before cutting the rig. The check list does not see a
  boundary that is merely a little off.
- **What it was proven on:**
  - A selftest figure whose silhouette cannot be split: an arm across the chest, a staff through the hand, a cape
    behind the legs, a bowstring. Every part scores IoU ≥ 0.8.
  - Looked at by eye on the 38 reference drawings: humanoids with weapons and props, quadrupeds carrying loads,
    fliers (birds, bats, a dragon), swimmers (a manta, an eel, a whale), serpents, insects, a crab in a shell, a
    golem, lizards and small mammals.
- **What it handles that a plain colour cut would not:** a dark body tone close to the background stays figure
  (background is what is like the border colour *and* joined to it); a colour patch shared by two parts is split
  rather than given wholly to one; dark cloth is not taken for an ink line (a part follows ink alone only when its
  bone lies 90 % on ink).

### creature_map.py: a first look only

Before the landmarks, the older automatic map can give a first guess at facing, ground line and spine. Do not take
its part names. It reads the drawing's silhouette only, so it sees shapes, not what they are (see above).

```
python -I ${CLAUDE_SKILL_DIR}/creature_map.py drawing.png --eye-at X,Y [--floating] --out DIR --name NAME
python -I ${CLAUDE_SKILL_DIR}/creature_map.py --selftest
```

- **Eye:** give the eye with `--eye-at X,Y` (sure), or `--eye #rrggbb` (only when that colour is found nowhere
  else). The head is the eye's end.
- **Floating:** pass `--floating` for anything that flies, swims or hovers: a single drawing cannot show whether a
  creature stands or floats.
- **How it reads a drawing:**
  - the silhouette, then a chamfer distance transform for its thickness;
  - a Zhang-Suen skeleton, its spurs pruned by width, with junctions found by crossing number;
  - the spine: the thick trunk's core, out to the eye at the front and at the back to the skeleton end that is
    straightest on and heaviest;
  - twin forks (two legs under an upright body) cut back so both are limbs;
  - each skeleton end its own limb, with a geodesic Voronoi for its pixels;
  - each limb named only by where it joins: ears and horns on the head, legs, arms and wings on the trunk, fins
    on the tail.
- **Body plans:** quadruped, biped (upright or leaning), hexapod, octopod, winged quadruped (dragon), flier,
  serpent, swimmer, floater with tentacles, floater, blob. The selftest draws a clean shape of each and checks the
  plan it reads. The fish is checked loosely: swimmer, flier or floater all pass, since side-on fins look like
  wings to a silhouette.
- **Its limits:** it reads the selftest's clean shapes, and fails on real art. On the 38 reference drawings it got
  13 plans right and named most parts wrong. Hidden far legs, fur, held things, capes and hair defeat a silhouette.
  Use body_parts for the parts. It takes one drawing, not a strip of frames.

## 2. The rig: the reference cut into parts

Choose the way by the drawing you start from:
- **The drawing is already at game size** (pixel art drawn at the sprite's own size): pose it at that size and never
  shrink it. Follow the game-size rules below, then the steps, leaving out step 5.
- **The drawing is a large painted reference:** work at the reference's own resolution and bring every frame down
  at the end (step 5, `shrink.py`). This keeps the art's detail; the cuts and turns are hidden by the shrink.

**At game size** every pixel of the drawing is a pixel of the sprite, so nothing may be resampled: a pixel turned
or scaled a fraction comes out as a new tone, and the texture crawls. Move the drawing's own pixels instead. The
working example is `examples/showcase/` in this repo (each creature's `*_rig.py`, and its `animate.py` docstring
for the loops); where only `skills/` was copied, it is at https://github.com/therwn/limberpix/tree/main/examples/showcase.
- **Place every part at whole-pixel offsets.** A fractional place needs resampling.
- **Bend a leg, a neck or a tail row by row between its joints:** the rows at one joint move by that joint's offset,
  the rows at the next by its own, the rows between by the mix, each row rounded to whole pixels; a row moved down
  past the next row's place is repeated into the gap. The limb curves and keeps every drawn pixel, and a stretch
  repeats a row instead of tearing. A lift shortens only a limb's narrow segment, so it keeps its mass.
- **Move the body whole, or stretch it in whole-pixel column steps** (each column moved by its own whole offset, a
  gap repeated). Never tilt it by a lone pixel: a step in its topline reads as a torso cut in bands (`split`).
- **Turn a part about its joint with three shears** (its rows, then its columns, then its rows again, each moved
  whole): every pixel is kept once, with no hole and no doubled pixel at any angle, and nothing is resampled. A paw
  folding at the wrist, a jaw opening.
- **Draw the outline last, on the posed frame.** Lay the parts back to front; fill a small pocket of air that two
  crossing legs close with the far leg's shadow (at 1× it reads as a hole through the body); then, where a pose has
  opened an edge, give the edge pixel the line (the lit line where the air is above or to the left, the ink
  elsewhere); then take off a leg pixel left with air on three sides, a burr the sliding rows leave. The parts keep
  the drawing's own outline: only an edge a pose uncovers, fill the drawing had inside, is lined anew, so the
  silhouette stays closed whatever the pose.

1. **Separate the drawing from its background** (by its colour or alpha).
2. **Cut each part from the approved drawing using the label image.** Select every pixel with that part's label.
   This keeps both ends of a staff behind a hand, the visible sections of a cape and the holes between them.
   Layer the pieces back to front: far limbs, tail, body, near limbs, head and ears.
   - Check detached pixels against the drawing before removing a stray sliver.
   - Anything that hangs from a part (a lantern on a tail, a flame on a tail tip, ears on a head) is a *child*. It
     moves with its parent and then by its own motion.
   - A turning part shows its cut. Put the pivot where the drawing hides it: under an overlapping part, or at a
     collar, band or change of material. Draw the piece the overlap hides rather than leave a gap.
3. **Move each part:**
   - **Wings seen side-on:** foreshorten them about the shoulder. Squeeze them upright, take them edge-on at
     mid-stroke, and flip them under the body on the downstroke, in the idle too (depth and far-wing rules in
     3.5). Never turn a side-on wing like a door.
   - **Spread wings (front or 3/4 view):** turn them about the shoulder *point*, tips sweeping down past the body.
     A vertical squeeze moves only their top edge.
   - **Torsos:** one piece. Bend it by a shear or a curve spread over its whole length, or turn it whole about a
     pivot. Never move a hip band and a shoulder band rigidly by different amounts: where they meet, the back or
     the belly line shows a 1-px step the drawing does not have, and the body reads as two pieces (`split`). A
     1-px bend has to step somewhere: put the step where the line already slopes.
   - **Legs:** shear them below the hip (each row shifted in proportion to its depth below the joint), so the top
     stays joined. Turning a leg opens a wedge at the hip and shows the cut's straight edge. The foot swinging
     forward lifts.
   - **Tails and long appendages:** a chain. The root turns first, and each segment after it turns a beat later
     and a little more. A tail that only stretches, or moves only at its tip, is dead.
   - **Limbless bodies (snakes, eels, fish):** bend the body along its own spine. Find the middle of the body in
     each column from the neck back to the tail tip, then move every pixel along the spine's normal (across the
     body) by a wave running from head to tail, none at the neck. The S travels, and the body keeps its thickness.
     - Never move whole columns up and down: at pixel scale it reads as hatching, scanlines sliding through the
       art.
     - Never use rigid segments turned at joints: each joint breaks the back's outline into a step, which reads as
       a chain of boxes.
     - Fins and anything else riding the body bend with it, along the same spine.
     - A raised neck leans by shearing from its base.
     - Pin the wave where the belly lies on the ground, and never re-seat a bent frame by moving it whole (3.7).
   - **Long flowing parts on a solid body (manes, comet tails, flame tails):** a chain of two or three segments,
     each turning about its joint a beat after the one before. Give each joint an overlap strip so no gap opens.
   - **Fins and sails standing on a back:** shear them from their base (the base row stays on the back). Turned,
     they break off the back at their root.
   - **Heads:** turn them on the neck. Nod on each step of the walk, look about in the idle, rise for the action.
     Eyes and features move with the head. At 1-px steps carry a rise or a bow with the body: the trunk, the neck
     and the head on the same pose (MOTION.md 3.0; a chain taking it a pose a part reads as a shiver). Never step the
     head alone by a lone pixel after a long hold while the rest stands still: it reads as a jerk (`hitch`).
   - **Ears, crests, whiskers, antennae:** they ride the head; a flick now and then in the idle rides a pose on which
     the body moves too.
4. **Hide the seams:**
   - A child gets a strip of overlap past its cut, drawn under its parent, so no gap opens when the two turn apart.
   - Where a part reveals body the drawing never showed, fill it with the body's shade up to a line, sparingly. A
     big flat patch reads as a hole.
5. **Bring each frame down on one fixed grid at one fixed scale,** with `shrink.py`:
   ```
   python -I ${CLAUDE_SKILL_DIR}/shrink.py rest.png --size W,H --colours 16 --out DIR --name rest   # the rest frame, once
   python -I ${CLAUDE_SKILL_DIR}/shrink.py pose.png --size W,H --palette DIR/rest_shrunk.png \
          --rest DIR/rest_shrunk.png --out DIR --name pose                                            # every other frame
   ```
   - Pin the grid to the union of all poses of every loop, sized from the farthest reach (a lunge, a breath, a wing
     tip), so still parts land on the same pixels in every frame and no reach is cut by the cell edge. Crop every
     frame to that one box before shrinking it; `--size` is the box's size in game px.
   - Each game pixel reads its own cell of reference pixels:
     - it is drawn when 0.42 of the cell is figure (`--cover`; about 0.3 for a creature with a narrow wing or a
       thin tail joint, which would otherwise break);
     - the contour, the reference's near-black line, is read apart from the fill: a cell is line when the contour
       fills 0.45 of it, or 0.12 of it and it is the line's crest across the line. A line thinner than a cell
       stays whole and one pixel wide. Left in the vote, it loses to the fill and the outlines break;
     - the fill is voted: every other reference pixel is snapped to the palette first, and the cell takes the
       commonest colour. Never average the cell and snap the average: the average is a tone the cell does not
       hold, and it changes with every small move. On painted references averaging left over twice the lone
       pixels and changed about twice as many pixels under a fifth-of-a-cell move (REFERENCES.md).
   - Snap the colours to the rest frame's tones: shrink the rest frame once with `--colours` (10-12 tones for a busy
     texture, 16-18 for a plain one) and give its result to every other frame as `--palette` and `--rest`, one
     palette for every loop. Every frame uses only the approved drawing's colours plus declared glow and effect
     colours. A sub-pixel mid tone comes from the drawing's own ramp.
   - Put back the eye and the small marks the shrink loses, at their place in the reference, moved with their part.
   - Drop a pixel left with no neighbour: a turned part's edge leaves them.
   - Draw a one-pixel outline last, on every frame.
6. **Render a part strip beside every loop:** the same frames with each part filled in one flat colour
   (body_parts' label image gives the map). Read and approve the motion on it at 1× before the textured frames:
   paths, lags, foot contacts and near and far swings show there first, with no texture in the way. Give it to
   pixel-anim-check too, where it takes one, to track each part. A part keeps its area outside a squash or a
   foreshortened wing: on a part of 40 px or more, a change over a tenth (and over 2 px) is a cut or a pivot gone
   wrong. A smaller part changes more from rasterising alone.

## 3. Motion that reads in pixels

The numbers are for loops played at 30 fps; scale the frame counts with the game's rate.

**Default rules.** These come first, and nothing below loosens them:
- **Move the body's mass on every pose; never one small part alone.** At sprite scale each whole-pixel step is seen. A
  pose that moves only an ear or a muzzle on a beat of its own while the body holds reads as a click, and parts that
  take a rise a pose apart (the trunk, then the neck, then the muzzle, then the ears) read as a shiver, not as overlap.
  A free tip (a tail's end, a plume) may finish the body's move a pose late, as follow-through. Slynyrd 52's idle moves
  the torso on every frame (its head holds on two of them) and his walk cycles move the whole figure; the rule's general
  form is this repo's, from its showcase (one person's judgment), and the blog does otherwise where it suits (MOTION.md
  3.0).
- **Further from the body, more pixels a pose** (Slynyrd 52): the torso and head 1, the limbs 2, the tips 2-4. That
  spread is what reads as weight and overlap.
- **Move parts joined by a seam as one piece** (this repo's showcase; the blog does not teach it). At 1-px steps a cut
  layer moved a pixel off its neighbour shows the cut: a head off its neck, a neck off the chest it lies over, a back
  lifted over a still belly while the neck rides the head. Lift the whole torso with its neck and head (the legs stretch
  under it), and give the lag to a free tip, at most a pixel off its parent a pose.
- **Ease with timing: slow over the top, quick on the drop.** An idle breath of 8 poses held 3 frames over the rise and
  the top and 2 on the drop (Slynyrd 52), the body a pixel up, at rest, a pixel down.
- **A planted foot moves with the ground every frame** (this repo's showcase). Over a road scrolling a pixel a frame,
  walk on ones; a foot held two frames falls behind the road and catches up, and the feet judder.
- **Move whole game pixels only** (the sub-pixel sources of MOTION.md 3.1). A fractional move resamples the sprite every
  frame, and its texture crawls.
- **Turn in steps of about 1.5° and hold each pose 2 frames** (this repo's practice, 3.1). Smaller turns every
  frame resample the art and crawl the same way.
- **No column waves** (this repo's practice, 3.7). Columns moved up and down read as hatching, scanlines sliding
  through the art.
- **A tail moves as a chain; the head moves with the body** (the chain sources of 3.10; Slynyrd 52). A stiff tail reads
  as a board, a head pasted in place while the body moves as a mask.
- **A walker's body rises on each step** (Slynyrd 50; saint11's walk, 3.8). Legs stepping under a body that never moves
  read as a board on wheels.
- **Keep the usual hold under 4 frames, and never let an idle stop dead.** A tempo of 4+ frame holds (under 10 updates a
  second at 30 fps) reads as a dropped frame rate when only parts move (this repo's calibration set), and a dead stop as
  a frozen statue (this repo's choice: Slynyrd 39 uses a still idle). Where every pose is the body's, the blog holds
  longer, and so may you: a walk whose every pose is a new stride drawing up to 5 frames (the blog's walks 100-280 ms a
  pose), an idle whose every pose moves the whole body up to 0.4 s (12 frames), one pose twice the others (Slynyrd 55,
  measured: 200, 200, 400 ms). One longer hold belongs only where the motion stops: a sway's turn (a 1-2 frame base
  doubled, 4 at most), an idle's rest (3.3), an action's held keys (two at most, 3.13). In a running motion it is a lost
  update, which the check misses among twos: the pose list of section 5 catches it.
- **Keep the creature's look exactly: do not redraw it** (the art owner's notes, section 1). A redrawn creature reads as
  a different one.

The thresholds in the motion guide say how to keep motion dense and smooth *inside* those limits. No source gives a pixel
threshold for judder, so they were fitted to a private calibration set: 39 animated creatures, with 15 accept or
reject judgements on them by one reviewer (not included). Treat them as tested defaults.

Read the relevant sections of [MOTION.md](MOTION.md) when planning or diagnosing a loop.

- Section 3.0 covers smooth motion at sprite scale (the body on every pose, seams, easing, hold lengths), measured
  on Slynyrd's animations; read it first.
- Sections 3.1-3.4 cover pixel steps, cadence, holds and bobbing.
- Sections 3.5-3.8 cover wings, hovering, snakes and walking gaits.
- Sections 3.9-3.12 cover heads, overlapping motion, seams and effects.
- Sections 3.13-3.14 cover attacks, jumps and landings.

## 4. Sprite sheets with few drawings (AI-generated or hand-drawn)

AI frames redraw the whole texture each frame, so it crawls (`shimmer`), and they redraw the head, so the face
reshapes.
- Prompt only the motion (which loop, how many frames, the pose sequence). Give the approved drawing as the
  reference. Keep the frames that hold the creature's look.
- **Timing:** hold each drawing **≤ 3 frames, preferably 2**. Cycle the beat twice a loop rather than holding
  longer. A long rest only as a moving hold (3.3).
- **An idle never borrows walk drawings.** If a shuffle is kept, it is a whole step that ends where it began, eased
  in and out (holds 3, 2, 2, 3), with a breath running under the rest.
- **Lock what must not change:**
  - draw the body once (keep everything below a line fixed) and the **head once**: paste one approved head, with
    its jaw, at each drawing's head position placed by the eye, keep the frame's own near-wing pixels on top, and
    re-ink the seam;
  - read every cell on **one shared block grid**, the rest cell's lines moved by the cell's offset. A grid fitted
    per cell can merge a narrow snout column.
- Or build the loop from the rig instead.
- Why: a sheet that redraws the head in every cell flattens the mouth in some of them, and the face reads as redrawn
  between poses.
- **Boil is not a pose.** A generated clip often changes only a 1-px trace along every outline between poses, then
  changes it back. Drop such a frame. A sub-pixel lead (3.1) also changes the edge, but once and in one direction,
  and it stays. Count real poses per second, not frames: boil frames hide a rate under 10/s.
- **Thin a clip evenly** (every 2nd or every 3rd frame), then re-time it to its intended length. Thinning by hand
  in uneven steps (1, 2, 2, 1) slows the motion and jerks it.
- **Scale and anchor:** generated cells drift (a height swing of ±8 % is common). Normalise each cell's scale to the
  approved drawing. Anchor walkers by the feet and fliers by the body centre.
- **One palette:** map the whole sheet to one palette in one pass; quantising each cell alone makes the colours
  flicker. Clear the key colour's fringe before quantising, or it turns to specks. pixel-anim-check's `--key` reads
  only that exact colour as air, so the fringe must be gone before it too. Then remove orphan pixels and
  close the outlines.
- **Room:** give a generated cell 1.3-1.8× the figure's longest side, anchored opposite the action (at the feet for
  a jump, behind the creature for an attack). Pad interpolation keys to one size yourself. A reach cut by the cell
  edge cannot be put back.
- **Part continuity:** a part never appears, vanishes or changes sides between cells (a held shield, a weapon
  passing to the other hand). Look for it on the contact sheet; a colour group that drops to a third of its usual
  count, or doubles, for 1-3 frames is the sign.
- Sources: Sorceress Gamedev (boil, thinning, drift, one palette, part swaps); SpriteCanvas; Pixel Engine (Reframe
  room; per-frame quantising); PixelLab (interpolation keys, one colour cap per animation).

## 5. Check, look, then show

1. **Before rendering**, print each loop's pose tuples per clock tick and check:
   - no two identical ticks outside a turn;
   - the lift peak, in game px after rounding, lies outside 0.5-0.9;
   - every squeezed wing crosses 0 in the idle and the move;
   - no hidden-edge run sits at a turn.
2. **Rig lints.** If your pipeline has a rig, lint its pose curves from the pose function alone, with no
   rendering: they see causes a frame cannot. These are checks to write in your own pipeline; these skills do not
   ship them. For example:
   - `stroke`: a squeeze-driven wing in the idle or move with a squeeze range ≥ 0.2 must go below 0 (actions may
     hold the wings high on purpose);
   - `hide`: a run of an edge-hidden part (|s| < 0.35) must have opposite signs on either side and last ≤ 5 frames;
   - `lift`: rebuild the lift exactly as the pipeline rounds it, in game px; fault when an excursion's duty (its
     length over the frames between excursions) is under 0.18, warn when the peak lies in [0.5, 1.0);
   - `seat`: the step that seats a figure on its ground line must never translate a whole frame; assert that no
     frame moved.
3. Run **pixel-anim-check** on every loop (idle, move and action) and fix every fault (`choppy`, `snap`, `tick`,
   `hop`, `vanish`, `shallow`, `reshape` and the older ones). Give it every input it takes (its SKILL.md lists
   them): which actions are strikes and their direction, the part strip (2, step 6), and the approved drawing at
   game size with its palette, so it can compare the rest pose and the colours with it.
   - A clean run is a floor, not the result. Do not tune a loop toward a number in place of the look: not the fault
     count, and not a pixel match with a reference animation either. A cut-out idle brought 40 % nearer a hand-drawn
     one by pixel difference was judged worse, played, than the version before it. If a change is meant to make the
     motion better, the person who plays it says whether it did.
4. Read the eye's row track and the per-step change list. A 2-3-frame excursion, or a long hold followed by a big
   step, shows there before it shows in a GIF.
5. Look at the part strip, then the contact sheet and the GIF yourself, zoomed and at 1×:
   - extreme poses at the reference's own size, where cut remnants show first;
   - seams, likeness, life in every part, the idle standing;
   - a walk over a ground line scrolling at the game's speed, where a sliding foot shows.
6. Show the loops as a GIF (and the attack, with its effects, in place). Say what was checked and what is still
   doubtful. If the project has a review step (an art lead, a client, the person you are working with), the
   animation goes into the game after that review.
7. When a reviewer or player reports a fault, fix the animation and rerun the check. If it missed a repeatable
   defect, describe the missed case. When the task includes updating the checker, add a selftest for that case.
