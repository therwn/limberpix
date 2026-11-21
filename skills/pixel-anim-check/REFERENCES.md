# References for pixel-anim-check

The checks rest on these sources for what reads as smooth or broken. None of them gives a threshold in pixels for
judder, a tick or a pop, so the numbers in [SKILL.md](SKILL.md) were fitted to a private calibration set (39 animated
creatures, with 15 accept or reject judgements on them by one reviewer; not included), and are kept honest by the
selftest. Sources marked *summary only* could not be read directly (the page refused access) and are cited from
search summaries. The craft sources behind the fixes in the table are listed in the pixel-animate skill's
REFERENCES.md.

## Timing, holds and frame rate

- Wave Motion Cannon, "An introduction to framerate modulation" (threes and fours read jerky):
  https://wavemotioncannon.com/2016/12/31/an-introduction-to-framerate-modulation/
- Richard Williams on ones and twos, quoted secondhand (the book itself was not read):
  https://animationpodcast.com/2005/06/04/ones-and-twos/ ;
  https://www.awn.com/print/animationworld/animators-survival-kit-most-valuable-how-animate-book-you-will-ever-want-own
- Animating on ones, twos and threes:
  https://publish.obsidian.md/mister-chad/animation/animating+on+the+ones%2C+two%2C+and+threes ;
  https://www.idtech.com/blog/what-does-animating-on-ones-twos-and-threes-mean
- Klein et al., "The Influence of Variable Frame Timing on First-Person Gaming" (the longest frames dominate
  perceived smoothness): https://ar5iv.labs.arxiv.org/html/2306.01691 ;
  https://web.cs.wpi.edu/~claypool/papers/frame-variation-chi-23/paper.pdf
- Mixing ones and twos (jitter), Taylor & Francis chapter:
  https://www.taylorfrancis.com/books/9781136134623/chapters/10.4324/9780080519272-31
- Judder and stutter: https://www.forasoft.com/learn/video-quality/articles-vqm/judder-stutter-frame-rate-artifacts
- Frame rate and apparent motion: https://en.wikipedia.org/wiki/Frame_rate ;
  https://en.wikipedia.org/wiki/Korte%27s_third_law_of_apparent_motion
- Pixel-perfect slow motion jitter (Lexaloffle forum): https://www.lexaloffle.com/bbs/?tid=28176
- Slynyrd Pixelblog 8, Intro to Animation: https://www.slynyrd.com/blog/2018/8/19/pixelblog-8-intro-to-animation
- Slynyrd Pixelblog 52, Idle Fighting Stance (extremes held longer than the middle):
  https://www.slynyrd.com/blog/2024/9/26/pixelblog-52-idle-fighting-stance

## Stillness and overlap

- The moving hold: https://animationmentor.com/blog/why-all-animators-need-to-master-the-moving-hold (*summary
  only*) ; https://blog.animschool.edu/?p=858 ; https://anim.works/?p=25924
- Twelve basic principles of animation: https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation
- Follow-through and overlapping action:
  https://en.wikipedia.org/wiki/Follow_through_and_overlapping_action

## Sub-pixel motion (why `shimmer` forgives a monotonic in-between)

- "Animator Techniques: Sub-Pixel Animation": https://someanimatorwannabe.substack.com/p/animator-techniques-sub-pixel-animation
- Tiny Warrior Games, sub-pixel animation:
  https://tinywarriorgames.com/2019/01/04/game-development-pixel-art-sub-pixel-animation/
- Pixel Parmesan, anti-aliasing fundamentals: https://pixelparmesan.com/anti-aliasing-fundamentals-for-pixel-artists

## Measurement

- Schödl, Szeliski, Salesin, Essa, "Video Textures" (loop seams as a transition cost), lecture slides:
  https://pages.cs.wisc.edu/~dyer/cs534/slides/05-video-textures.pdf
- Sprite-sheet frame audit: https://llamagen.ai/guides/sprite-sheet-frame-audit
- Temporal motion smoothness (ICIP 2018): https://ece.uwaterloo.ca/~z70wang/publications/icip18.pdf
- Optical flow on pixel art: https://mars.gmu.edu/handle/1920/11466
- Smoothness measures (SPARC, jerk), read but not used as gates because they only rank loops:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4674971 ; https://monalysa.readthedocs.io/en/latest/smoothness.html ;
  https://peerj.com/articles/9843

## The later checks (section 2b of SKILL.md, and jump on held poses, palette and mark)

These sources describe what good motion does; none of them gives a pixel threshold either. The later checks turn
their statements into first-guess margins, kept as warnings until they are fitted on accepted animations. Each line
says what the check takes from the source, in our words. The videos are cited by title and channel (YouTube); no
stable link was found for them.

- Pedro Medeiros (saint11) and others, the animation tutorials indexed on Lospec (Walk Cycle, Quadruped Walk and
  Trot, Squash and Stretch, Easing, Death and Take Hit, Slide-Roll-Dash, Motion Blur, Wings and Flying, Character
  Idle, Seamless Looping, Less Than 1 Pixel Movement; Sandy Gordon on attacks and on walk and run cycles;
  finalbossblues on walks; Luke Sadface on motion lines): https://lospec.com/pixel-art-tutorials/tags/animation .
  Behind `skate` (the planted foot slides back evenly), `gait` (one bob a step), `counter`, `strike`, `recover`
  (an anticipation, a fast strike, an eased return), `gravity` and `squash` (spacing that grows on the fall, a
  squash that keeps its mass), `piston` (an attack's arc).
- Raymond Schlitter, Slynyrd Pixelblog 8, Intro to Animation (already above): a single orphan pixel is glaring in a
  loop (`orphans`, `speck`); a walk's width at contact against its passing pose (read out by `gait`, not judged:
  a long-bodied animal's width barely changes).
- Sandro Maglione, "Pixel art character animations guide":
  https://www.sandromaglione.com/articles/pixel-art-character-animations-guide . Hair that lags a frame behind the
  head (`lag`), a jump's squash that lands on the anticipation drawings (`squash`), a lone bright pixel drawing the
  eye (`mark`).
- Sprite-AI, "Animation principles": https://www.sprite-ai.art/guides/animation-principles . Staging (a key pose must
  change the silhouette: `stage`), arcs (`piston`), timing of the strike against its anticipation (`strike`), a base
  sprite locked first (`drift`).
- SpriteGen, "How to animate pixel art": https://spritegen.io/guides/how-to-animate-pixel-art/ . No foot skating, a
  planted foot holding its pixel (`skate`); motion along arcs (`piston`); one palette over every frame (`palette`).
- Kyle McArthur, "The process of pixel art animation: a beginner's guide" (ArtStation):
  https://www.artstation.com/blogs/calamity_kyle/wVE2/the-process-of-pixel-art-animation-a-beginners-guide . A fixed
  ground line, motion fixed on flat blobs first (`--parts`), a plume a frame late (`lag`), the approved still kept
  in view (`drift`).
- SpriteCanvas, "Pixel art animation": https://spritecanvas.com/pixel-art-animation/ . Generated walks that boil and
  drift in palette (`boil`, `palette`, `orphans`).
- PixelEngine: https://pixelengine.ai . Per-frame quantising flickers (`boil`, `blend`); room round the figure for
  a reach (the `outline` note on a figure cut by its cell).
- PixelLab: https://www.pixellab.ai . An animation's first frame is its input drawing, unchanged (`drift`); a colour
  cap over the whole animation (`palette`).
- "The ONLY Pixel Art Guide You Need (Beginner to Advanced)", Juniper Dev (YouTube video). No doubled outlines or
  L-corners in any frame (`doubles`); one light source and one palette over a loop (`palette`); a squash keeping
  its area within about 15 % (`squash`); a walk's body bob (`gait`).
- "Creating Real Pixel Art Animations with AI", Sorceress Gamedev (YouTube video). Generated sheets come as held
  pairs whose second frame redraws only a trace along the outline (`boil`, and why `jump` compares a held pose with
  the poses either side of the hold); a part switched off for one cell (`swap`); cell scale and anchor drifting
  (the box read-out).
- "Pixel Art Animation Tips For Beginners", Broadleaf Digital (YouTube video). Silhouette first, colour-coded parts
  (`stage`, `--parts`); an attack timed as anticipation, a one-frame strike and a held key (`strike`, the action's
  held key in `choppy`); a strike drawn without a smear (why smears are not checked).
- "The secrets to good Pixel Art animation! (Animation tutorial)", Pixel Overload (YouTube video). Anticipation,
  strike and settle; a head lagging the hip by a drawing (`lag`); sub-pixel in-betweens that are small and
  edge-only but lead the move (why `boil` asks for a step that reverts).

## Why the slower timings in these sources do not loosen `choppy`

Many hand-made sources time walks and runs at 80-150 ms a drawing (7-12 a second) and hold idle drawings 200-800 ms
(3 to 24 frames at 30 fps, which `choppy` would flag): Slynyrd, finalbossblues, Sprite-AI's idles, Pixel Overload,
Broadleaf Digital, Juniper Dev and SpriteCanvas among them. Their sprites are 16-48 px, and each of their pose
changes is a clean whole-pixel step of a whole part. The 10-a-second floor and the rule against a hold of 4+ frames
inside a cycle were set on a calibration set of larger textured creatures, where slower rates were judged choppy,
so they stay, stricter than these sources on purpose. What these sources teach is spacing (one big strike step,
eased steps elsewhere), not a slower rate. A declared action may hold one key up to 13 frames (the sources' 4-13),
and only that one.

