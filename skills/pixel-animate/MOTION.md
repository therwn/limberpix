# Side-view sprite motion

Frame counts assume 30 fps. Scale them to the game's playback rate. Sources are in [REFERENCES.md](REFERENCES.md).

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
- **Other sub-pixel tricks.** Each changes a pixel once and keeps it:
  - *The highlight moves with the form:* on a round body (a shell, an egg, a dome) a breath or a small turn moves
    the highlight cluster 1 px while the silhouette stays. The light's direction never moves.
  - *Part first:* a long edge steps 1 px in 2-3 pieces over 2-3 poses, the middle first, then the ends. More pieces
    look bent.
  - *Interior after silhouette,* on a blob body with no separate head only: the outline drops first and the face
    follows a pose later; both rise together.
  - In a 1-px move, the in-between poses change only outline corners or anti-aliasing pixels (a few percent of the
    shift's change), leading the whole shift.
  - Sources: saint11 (< 1 Pixel Movement, Character Idle); Kiwi on sub-pixel animation; Pixel Overload.
- **Thin parts and busy designs:** antennae, whiskers and spines thinner than a game pixel turn into outline and
  specks when shrunk, and a sprawling design turns to a dark clot. Make the sprite bigger first. Then widen a thin
  part only as much as it needs to stay joined (a few reference pixels): widened more, an antenna becomes a horn.

### 3.2 Cadence: holds against crawl

- **The rate:**
  - Continuous motion (a sway, a beat, a bob) gets a new picture at **15/s: hold 2**. This is the target.
  - **Hold 3 (10/s)** is the floor, and only for a uniform whole-body beat (a big, slow animal).
  - **The tempo is what fails: a usual hold of 4 or more** (under 10 updates a second at 30 fps) reads as a low
    frame rate, whatever the step size. Six small idle poses held 6 frames each read as a dropped frame rate, even
    at 6-13 % of the figure a step.
  - The mean update rate (moves × fps / frames) is ≥ 10/s.
  - Holds of 3 read as smooth enough; holds of 4 read as a dropped rate.
  - **One longer hold belongs only where the motion stops:** at a sway's turn (below), in an idle's rest (3.3), on
    an action's held key (3.13). In the middle of a running motion it is a lost update (below): the check sees it
    only when the usual hold is 3+ (`choppy`) or at the loop's seam (`seam`), not as one 4-frame hold among twos, so
    check the pose list for two identical ticks outside a turn.
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
- **One-pose peaks:** a quantised turn that reaches a new step for a single pose resamples the part's edge, and a
  highlight lands on a neighbour for 2 frames (`speck`). Cap the swing below that step, or let the peak dwell 4+
  frames.
- **One rate class per creature:** the idle and the move update at the same rate (ones or twos), so switching loops
  never shows a stall. The idle's median hold is under 3× the move's (Taylor & Francis on mixing ones and twos;
  Slynyrd 8).
- **A beat sampled in held steps:** sample half a step off the top (sin 60° = sin 120°: two poses running are one).
- **Slower sources do not loosen this.** Many hand-made guides time walks and runs at 80-150 ms a drawing (7-12/s)
  and hold idle drawings 200-800 ms (6-24 frames at 30 fps). Their sprites are 16-48 px, and each pose change is a
  clean 1-px step of a whole part. The 15/s target, the 10/s floor and the 4-frame hold limit were judged on larger,
  textured creatures, and they stay. Take spacing from those sources (one big strike step, eased steps elsewhere),
  not their slow rate.

### 3.3 Stillness: the moving hold

- An idle never stops dead:
  - the longest run of identical frames is **≤ 12 frames (0.4 s)**, unless a discrete event (a blink, a glint, a
    glow step) falls inside it;
  - and it is ≤ 3× the median hold.
- After a still run of 10 frames or more, the first step is **under 25 % of the figure**. A bigger change eases in:
  its first and last steps are ≤ 60 % of its peak step, and the holds around it run 3, 2, 2, 3.
- A good model: one drawing, with a blink, a glow and a breath spread over the loop.
- **An accent and a rest** is a second idle shape: a quick event (a rise of 1-2 px with a mouth or an ear opening,
  held a few poses, then a fall) and then a quiet stretch of up to 40 % of the loop. The quiet stretch is still a
  moving hold, carried by a breath, a blink or the tail, and the accent eases in and out as above.
- A heavy, rooted body with no head (a plant, a shell, a statue) may hold still while its light appendages carry
  the idle. A creature with a head keeps the head and ears alive.
- An action holds one key on purpose (3.13); this rule is for the idle.
- Sources: Animation Mentor, "the moving hold"; AnimSchool, "never still"; Slynyrd 52 (extremes 100 ms, the middle
  50 ms); the twelve principles (slow in and out); Broadleaf Digital (the accent-and-rest idle, a rooted body).

### 3.4 Lift and bob without ticks

- **The square wave:** rounded to whole game pixels, a 1-px lift is a square wave. With a peak of A game px,
  `round(max(0, sin)·A)` is up for `(π − 2·asin(0.5/A)) / 2π` of the beat: 0.17 at A = 0.58 (reads as a tick), 0.35
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
- **Rise fast, sink slow,** for lifts of 2 px or more: the body rises during the downstroke over about 1/3 of the
  beat and sinks during the upstroke over about 2/3; the wing's lowest point comes at the end of the rise. Body
  timing and wing timing are separate: the downstroke itself stays broad (3.5). Every level still keeps the dwell
  above. (One source: saint11, Wings/Flying.)
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
  - for birds and bats, at least 4 distinct wing drawings a beat, ideally 6-8, never 2 (insects follow 3.6: a
    flutter about the shoulder, or ghost copies in one frame);
  - the downstroke is broader and as long as or longer than the upstroke.
  - Sources: PixelJoint bat thread ("the whole wing flaps"); Slynyrd 25 (8-frame flap); Taylor & Francis flight
    chapter (3 in-betweens up, 5 down).
- **The far wing never vanishes:**
  - it may be hidden (|s| < 0.35) only *while crossing* edge-on, for ≤ 5 frames, never at a turn;
  - otherwise it keeps ≥ 25-30 % of its rest-visible pixels, and at least 3 game px;
  - on the downstroke its tip shows below the belly.
  - Source: Tuts+ flying bird ("a little should still show").
- **Beat period by size** (move loops; stylised): owl or drake 18-36 frames, with a glide; shrike, magpie or bat
  12-18; wren or lark 8-12; insects 2-4 frames a beat on twos (1-2 drawings: the flutter of 3.6, not a bird's
  stroke), the body steady. An idle may beat once a loop. Sources:
  Pennycuick 1990; Jensen, Dyre & Hecksher 2024 (bigger, broader wings beat slower).
- **Optional, for big wings:** cut the lower feather mass as its own part, turned a beat after the wing (1.5°
  steps, held 2 frames).
- **Optional, a glide:** a bird may beat a few times, then glide with its wings folded and only sub-pixel shading
  moving (saint11, Wings/Flying).

### 3.6 Hoverers and insects

- Wings flutter about the shoulder on twos, fore and hind against each other (±8-14°), sampled half a step off the
  top. A faceted wing turned every frame resamples and its facets crawl.
- The body is steady (A < 0.5), or it drifts once a loop with each whole-pixel level held ≥ 1/3 of a beat. Never a
  half-cycle rigid lift peaking at 0.5-0.9 px: it reads as ticking up and down, not flying.
- Antennae and head run on their own slower beat, a beat late.
- Optional: draw very fast wings as 2-3 ghost copies in one frame, a blur, in place of more beat poses.
- Sources: Lynda insects course; measured on a mantis sprite (lift peak 0.58 → 1.15 px, duty 0.11 → 0.33);
  saint11 (Wings/Flying: insect wing copies).

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
  planted feet as the legs pass under it, twice a stride, and sinks as they reach out. Draw a stride in an even
  number of poses, so its two steps match. Legs stepping under a body that never moves read as a board on wheels.
  Raise every part but the legs, and give the legs an overlap strip upward so no gap opens at the hip. Do not hold
  the leg poses two frames with the bob on a step of its own: a held frame, a small leg step, then the whole body
  jumping reads as a hitch on every beat (`lurch`). Where the hips and the shoulders rise a pose apart, bend the
  back between them over its length; two rigid bands leave a step in the back (`split`).
  - Size the rise in game pixels before rounding: a lift worked out in reference pixels can round to 0 after the
    shrink, and the torso then never moves (a rise of 12 ref px on a sprite shrunk 25:1 is nothing). Use exactly one
    game pixel's worth, and hold each level 4+ frames.
  - Tie the chain parts (tail, mane, flame) to the step beat in a walk, once a step, a pose or two late. A big part
    swinging once a loop outweighs the bob, and the body reads as one slow heave (`gait`).
- **Planted feet do not slide.** A planted foot stays on one world pixel until it lifts.
  - In a walk drawn in place over a scrolling ground, every planted foot moves back the same amount each pose,
    never stopping, stepping forward or catching up.
  - That amount is the ground's scroll speed in game px per frame: the distance the foot goes back while planted
    divided by the frames it is planted, which equals the stride's length (a full cycle, two steps) divided by the
    loop's frames. A 32-frame walk whose paw goes back 20 px over 20 planted frames scrolls 1 px a frame, and its
    stride is 32 px (`examples/showcase/beast`). Match it to the game's real scroll speed (an easing scroll
    changes it, so match the steady pace).
  - Drive a planted foot's x by a backward ramp, not a sine: a sine swings it forward again before it lifts.
  - Look at the move over a scrolling ground line before showing it; a skating foot hides on a still background.
- **Footfall** (choose per creature): a quadruped is two bipeds with a small time offset, the head following the
  front pair a beat late.
  - A walk sets the feet down in turn, back-right, front-right, back-left, front-left (or mirrored), one contact
    each quarter stride. A trot moves the diagonal pairs together.
  - Each leg runs contact, drag, rise, forward. The back paw trails its knee; the front elbow moves fast at contact
    and release, and the paw snaps forward on release.
- **Near and far limbs:** the far limb swings less (one biped's arms: about half), both eased at their extremes
  (small end steps, larger mid-swing). Offset the far leg a little in time or place: never drive the near and far
  legs with one mirrored function. A far limb made by mirroring a near one is shaded a tone darker with little
  highlight (a rig cut from the drawing keeps the drawing's own shading).
- **Idle: layers, each on its own phase and period,** staggered so no frame stops everything or moves everything:
  1. a breath from the belly up to the chest: 1 px, or a sub-pixel tone (3.1). A soft body (fur, a blob) may widen
     by at most 1 px as it sinks; a shell or a golem keeps its width;
  2. a slow head drift or bow, the muzzle first and the poll a pose later;
  3. the ears a pose after the head, with one flick a loop;
  4. the tail as a chain, the middle leading and the tip following;
  5. a blink or an eye dart in any long stretch.

  Give the layers periods that divide the loop, each at its own offset (in 36 frames: breath 36, tail 18, an ear
  twitch 12), so no frame starts every layer at once. Such periods do not lengthen the repeat; they only stop the
  layers turning together. Only a layer the engine plays as a separate sprite, with a length that does not divide
  the body's (a flame, a swinging lamp, a banner), really hides the loop. That is a pipeline choice for whoever owns
  the engine side.
- **Weight on all four feet;** never caught mid-stride. A reference drawn mid-stride gets its legs drawn in.
- **A big part's 1-px move** (a head of 10-16 % of the figure) is staged over ≥ 2 poses: ears, then face, then neck
  on the bow; face, then neck, then ears on the rise. Avoid any single step that changes ≥ 8 % of the figure;
  when one must, hold it ≤ 2 frames. Horns can lead like ears. A head that steps only every second or so needs
  other parts changing on the same poses, or it jerks after each long hold (`hitch`).
- **Rate:** for example 18 poses held 2 frames, something changing on every pose, every moving region changing at
  least every 6 frames. A longer loop (about 2.4 s) makes a big animal's 1-px nod less of a metronome, if the
  player reads the frame count from the data.
- Sources: Game Developer, "Animating four-legged beasts" (head offset from hips and chest, tail last); Animation
  Mentor and AnimSchool (layered, never still); MoCap Online (base breathing, a slight head drift); Merck Vet Manual
  (resting breathing rates: a short loop can only stylise them); Slynyrd 52 (parts move different amounts);
  SpriteGen and saint11 Walk Cycle (planted feet); saint11 Quadruped Walk/Trot (footfall); Broadleaf Digital,
  finalbossblues and Sandy Gordon (near and far limbs); saint11 Seamless Looping and Kiwi (layer periods).

### 3.9 Heads, mouths and features

- The head is a rigid part. The eye, the mouth line and the jaw move with it; the face never reshapes between
  frames, and a mouth never flattens as if cut.
- A jaw opens only on purpose (an action). It pivots at the hinge, behind and below the eye, never at the mouth
  corner.
- Each snout column's height stays within ±1 px of rest, and so does the snout-to-eye length.
- **Defining features:** a feature the creature is named for (lamp eyes, a gem, a glowing mark) must survive the
  shrink at a size that reads. When it melts to one pixel or into its neighbours, draw it back at game size (two by
  two for big eyes) in its own colour.
- **Small marks:** a 1-3 px feature of high contrast (a gem, a lamp, a glint, a lone bright pixel) is where the eye
  goes. It shows on every frame and moves at most 1 px from one frame to the next, held frames included (Sandro
  Maglione's guide).
- Sources: WigglyPaint (the face centre does not drift); Tiny Warrior (keep key details crisp); Toon Boom and
  Godot cut-out joints (the pivot at the overlap's centre).

### 3.10 Chains and overlap

- Nothing starts or stops together: body, then head, then ears; root, then tail, then tip.
- In a chain each link lags its parent by **1-3 frames** (10-30° of phase in a 36-frame loop), the amplitude
  growing toward the tip. Lag 0 moves the chain as a board; a lag over a quarter loop detaches it. A tail catches
  up in about 0.3 s.
- **One pose of lag is enough** at sprite scale, and it may be one-sided: hair, a plume or ears come down a pose
  late and rise with the body.
- **On a walk the head lags the body's bob by one pose.** With a 1-px bob the head takes the whole pixel, late:
  a fraction of a pixel cannot be drawn, and the eye would tick. In an idle a lagging head still keeps the eye's
  dwell (3.4).
- **Paired appendages** (two antennae, two ears) alternate about half a loop apart and keep moving while the body
  holds.
- **Thin tips drag** 1-2 px against the travel on a contact or impact frame.
- **Drive every link from one wave** with a fixed phase offset per link, not keyed link by link. A tail's amplitude
  grows toward the tip; cloth may keep an even amplitude and lag more (about a fifth of its cycle per link).
- Sources: Babbitt and Williams (successive breaking of joints); SIGGRAPH HyperGraph on follow-through; AzureLib and
  Houdini KineFX spring chains; Sandro Maglione and Kyle McArthur (one pose, one-sided); Pixel Overload (head lag,
  fabric chain); Juniper Dev (paired antennae, tip drag).

### 3.11 Seams

- In a continuous loop (a walk, a wing beat), the last-to-first step is about the size of the others: the clean
  walks and beats here close at 0.78-1.32× their median moving step, while a 16-frame walk cut at 13 frames reads
  1.64 and at 11 frames 2.11, so stay under about 1.5. An idle may close on an accent (the showcase's beast and
  lizard close at 3.47 and 3.21× theirs) and is not held to it. pixel-anim-check prints the move's ratio as a
  read-out (the closing step).
- No duplicated closing frame: a repeated final pose doubles a hold (`seam` warns).
- Sources: Schödl et al., Video Textures (transition cost); llamagen's sprite-sheet frame audit.

### 3.12 Idle, amplitude, light, effects

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
  - **Timing:** a dust puff runs small, bigger, fading over 3 frames, about 4×4 px. A hit spark is 2 frames: a
    flash, then scattered pixels. Debris flies 2-3 poses after contact. A pop lasts about 3 frames (150 ms). A
    trail fades over 1-2 frames in darker tones.
  - A charge glow may light the creature's own pixels within a few px of its source, no further (Glow, above).

### 3.13 Actions and attacks

An action is a gesture, not a cycle. Its timing has its own rules; everything else in section 3 still holds.

- **Style:** give each attacker its own style that fits what it is.
  - A ranged creature looses a bolt or a breath; a melee creature lunges where it stands, or reels out and bites; a
    diving flier stoops in place and sends a cry; a gaze or curse stares a mark onto its foe.
  - Several creatures all darting to the foe and back looks cheap.
  - Time the hit to the frame that delivers it.
  - A blow that strikes several targets reads as one stroke passing through them: time each target's hit reaction
    to the frame the blow reaches it, not all together.
- **Phases of a strike** (a lunge, a bite, a swing, a pounce):
  1. *Anticipation:* a counter-move of at least 1 px against the strike, over 2-5 small poses. A still
     anticipation has no force.
  2. *Strike* in 1-2 frames: the largest step of the action, at least 3× the median anticipation step. A middle frame
     may be skipped to make it stronger.
  3. *One held key,* 4-13 frames at 30 fps: the wind-up for a telegraph or a heavy attack, or the contact for
     weight. Never hold both as briefly as the in-betweens. Make it a moving hold: the body sinks 1-2 px, the head
     follows a pose later, debris flies for 2-3 poses.
  4. *Follow-through, then recovery* over 2-5 poses whose steps grow, then shrink, none over half the strike step.
     A small overshoot past rest is fine.
  5. Typical ratios of anticipation, strike and recovery: 5:1:5 or 5:1:2 poses.
  6. Pose the strike on a *line of action:* one long line from the planted foot through the body to the striking
     part.
  - Only the one held key is exempt from the cadence rules (3.2); every other frame keeps them.
  - A breath, a spit or a ringing bell has no strike: it needs no counter-move, and 1, 2 and 4 do not apply. Tell
    the check which actions are strikes, and their direction.
- **Arcs, not pistons:** the leading part moves on a curve. The head rises, then drops into the bite; a tail or
  weapon tip sweeps a circle about its joint; a walk's head bob follows an arc too. Over 3+ key positions spanning
  4+ px, a path within 1 px of its straight chord reads as a piston.
- **Smears** (optional, actions only): on the fastest frame, a part that moves farther than its own length may be
  stretched along its path (to about the distance moved), or its swept path drawn as one shape in effect colours
  (a wedge, a crescent, ghost copies, an arc line). It lasts 1 frame, then a trail fades over 1-2 frames in darker
  tones. Limit it to the moving limb, a body stretch or the effect layer; never smear the face. A clean one-frame
  strike with no smear reads too.
- **Hit reactions:** the full displacement on the first frame, then a decay with no second peak (about 100, 70,
  60, 50, 30, 10, 0 % of it). One contrast flash frame may lead it.
- **Deaths:** the first frame throws the figure fully. It stops recovering halfway, the limbs and head lagging,
  overshoots the ground by 1 px, then rests. A small creature may squish (keeping its mass), flash, then burst.
- Sources: Broadleaf Digital (5:1:5, line of action); Pixel Overload (held contact, settle, smears); Sandy Gordon,
  Attack Animations; Sandro Maglione (5:1:2); Sprite AI and SpriteGen (which key to hold; arcs); saint11 (Easing,
  Squash and Stretch, Motion Blur, Death/Take Hit, Slide-Roll-Dash); Luke Sadface, Motion Lines.

### 3.14 Jumps and landings

- **Anticipation:** a squat 15-20 % lower, the width kept or wider, against the coming move.
- **Launch:** a stretch, taller and narrower.
- **Apex:** two drawings near the top, or the apex held about 2×.
- **Fall:** the vertical steps grow on the way down; never even.
- **Landing:** a squash of 1-2 frames; it may reuse the anticipation drawings. Then an overshoot of 1-2 px past the
  ground or rest, shrinking settle steps (the recovery rule in 3.13) and a hold.
- **Mass never changes:** a frame whose height changes 10 % or more changes its width the other way, its area
  within ±15 %. A deformation lasts at most 2 poses.
- **No squash in a solid creature's idle** (a shell, a golem, armour); a soft body's breath at most 1 px wider (3.8).
- **In a rig:** squash at the reference size and shrink once; hold each squash level 2 frames, in whole pixels
  (3.1).
- Sources: Pixel Overload (apex spacing, overshoot); Sandro Maglione (a 19 % squat, a held apex, landing reusing
  the anticipation); Sprite AI; saint11 (Squash and Stretch, Easing); Juniper Dev (area within ±15 %);
  finalbossblues (one squash frame on impact).
