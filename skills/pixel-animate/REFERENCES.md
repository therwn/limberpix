# References for pixel-animate

The sources named in [SKILL.md](SKILL.md), grouped by the section that cites them. Where a page refused access, it
is marked *summary only*: its point was taken from search summaries and not read first-hand. Richard Williams'
*The Animator's Survival Kit* is cited only through secondary quotes; the book itself was not read.

None of these gives a threshold in pixels for judder, a tick or a pop. The numbers in SKILL.md were fitted to a
private calibration set (39 animated creatures, with 15 accept or reject judgements on them by one reviewer; not
included), and are kept honest by the pixel-anim-check selftest.

Four sources are YouTube videos, cited by title and channel. They were read from the screen without sound, and
their example loops were measured frame by frame, so any point made only in speech is missing:

- Juniper Dev, "The ONLY Pixel Art Guide You Need (Beginner to Advanced)".
- Broadleaf Digital, "Pixel Art Animation Tips For Beginners".
- Pixel Overload, "The secrets to good Pixel Art animation! (Animation tutorial)".
- Sorceress Gamedev, "Creating Real Pixel Art Animations with AI" (a demo of the Pixel Snap tool:
  https://sorceress.games/pages/pixel-snap).

Many of saint11's and Sandy Gordon's tutorials are single animated sheets posted on Twitter; they are indexed by
Lospec, "Pixel Art Animation Tutorials": https://lospec.com/pixel-art-tutorials/tags/animation

## Sub-pixel motion and whole pixels (3.1, 3.4)

- someanimatorwannabe, "Animator Techniques: Sub-Pixel Animation" (Metal Slug's Fio breathes by colour, not by
  position): https://someanimatorwannabe.substack.com/p/animator-techniques-sub-pixel-animation
- Tiny Warrior Games, sub-pixel animation:
  https://tinywarriorgames.com/2019/01/04/game-development-pixel-art-sub-pixel-animation/
- Pixel Parmesan, anti-aliasing fundamentals: https://pixelparmesan.com/anti-aliasing-fundamentals-for-pixel-artists
- saint11, pixel art tutorials (the sub-pixel GIF): https://saint11.art/blog/pixel-art-tutorials/
- Tsugumo, *The Pixel Artist*, ch. 10 and 11:
  https://web.cs.wpi.edu/~claypool/courses/frontiers-06/samples/pixel-artist/chapter10.htm ;
  https://web.cs.wpi.edu/~claypool/courses/frontiers-06/samples/pixel-artist/chapter11.htm
- Slynyrd Pixelblog 23 (slow motion jitter): https://www.slynyrd.com/blog/2019/11/12/pixelblog-23-parallax-scrolling
- Pixel-perfect slow motion jitter (Lexaloffle forum): https://www.lexaloffle.com/bbs/?tid=28176
- saint11, "< 1 Pixel Movement" (move part of an edge first, then the rest; on round shapes move the light, not
  the shape; too many in-between pieces look bent): https://twitter.com/saint11/status/816102966591705088
- saint11, "Character Idle" (a slime's face catches up one pose after its outline drops; the lower body widens a
  little as it sinks): https://twitter.com/saint11/status/882228769230073858
- Kiwi, "Give your sprites depth with sub-pixel animation" (animate the anti-aliasing and interior shading; a big
  walker whose legs change every frame and whose trunk and tail run on a cycle twice the body's):
  https://2dwillneverdie.com/tutorial/give-your-sprites-depth-with-sub-pixel-animation/
- Pixel Overload (video, above): the in-betweens of a 1-px move changed 8-47 px against 215-531 px for the
  whole shift, outline corners stepping before the fill.
- Juniper Dev (video, above): one light source that never moves between frames; the terminator follows the form.

## Cadence and holds (3.2)

- Richard Williams on ones and twos, secondhand: https://animationpodcast.com/2005/06/04/ones-and-twos/ ;
  https://www.awn.com/print/animationworld/animators-survival-kit-most-valuable-how-animate-book-you-will-ever-want-own
- Wave Motion Cannon, "An introduction to framerate modulation" (threes and fours read jerky):
  https://wavemotioncannon.com/2016/12/31/an-introduction-to-framerate-modulation/
- Animating on ones, twos and threes:
  https://publish.obsidian.md/mister-chad/animation/animating+on+the+ones%2C+two%2C+and+threes ;
  https://www.idtech.com/blog/what-does-animating-on-ones-twos-and-threes-mean
- Klein et al. 2023, "The Influence of Variable Frame Timing on First-Person Gaming" (the longest frames dominate
  perceived smoothness): https://ar5iv.labs.arxiv.org/html/2306.01691 ;
  https://web.cs.wpi.edu/~claypool/papers/frame-variation-chi-23/paper.pdf
- Taylor & Francis chapter on mixing ones and twos (jitter):
  https://www.taylorfrancis.com/books/9781136134623/chapters/10.4324/9780080519272-31
- Slynyrd Pixelblog 8, Intro to Animation: https://www.slynyrd.com/blog/2018/8/19/pixelblog-8-intro-to-animation
- Judder and stutter: https://www.forasoft.com/learn/video-quality/articles-vqm/judder-stutter-frame-rate-artifacts

**Why slower sources do not loosen the cadence rules.** Many hand-made sources run slower than SKILL.md allows:
Slynyrd 8 uses 80-160 ms a drawing for runs; finalbossblues' walk GIFs run 80-150 ms a frame (200 ms for a
4-frame walk); Sprite AI's table holds idle drawings 300-500 ms; Pixel Overload's loops all advance about every
108 ms; Broadleaf Digital's previews hold 110-300 ms; Juniper Dev's runs use 100 ms; SpriteCanvas suggests
8-12 fps. At 30 fps those are holds of 3-24 frames, which `choppy` would flag. Their sprites are 16-48 px tall and
each pose change is a clean 1-px step of a whole part. The 15/s target, the 10/s floor and the 4-frame hold limit
were fitted on larger, textured creatures (the calibration set above), where slow holds read as a dropped frame
rate, so they stay stricter on purpose. What those sources teach is spacing: one large strike step and eased steps
elsewhere, at a uniform frame time (Broadleaf's attack and Sandy Gordon's attacks hold every frame alike).

## Stillness and the moving hold (3.3, 3.8)

- Animation Mentor, "Why all animators need to master the moving hold" (*summary only*):
  https://animationmentor.com/blog/why-all-animators-need-to-master-the-moving-hold
- AnimSchool, "never still": https://blog.animschool.edu/?p=858 ; also https://anim.works/?p=25924
- Slynyrd Pixelblog 52, Idle Fighting Stance: https://www.slynyrd.com/blog/2024/9/26/pixelblog-52-idle-fighting-stance
- Twelve basic principles of animation: https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation
- MoCap Online, creature animation for games: https://mocaponline.com/blogs/mocap-news/creature-animation-games-guide ;
  idle loops (a vendor's claim): https://mocaponline.com/blogs/mocap-news/idle-animation-loop
- Broadleaf Digital (video, above): a toad's idle that rises 2 poses, holds 3, falls 1-2 and rests 5 of 12 (about
  40 % at rest), with a drip, a cloth strip and a blink on other cycles; a mandrake whose body stays still while its
  leaves move.
- Endesga, "Pixelart Quicktip: Idle Animation" (hold the up and down extremes of a simple bob):
  https://twitter.com/ENDESGA/status/862254940529377280

## Wings, fliers and hoverers (3.4, 3.5, 3.6)

- PixelJoint bat flight critique, TID 2095 ("the whole wing flaps"):
  https://pixeljoint.com/forum/printer_friendly_posts.asp?TID=2095 ; wing thread:
  https://pixeljoint.com/forum/printer_friendly_posts.asp?TID=26583
- Tuts+, how to animate a flying bird ("a little should still show"; the body rises on the downstroke):
  https://design.tutsplus.com/tutorials/animation-for-beginners-how-to-animate-a-flying-bird--cms-25209 ;
  https://design.tutsplus.com/tutorials/create-a-flight-animation-from-scratch-in-adobe-photoshop--cms-22739
- Hovering lift on the downstroke: https://pmc.ncbi.nlm.nih.gov/articles/PMC3367811
- ornithopter.org, how birds flap: https://ornithopter.org/birdflight/flap.shtml
- Bird flight analysis for animation (corn-vanilla): https://corn-vanilla-t4dg.squarespace.com/learn/bird-flight
- Animation Mentor, birds in flight (*summary only*):
  https://www.animationmentor.com/blog/tutorial-how-to-animate-birds-in-flight/
- Slynyrd Pixelblog 25, Motion Cycles (8-frame flap): https://www.slynyrd.com/blog/2020/1/23/pixelblog-25-motion-cycles
- Taylor & Francis chapter on flight cycles (3 in-betweens up, 5 down):
  https://www.taylorfrancis.com/books/9781136134944/chapters/10.4324/9780080476438-13
- Pennycuick 1990, "Predicting wingbeat frequency and wavelength of birds", J. Exp. Biol. 150:
  https://doi.org/10.1242/jeb.150.1.171
- Jensen, Dyre & Hecksher 2024 (bigger, broader wings beat slower):
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11152310/ ; news summary:
  https://physicsworld.com/a/simple-equation-predicts-how-quickly-animals-flap-their-wings/
- Lynda, 2D animation of flying creatures, insects and small birds:
  https://origin-www.lynda.com/3D-Animation-tutorials/Insects/501129/602249-4.html ;
  https://origin-www.lynda.com/3D-Animation-tutorials/Small-birds/501129/602246-4.html
- Rodeo FX at Autodesk University, how to make a dragon fly:
  https://autodesk.com/autodesk-university/class/Rodeo-FX-Animation-Department-How-to-Make-a-Dragon-Fly-2024
- saint11, "Wings / Flying" (the body rises fast on the downstroke and falls a pixel a frame on the upstroke; a
  bird's glide on sub-pixel shading; ghost copies for fast insect wings):
  https://twitter.com/saint11/status/854346428562407425

## Snakes and legless bodies (3.7)

- PixelJoint snake idle critique, TID 26707: https://pixeljoint.com/forum/printer_friendly_posts.asp?TID=26707
- Hu, Nirody, Scott, Shelley, PNAS 2009, the mechanics of slithering locomotion:
  https://math.nyu.edu/~shelley/papers/HNSS2009.pdf ; a review: https://pmc.ncbi.nlm.nih.gov/articles/PMC7391877
- *Character Animation 2D*, slither chapter:
  https://www.oreilly.com/library/view/character-animation-2d/9780240520544/14_Chapter_07.xhtml
- Tongue-flick rates: https://pmc.ncbi.nlm.nih.gov/articles/PMC8833826/table/animals-12-00373-t003

## Walkers and quadrupeds (3.8)

- Game Developer, "Animating four-legged beasts": https://gamedeveloper.com/art/animating-four-legged-beasts
- Merck Veterinary Manual, resting respiratory rates:
  https://www.merckvetmanual.com/multimedia/table/resting-respiratory-rates
- SpriteGen, "How to animate pixel art" (no foot skating: a planted foot keeps its pixel until it lifts; arcs; one
  size and one palette per frame): https://spritegen.io/guides/how-to-animate-pixel-art/
- saint11, "Walk Cycle" (the planted foot always slides back; two bobs a cycle):
  https://twitter.com/saint11/status/905098438571958272
- saint11, "Quadruped Walk/Trot" (two bipeds with a small offset; contact order; paw lag and snap):
  https://twitter.com/saint11/status/900382741086261249
- saint11, "Seamless Looping" (overlapping cycles of different lengths, started at different offsets):
  https://twitter.com/saint11/status/803206812661059584
- Sandy Gordon, "Walk Cycles" and "Run Cycles" (an even frame count; offset the far leg so it is not a mirror):
  https://twitter.com/Bandygrass/status/809420271769686016 ;
  https://twitter.com/Bandygrass/status/829350756004175874
- Jason Perry (finalbossblues), "Walk Cycles" parts 1-3 (the planted leg slides back; back limbs darker; blocking
  in flat colours; the body rises and falls twice in 8 frames): http://finalbossblues.com/walk-cycles-p1/ ;
  http://finalbossblues.com/walk-cycles-part-2/ ; http://finalbossblues.com/walk-cycles-part-3/
- Kyle McArthur, "The Process of Pixel Art Animation: A Beginner's Guide" (a fixed ground line; motion settled at the
  flat-blob stage; the plume one frame late):
  https://www.artstation.com/blogs/calamity_kyle/wVE2/the-process-of-pixel-art-animation-a-beginners-guide
- Broadleaf Digital (video, above): a walk whose near arm swings about 4 px and far arm about 2 px, both eased at the
  extremes.

## Heads, joints and chains (3.9, 3.10)

- WigglyPaint, pixel art animation guide: https://wigglypaint.com/blog/pixel-art-animation-guide/
- Toon Boom Harmony, fixing and patching articulations:
  https://docs.toonboom.com/help/harmony-12-2/premium/rigging/fix-articulations.html ;
  https://docs.toonboom.com/help/harmony-12-2/premium/rigging/patch-articulation.html
- Godot, cutout animation: https://docs.godotengine.org/en/stable/tutorials/animation/cutout_animation.html
- Successive breaking of joints (Art Babbitt, taught by Richard Williams):
  https://animationapprentice.blogspot.com/2019/04/what-is-successive-breaking-of-joints.html ;
  https://en.wikipedia.org/wiki/Follow_through_and_overlapping_action
- SIGGRAPH HyperGraph, follow-through:
  https://education.siggraph.hosting.acm.org/static/HyperGraph/animation/character_animation/principles/follow_through.htm
- Spring chains: AzureLib secondary motion,
  https://moddedmc.wiki/en/project/azurelib/latest/docs/misc/animating/secondary_motion.md ; Houdini KineFX,
  https://www.sidefx.com/docs/houdini/character/kinefx/secondarymotion.html
- Sandro Maglione, "Pixel Art Character Animations Guide" (hair one frame late on the way down only; a lone
  high-contrast pixel is where the eye goes; a jump and an energy blast measured below):
  https://www.sandromaglione.com/articles/pixel-art-character-animations-guide
- Pixel Overload (video, above): the head follows the hip one drawing late at about 2/3 of its travel; a fabric
  chain with every joint a fixed fifth of the cycle behind its parent, at an even amplitude.
- Juniper Dev (video, above): two antennae half a loop apart that keep moving while the body holds; a thin tip
  dragging back on the contact frame.
- Sprite AI, "The 12 Animation Principles for Pixel Art Sprites" (accessories one frame behind; arcs; volumes kept;
  staging by silhouette): https://www.sprite-ai.art/guides/animation-principles

## The rig and the part strip (1, 2)

- saint11, "Modular Animation" (draw the hidden parts; hide bends behind solid parts or a change of material; avoid
  rotation and scale where possible): https://twitter.com/saint11/status/925756719841628160
- Broadleaf Digital (video, above): the silhouette designed first as one flat shape; parts colour-coded to plan
  and check overlap; a stick figure on a line of action under each key.
- Kyle McArthur (above) and finalbossblues, walk part 3 (above): the motion settled on flat colour blocks before
  any detail.

## Bringing a frame down to game size (2, step 5)

- Astropulse, K-Centroid downscale (MIT): https://github.com/Astropulse/K-Centroid-Aseprite . Its README calls it
  "a new downsampling algorithm using k-means"; its itch.io page (https://astropulse.itch.io/k-centroid , *summary
  only*) describes it as taking the most common colour of every tile. `shrink.py`'s voted fill is that idea with the
  palette known beforehand.
- Shin-Ying Yeh, PixelOE (Apache-2.0): https://github.com/KohakuBlueleaf/PixelOE . It widens the outlines of key
  features before downscaling, so that fine details and high-contrast edges survive it, and lists Astropulse's
  k-centroid among its downscale modes. `shrink.py` meets the same loss by reading the contour apart.
- Gerstner, DeCarlo, Alexa, Finkelstein, Gingold and Nealen, "Pixelated Image Abstraction", NPAR 2012:
  https://pixl.cs.princeton.edu/pubs/Gerstner_2012_PIA/index.php . Nearest-neighbour or cubic downsampling followed
  by median-cut quantisation gives detail loss and blurriness (the teaser figure's caption).
- Kopf, Shamir and Peers, "Content-Adaptive Image Downscaling", ACM Transactions on Graphics 32(6), SIGGRAPH Asia
  2013: https://johanneskopf.de/publications/downscaling . Filters blind to the content either keep sharpness and
  alias (subsampling) or smooth out fine details and edges (bicubic, Lanczos).

**What `shrink.py`'s rules were measured on.** Six painted reference drawings from a private set (single creatures
on a plain ground, 1300 to 1650 px wide; not included), each brought to its game size (25 to 54 px wide, a cell of
24 to 36 reference px) with 18 tones. Three numbers that need no ideal answer were read: the share of the figure
left as lone pixels (a pixel unlike all eight round it); the share that changes when the drawing is moved a fifth of
a cell on the same grid, which should be none; and how much of the figure the darkest tone, the contour, keeps.

| How a cell becomes a pixel | Lone pixels | Changed by a fifth-of-a-cell move | The contour's share |
|---|---|---|---|
| the cell's average | 42 % | 67 % | 5 % |
| one sample at the cell's centre | 41 % | 65 % | 5 % |
| 2-means of the cell's colours, the larger part, the contour read apart | 27 % | 45 % | 26 % |
| `shrink.py`: the contour read apart, the fill voted | 18 % | 34 % | 25 % |
| the same vote, no contour rule | 18 % | 32 % | 9 % |

On each of the six, `shrink.py` was lowest on the first two numbers, the 2-means next, the average and the single
sample highest. The third row is the pipeline the private set's sprites were made with;
`shrink.py`'s coverage and contour thresholds (0.42, 70, 0.45, 0.12) are that pipeline's. Looked at by eye on three
of the six: the contour rule keeps the outlines the plain vote loses, and the voted fill kept a tail flame and an
eye that the 2-means lost. One person's measurements and look; nobody else judged the pictures. Even the best row
changes a third of the pixels under a small move, which is why the default rules move parts by whole game pixels.

The crest rule (which of two cells a thin line straddles is the line) was fixed on built cases, not on the
drawings: on the six it changed 2 to 10 pixels a drawing against the pipeline's own rule. `shrink_selftest.py`
holds those cases: a 3-px line across two 8-px cells stays one pixel wide, and a drawing blown up 3, 7.5 and 8
times in solid cells comes back the same. The three showcase drawings come back the same from their 8x pictures.

## Actions, jumps, hits and effects (3.12, 3.13, 3.14)

- Broadleaf Digital (video, above): a punch of 5 anticipation frames (small steps, sinking 2 px, the fist drawn
  back), a one-frame strike with a 12 px jump and no smear, the reach held 2 frames, and a recovery whose steps grow
  then shrink: 5:1:5.
- Pixel Overload (video, above): an axe chop whose wind-up builds and holds, strikes in 2 drawings with smears,
  holds the contact, and settles with the head a drawing after the body; a ball with two drawings near the apex and
  growing steps on the fall; overshoot and settle in shrinking steps.
- Sandy Gordon, "Attack Animations" (ready, anticipation, swing, follow-through, recover; a still anticipation has
  no force; the snap comes from spacing): https://www.patreon.com/posts/attack-animation-7820106
- Sandro Maglione (above): a jump with a squat about 19 % lower at the same width, a narrower stretch, a held apex
  and a landing that reuses the anticipation; an energy blast at 5:1:2 whose glow lights the face nearby.
- Sprite AI (above): a duration table for wind-up, held impact, recovery, launch, apex and landing; a 3-frame dust
  puff and a 2-frame spark; no squash in solid idles.
- SpriteGen (above): hold the wind-up when the telegraph matters and show the contact once. Sprite AI holds the
  impact instead; SKILL.md asks for one held key and leaves the choice to the action.
- saint11, "Animation Easing" (two middle frames carry most of an eased move; a back-ease pulls back a little,
  jumps most of the way in one frame and overshoots): https://twitter.com/saint11/status/829062247649570816
- saint11, "Squash and Stretch" (mass never changes; anticipation squashes against the action):
  https://twitter.com/saint11/status/874640430742347777
- saint11, "Motion Blur" (a one-frame smear, then a trail fading in darker colours):
  https://twitter.com/saint11/status/872098481057517568
- saint11, "Death / Take Hit" (the full offset on the first frame, then a slow decay; a death overshooting the
  ground by a pixel; a contrast frame): https://twitter.com/saint11/status/940622511041064961
- saint11, "Slide-Roll-Dash" (an overshoot on recovery): https://twitter.com/saint11/status/955811374994743296
- Luke Sadface, "Motion Lines" (one arc line in the impact frame only):
  https://twitter.com/Sadface_RL/status/987767929797308416
- Jason Perry (finalbossblues), "Basics of Animation" (volume kept; one squash frame on impact):
  http://finalbossblues.com/basics-of-animation/
- Juniper Dev (video, above): a fast turn whose deformed in-betweens keep the area within about 15 %; an overshoot
  and settle after a big move; a 3-frame pop on its own layer.

## Sprite sheets and generated frames (4)

- Sorceress Gamedev (video, above): in its output, every other kept frame changed only a 1-px trace along the
  outlines, a fraction of a real pose step; thinning by hand in uneven steps slowed the motion; the clip drifted in
  height by about 8 %; it swapped a shield on and off; and the tool offers one palette for the whole sheet, a head
  lock and foot anchoring.
- SpriteCanvas, "Pixel art animation" (generated sheets whose texture boils between frames):
  https://spritecanvas.com/pixel-art-animation/
- Pixel Engine (room on the canvas 1.3-1.8× the longest side, anchored opposite the action; per-frame quantising
  flickers): https://pixelengine.ai ; https://pixelengine.ai/guides/reframe ; https://pixelengine.ai/guides/animate
- PixelLab (the first frame is the input; interpolation keys are not padded for you; one colour cap for the whole
  animation): https://www.pixellab.ai ; https://www.pixellab.ai/docs
- Juniper Dev (video, above): animation frames use exactly the drawing's colours.

## Choices recorded where sources disagree

- **Accent and rest.** Broadleaf's toad rests still for about 40 % of its idle; the moving hold (3.3) forbids a
  dead stop. SKILL.md adopts the shape with the rest carried by secondary layers, and the accent eased.
- **Breath that widens.** saint11 widens a sinking idle; Sprite AI forbids squash in a solid creature's idle.
  SKILL.md allows at most 1 px of width on soft bodies only.
- **Which key to hold.** Sprite AI holds the impact, SpriteGen the wind-up. SKILL.md asks for one held key, chosen
  per action, as a moving hold.
- **Chain amplitude.** Pixel Overload's fabric keeps an even amplitude; SKILL.md keeps a growing one for tails and
  allows an even one for cloth.
- **Flight rise and fall.** saint11's bat holds some levels a single frame and rises 3 px in one; only the
  asymmetry (rise fast, sink slow) is adopted, inside the dwell rules of 3.4.
- **Smears.** Broadleaf's strike reads with no smear, while Sandy Gordon and Pixel Overload smear; smears are an
  option.

## Seams (3.11)

- Schödl, Szeliski, Salesin, Essa, "Video Textures" (SIGGRAPH 2000), lecture slides:
  https://pages.cs.wisc.edu/~dyer/cs534/slides/05-video-textures.pdf
- llamagen, sprite-sheet frame audit: https://llamagen.ai/guides/sprite-sheet-frame-audit

## Further reading

- Outlines: https://lospec.com/articles/pixel-art-outlines
- Pixel-art scaling (RotSprite) and cleanEdge: https://en.wikipedia.org/wiki/Pixel-art_scaling_algorithms ;
  https://gist.github.com/torcado194/e2794f5a4b22049ac0a41f972d14c329
- Vapor Trails, basic skeletal animation for pixel art:
  https://sevencrane.itch.io/vapor-trails/devlog/214252/tutorial-basic-skeletal-animation
- Slynyrd Pixelblog 37 and 55: https://www.slynyrd.com/blog/2022/3/19/pixelblog-37-classic-castlevania-study ;
  https://slynyrd.com/blog/2025/3/24/pixelblog-55-top-down-character-animation
