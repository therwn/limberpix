---
name: pixel-animate
description: Animate a pixel-art character, creature, pet or monster from an approved drawing (idle, walk/move, an action or attack) so it moves like a living thing and still looks like its drawing. A method for any engine or pipeline (cut the reference into parts, pose them at full size, shrink every frame on one fixed grid), with the principles that make sprite motion read (chains, overlapping action, standing idles, wings, legs) and the faults to avoid. Use when making or remaking any sprite animation, when choosing how a creature attacks, or when told an animation looks stiff, broken or not like its drawing; check the result with pixel-anim-check.
---

# Animating pixel-art creatures

The goal is an animation that keeps the approved drawing's look and moves like a living thing. Do not redraw the
creature. A redrawn one that moves well but no longer looks like itself reads as a different creature, and a
faithful one that moves like a cut-out reads as paper. Work from the approved drawing.

**Paths.** The scripts sit next to this file. Inside Claude Code, `${CLAUDE_SKILL_DIR}` is that folder; outside
Claude Code, read `${CLAUDE_SKILL_DIR}` as the folder holding this SKILL.md. Python 3.8+ with numpy and Pillow.
Sources named below are linked in [REFERENCES.md](REFERENCES.md).

**Terms.** *Game px*: one pixel of the sprite as the game shows it; *reference px*: one pixel of the larger drawing
the animation is made from. *On twos*: a new drawing every 2nd frame (a *hold* of 2); *threes*: every 3rd. A
*moving hold* is a pose that looks still but keeps a small motion. A *rig* poses cut-out parts by numbers before
rendering; a *lint* checks those numbers without rendering. A *contact sheet* shows every pose side by side.

## 1. Before drawing a frame

- **Read what the creature is and does.** Its role (what its action means in play), its nature (bird, lizard,
  golem, fox), and what it carries. Each loop has a job:
  - the idle is calm and alive;
  - the move travels in the creature's own gait;
  - the action says what it does.
- **Ask whoever owns the art what should change, if anything.** Treat their notes on earlier animations as rules for
  the next ones.
- **Plan the loops' lengths and the frame rate the game plays them at.** The motion must read at 1×, at that rate.

## 1b. Map the body first: `body_parts.py` (landmarks by eye, edges by measure)

A silhouette alone cannot tell what a shape is. A held bow and an arm, a quiver and a wing, hair and a fin, a cape
and a tail, a staff's head and an ear are the same to a skeleton. On a private set of 38 hand-drawn reference
drawings (humanoids, quadrupeds, fliers, serpents, insects and others; not included), the automatic map below got the
body plan of only 13, and even those had most parts named wrong (a bow called an ear, a cape a fin, a tail on a
human). So the work is split:

- **Recognise, by eye (coarse):** for each part, a *bone*: 1 to 4 points down its middle, in the drawing's pixels.
  Examples: crown and chin; shoulder, elbow and hand; hip, knee, ankle and toe; a cape's collar and hem; a bow's
  tip, grip and tip. A rough line is enough: it only has to lie inside the part, clear of its edges.
- **Measure, by the tool (exact):** it finds the drawing's dark ink lines and flat colour patches, and grows every
  part from its bone over the figure along the cheapest path. Crossing ink, a colour edge or a patch border costs;
  entering a colour unlike any under the part's own bone costs per pixel. So parts meet where the drawing draws
  them apart, and a leg does not flood the cape behind it.

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
- **Out:**
  - `<name>_parts.png`: each part tinted, with its outline, bone and name;
  - `<name>_patches.png`: the patches and ink the cut follows;
  - `<name>_parts.json`: per part its kind, parent, pivot, area share, bbox, outline polygon and piece count;
  - `<name>_labels.png`: one grey level per part, for code that cuts by it.
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

Work at the reference's own resolution and bring every frame down at the end. This keeps the art's detail; the
cuts and turns are hidden by the shrink.

1. **Separate the drawing from its background** (by its colour or alpha).
2. **Cut parts with polygons** (body_parts' outlines, or its label image), back to front: far wing or far legs,
   tail, body, near wing or near legs, head, ears.
   - The body is everything not in a part.
   - Keep only the body's main piece, so no sliver of a cut is left floating.
   - Anything that hangs from a part (a lantern on a tail, a flame on a tail tip, ears on a head) is a *child*. It
     moves with its parent and then by its own motion.
3. **Move each part:**
   - **Wings seen side-on:** foreshorten them about the shoulder. Squeeze them upright, take them edge-on at
     mid-stroke, and flip them under the body on the downstroke, in the idle too (depth and far-wing rules in
     3.5). Never turn a side-on wing like a door.
   - **Spread wings (front or 3/4 view):** turn them about the shoulder *point*, tips sweeping down past the body.
     A vertical squeeze moves only their top edge.
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
     Eyes and features move with the head.
   - **Ears, crests, whiskers, antennae:** they follow the head a beat late and flick now and then in the idle.
4. **Hide the seams:**
   - A child gets a strip of overlap past its cut, drawn under its parent, so no gap opens when the two turn apart.
   - Where a part reveals body the drawing never showed, fill it with the body's shade up to a line, sparingly. A
     big flat patch reads as a hole.
5. **Bring each frame down on one fixed grid at one fixed scale:**
   - Pin the grid to the union of all poses, so still parts land on the same pixels in every frame.
   - Snap the colours to the rest frame's tones; fewer tones for a busy texture.
   - Put back the eye if the shrink loses it.
   - Draw a one-pixel outline last.

## 3. Motion that reads in pixels

The numbers are for loops played at 30 fps; scale the frame counts with the game's rate.

**Default rules.** These come first, and nothing below loosens them:
- **Move whole game pixels only.** A fractional move resamples the sprite every frame, and its texture crawls.
- **Turn in steps of about 1.5° and hold each pose 2 frames.** Smaller turns every frame resample the art and crawl
  the same way.
- **No column waves.** Columns moved up and down read as hatching, scanlines sliding through the art.
- **A tail moves as a chain; the head and ears move.** A stiff tail reads as a board, a still head as a mask.
- **A walker's body rises on each step.** Legs stepping under a body that never moves read as a board on wheels.
- **Never hold a frame 4 or more times inside a cycle, and never let an idle stop dead.** Long holds read as a
  dropped frame rate, and a dead stop as a frozen statue.
- **Keep the creature's look exactly: do not redraw it.** A redrawn creature reads as a different one.

The thresholds below say how to keep motion dense and smooth *inside* those limits. No source gives a pixel
threshold for judder, so they were fitted to a private calibration set: 39 animated creatures, with 15 accept or
reject judgements on them by one reviewer (not included). Treat them as tested defaults.

### 3.1 Whole pixels and sub-pixel motion

- **Whole pixels:**
  - A lift or bob of a fraction of a pixel resamples the whole body every frame, and its texture crawls. Round lifts
    to whole game pixels.
  - Small turns and scales do the same. Step them by about 1.5° or one level, held two frames, so each change is a
    step and never flips back a frame later.
- **Sub-pixel tone, for moves of 1 px or less** (a slow breath, a big head's bow): the leading edge's pixels may take
  a mid tone on the pose before the full step.
  - The tone changes monotonically and never flips back within 2 frames.
  - It never uses the ink colour.
  - It leads the whole-pixel move by 1-2 frames.
  - Never switch a few pixels on and off: that stutters.
  - Sources: someanimatorwannabe (Metal Slug's Fio); Tiny Warrior Games; Pixel Parmesan; saint11's sub-pixel GIF.
- **Thin parts and busy designs:** antennae, whiskers and spines thinner than a game pixel turn into outline and
  specks when shrunk, and a sprawling design turns to a dark clot. Make the sprite bigger first. Then widen a thin
  part only as much as it needs to stay joined (a few reference pixels): widened more, an antenna becomes a horn.

### 3.2 Cadence: holds against crawl

- **The rate:**
  - Continuous motion (a sway, a beat, a bob) gets a new picture at **15/s: hold 2**. This is the target.
  - **Hold 3 (10/s)** is the floor, and only for a uniform whole-body beat (a big, slow animal).
  - **Hold 4 or more inside a cycle is a fault, whatever the step size.** Six small idle poses held 6 frames each
    read as a dropped frame rate, even at 6-13 % of the figure a step.
  - The mean update rate (moves × fps / frames) is ≥ 10/s.
  - Holds of 3 read as smooth enough; holds of 4 read as a dropped rate.
  - Sources: Williams' twos (secondhand, animationpodcast and AWN); Wave Motion Cannon (threes and fours read
    jerky).
- **Turns:** at a sway's turn, and only there, a hold may double a 1-2 frame base, up to 4. Ease with smaller
  steps, never with longer holds: the longest frames set the perceived smoothness (Klein et al. 2023).
- **Lost updates:** a quantised curve can repeat a pose. A sway of 3-4° in 1.5° steps makes two ticks running
  identical, and a 3-frame hold becomes 6. To avoid it:
  - put all parts on **one clock** (`k // 2 * 2`); parts rounded on their own move on different frames and the
    motion stutters (`uneven`);
  - stagger their **phases** by 0.4-1.2 rad;
  - size the amplitudes so that *some* part changes on every tick;
  - list the pose tuples per tick before rendering: two identical neighbours outside a turn are a lost update.
  - Never lower the pose rate to silence `uneven`; stagger the phases instead.
- **One rate class per creature:** the idle and the move update at the same rate (ones or twos), so switching loops
  never shows a stall. The idle's median hold is under 3× the move's (Taylor & Francis on mixing ones and twos;
  Slynyrd 8).
- **A beat sampled in held steps:** sample half a step off the top (sin 60° = sin 120°: two poses running are one).

### 3.3 Stillness: the moving hold

- An idle never stops dead:
  - the longest run of identical frames is **≤ 12 frames (0.4 s)**, unless a discrete event (a blink, a glint, a
    glow step) falls inside it;
  - and it is ≤ 3× the median hold.
- After a still run of 10 frames or more, the first step is **under 25 % of the figure**. A bigger change eases in:
  its first and last steps are ≤ 60 % of its peak step, and the holds around it run 3, 2, 2, 3.
- A good model: one drawing, with a blink, a glow and a breath spread over the loop.
- An action may hold an anticipation and then spring; this rule is for the idle.
- Sources: Animation Mentor, "the moving hold"; AnimSchool, "never still"; Slynyrd 52 (extremes 100 ms, the middle
  50 ms); the twelve principles (slow in and out).

### 3.4 Lift and bob without ticks

- **The square wave:** rounded to whole game pixels, a 1-px lift is a square wave. With a peak of A game px,
  `round(max(0, sin)·A)` is up for `(π − 2·asin(0.5/A)) / 2π` of the beat: 0.16 at A = 0.58 (reads as a tick), 0.35
  at A = 1.07 (reads as a lift).
- **Choose:**
  - **A < 0.5 (no lift)**, the wings alone carrying the hover;
  - or **A ≥ 1.0** (1.05-1.2 keeps the body up a third of the beat);
  - **never 0.5-0.9.**
  - Write it as `px · round(max(0, sin))`, with `px` one game pixel at the reference's size, so the band cannot
    happen by accident. Check the peak after the pipeline's own rounding, in game px.
- **Dwell:** every whole-pixel level the body or the eye takes lasts **≥ 4 frames** at an extreme (≥ 3 on a smooth
  multi-level path), with at most 2 turns per beat.
- **The same band holds for every part, measured at the features:** a neck sway of θ about its base moves the head
  by `L·sin θ`. Keep that under 0.5 game px or over 1, add it to the lift, and check the **eye's** whole-pixel path,
  not the parts one by one. Keep a neck sway near ±1.5°: at ±3-5° the eye dips for 2-3 frames, which reads as a
  tick.
- **Timing:** a flier's body rises on the downstroke. Put the 1-px step on a frame where the wings also change,
  which masks it.
- Sources: Tsugumo ch. 10 (1 px is 4 % of a 20-px sprite); the sampled-sine math; PixelJoint TID 2095 and Tuts+
  (the body rises on the downstroke).

### 3.5 Wings

- **Side-on wings** (the shoulder-to-tip vector mostly vertical):
  - foreshorten by `s = sin θ` about the shoulder row: +1 raised, 0 edge-on, negative flipped under the belly;
    never turn a side-on wing like a door;
  - every idle and move **crosses 0**;
  - an idle beats *more slowly, never more shallowly*: depth ≥ 0.7 in `1 − (1 − cos)·depth`, lowest s ≤ −0.4
    (0.85-0.9 reads well on birds). A shallow idle depth such as 0.3-0.35 keeps the tip above the shoulder: only
    the top of the wing moves, and an edge-hidden far wing disappears at the turn. Both read as a broken flap.
  - Sources: ornithopter.org; corn-vanilla bird-flight analysis.
- **Spread wings** (mostly horizontal: a 3/4 or front view): turn them about the shoulder *point*, ±15-25° in a
  glide idle, ±30-45° in a beat. Squeezing such a wing vertically moves only its top edge.
- **The whole wing moves:**
  - tip travel ≥ 30 % of the wing's length, and the root half moves too;
  - at least 4 distinct wing drawings a beat, ideally 6-8, never 2;
  - the downstroke is broader and as long as or longer than the upstroke.
  - Sources: PixelJoint bat thread ("the whole wing flaps"); Slynyrd 25 (8-frame flap); Taylor & Francis flight
    chapter (3 in-betweens up, 5 down).
- **The far wing never vanishes:**
  - it may be hidden (|s| < 0.35) only *while crossing* edge-on, for ≤ 5 frames, never at a turn;
  - otherwise it keeps ≥ 25-30 % of its rest-visible pixels, and at least 3 game px;
  - on the downstroke its tip shows below the belly.
  - Source: Tuts+ flying bird ("a little should still show").
- **Beat period by size** (move loops; stylised): owl or drake 18-36 frames, with a glide; shrike, magpie or bat
  12-18; wren or lark 8-12; insects 2-4 a beat on twos, the body steady. An idle may beat once a loop. Sources:
  Pennycuick 1990; Jensen, Dyre & Hecksher 2024 (bigger, broader wings beat slower).
- **Optional, for big wings:** cut the lower feather mass as its own part, turned a beat after the wing (1.5°
  steps, held 2 frames).

### 3.6 Hoverers and insects

- Wings flutter about the shoulder on twos, fore and hind against each other (±8-14°), sampled half a step off the
  top. A faceted wing turned every frame resamples and its facets crawl.
- The body is steady (A < 0.5), or it drifts once a loop with each whole-pixel level held ≥ 1/3 of a beat. Never a
  half-cycle rigid lift peaking at 0.5-0.9 px: it reads as ticking up and down, not flying.
- Antennae and head run on their own slower beat, a beat late.
- Sources: Lynda insects course; measured on a mantis sprite (lift peak 0.58 → 1.15 px, duty 0.11 → 0.33).

### 3.7 Snakes and legless bodies

- **Idle:** the belly stays on the ground. The contact row and the contact columns are fixed (±1 column at the
  coil's ends), and no frame shifts the whole figure: lifting it reads as a hop. Life comes from:
  - the raised neck, sheared from its base, 1.5-3°, over 2-3 segments, each lagging 2-4 frames;
  - the head turning ±1.5-3° a beat after the neck;
  - a tongue flick, 2 frames out and 2 in, once a loop, in the head's still moment (it needs its own part);
  - the tail tip curling at right angles to the head, out of phase with it;
  - arches rising and falling ≤ 1 px; no constant breathing.
- **Spine op:** pin the wave where the belly lies on the ground, `d *= clip((ground − belly_y[x]) / H, 0, 1)` with H
  about 1.5 game px. Only the arches move; a trough never reaches the ground, so nothing has to be lifted back.
  Never re-seat a frame by translating it.
- **Move:** a travelling S from head to tail, its amplitude growing toward the tail, one wavelength in 12-24
  frames. The head runs on its own track. Contact points stay planted; crests rise ≤ 1 px; troughs never go below
  the rest ground row.
- Sources: PixelJoint TID 26707 (a coil on a flat base; the tail low and at right angles); Hu et al., PNAS 2009
  (lateral undulation keeps sliding contact); Character Animation 2D, slither chapter.

### 3.8 Walkers and quadrupeds

- **Gait:** a new leg pose every frame and the 1-px body bob riding it. The body rises a whole pixel over its
  planted feet as the legs pass under it, twice a stride, and sinks as they reach out. Legs stepping under a body
  that never moves read as a board on wheels. Raise every part but the legs, and give the legs an overlap strip
  upward so no gap opens at the hip. Do not hold the leg poses two frames with the bob on a step of its own: a held
  frame, a small leg step, then the whole body jumping reads as a hitch on every beat (`lurch`).
- **Idle: layers, each on its own phase,** staggered so no frame stops everything or moves everything:
  1. a breath from the belly up to the chest: 1 px, or a sub-pixel tone (3.1);
  2. a slow head drift or bow, the muzzle first and the poll a pose later;
  3. the ears a pose after the head, with one flick a loop;
  4. the tail as a chain, the middle leading and the tip following;
  5. a blink or an eye dart in any long stretch.
- **Weight on all four feet;** never caught mid-stride. A reference drawn mid-stride gets its legs drawn in.
- **A big part's 1-px move** (a head of 10-16 % of the figure) is staged over ≥ 2 poses: ears, then face, then neck
  on the bow; face, then neck, then ears on the rise. Avoid any single step that changes ≥ 8 % of the figure;
  when one must, hold it ≤ 2 frames. Horns can lead like ears.
- **Rate:** for example 18 poses held 2 frames, something changing on every pose, every moving region changing at
  least every 6 frames. A longer loop (about 2.4 s) makes a big animal's 1-px nod less of a metronome, if the
  player reads the frame count from the data.
- Sources: Game Developer, "Animating four-legged beasts" (head offset from hips and chest, tail last); Animation
  Mentor and AnimSchool (layered, never still); MoCap Online (base breathing, a slight head drift); Merck Vet Manual
  (resting breathing rates: a short loop can only stylise them); Slynyrd 52 (parts move different amounts).

### 3.9 Heads, mouths and features

- The head is a rigid part. The eye, the mouth line and the jaw move with it; the face never reshapes between
  frames, and a mouth never flattens as if cut.
- A jaw opens only on purpose (an action). It pivots at the hinge, behind and below the eye, never at the mouth
  corner.
- Each snout column's height stays within ±1 px of rest, and so does the snout-to-eye length.
- **Defining features:** a feature the creature is named for (lamp eyes, a gem, a glowing mark) must survive the
  shrink at a size that reads. When it melts to one pixel or into its neighbours, draw it back at game size (two by
  two for big eyes) in its own colour.
- Sources: WigglyPaint (the face centre does not drift); Tiny Warrior (keep key details crisp); Toon Boom and
  Godot cut-out joints (the pivot at the overlap's centre).

### 3.10 Chains and overlap

- Nothing starts or stops together: body, then head, then ears; root, then tail, then tip.
- In a chain each link lags its parent by **1-3 frames** (20-40° of phase in a 36-frame loop), the amplitude
  growing toward the tip. Lag 0 moves the chain as a board; a lag over a quarter loop detaches it. A tail catches
  up in about 0.3 s.
- Sources: Babbitt and Williams (successive breaking of joints); SIGGRAPH HyperGraph on follow-through; AzureLib and
  Houdini KineFX spring chains.

### 3.11 Seams

- The last-to-first step is ≤ 1.5× the median step.
- No duplicated closing frame: a repeated final pose doubles a hold.
- Sources: Schödl et al., Video Textures (transition cost); llamagen's sprite-sheet frame audit.

### 3.12 Idle, amplitude, light, effects, attacks

- **Idle:** the creature stands square, weight under it. It breathes and looks about. Never a frozen statue, never a
  walk on the spot.
- **Amplitude:** big enough to read at 1× (a move changes several percent of the figure a frame), small enough not
  to jitter.
- **Glow:**
  - Light only the creature's own light (its flame, crystal, ink, eyes), never the whole sprite.
  - Light it toward a colour that stands out from what it lights. White on a pale body vanishes; gold on parchment
    vanishes.
- **Effects** (sparks, motes, rings, streaks):
  - Give them their own few colours, so the check can tell them from the creature.
  - They start from where they belong: a breath from the mouth, sparks from the flame, streaks behind a dashing body.
  - Avoid shapes that read as symbols you did not intend.
- **Attacks:** give each attacker its own style that fits what it is.
  - A ranged creature looses a bolt or a breath; a melee creature lunges where it stands, or reels out and bites; a
    diving flier stoops in place and sends a cry; a gaze or curse stares a mark onto its foe.
  - Several creatures all darting to the foe and back looks cheap.
  - Time the hit to the frame that delivers it.
  - A blow that strikes several targets reads as one stroke passing through them: time each target's hit reaction
    to the frame the blow reaches it, not all together.

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
   `hop`, `vanish`, `shallow`, `reshape` and the older ones).
4. Read the eye's row track and the per-step change list. A 2-3-frame excursion, or a long hold followed by a big
   step, shows there before it shows in a GIF.
5. Look at the contact sheet and the GIF yourself, zoomed and at 1×:
   - extreme poses at the reference's own size, where cut remnants show first;
   - seams, likeness, life in every part, the idle standing.
6. Show the loops as a GIF (and the attack, with its effects, in place). Say what was checked and what is still
   doubtful. If the project has a review step (an art lead, a client, the person you are working with), the
   animation goes into the game after that review.
7. When a reviewer or a player points out a fault, fix it here, and ask whether the check could have caught it. If
   it could have, add that to the check, with a selftest case.
