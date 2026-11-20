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
