"""The Emberback skink: an original pixel-art lizard for the showcase, drawn by hand pixel by pixel and kept as data.

A 3/4 view from above, facing right, lit from the top left: the back and the near flank show, the four legs splay out
to both sides (the far pair above the back, the near pair in front of the flank), each foot with its toes. One clear
dorsal pattern: a row of ember spots down the spine, evenly spaced, shrinking along the tail.

Everything here is data: a palette, the body as strings (one character a pixel, "." for air), a mask naming the part
each body pixel belongs to, and the parts that move on their own (four legs, the eyelid, the tongue) as small layers
with their origin. animate.py poses these parts; it never redraws them.

    python creature.py            # writes lizard_art_8x.png next to this file (the drawing at 8x)
"""
import os

KEY = "lizard"
W, H = 74, 32                 # the canvas every pose is drawn in (room ahead of the snout for the tongue)

# 14 colours. Greens: a deep blue-green shadow, a cool shadow, the mid tone, a light and a warm yellow-green
# highlight (shadows cooler, lights warmer). The outline is ink, lightened to a dark green where the light falls on
# the back and the head.
PALETTE = {
    "o": "#1b1826",                                                    # ink
    "O": "#2c4438",                                                    # lit outline (top edges)
    "d": "#1f4a4f", "s": "#2e7458", "g": "#4f9e45", "l": "#8cc443", "h": "#d2e67a",   # scales, dark to light
    "r": "#f08a3c", "R": "#b2432e",                                    # ember spots, light and dark
    "c": "#ecdca2", "b": "#b89a6a",                                    # the lip, light and shadow
    "e": "#f6c544", "W": "#fffbe8",                                    # iris, glint
    "t": "#e0517a",                                                    # tongue
}
INK = "oO"
EYE = "e"
TONGUE = "t"

# The body: tail, trunk, neck and head, drawn whole (also where the legs cover it, so a leg that steps away never
# shows a hole). Its eye is 2x2: the glint, two iris pixels and the pupil.
BODY = [
    "..........................................................................",  # 0
    "..........................................................................",  # 1
    "..........................................................................",  # 2
    "..........................................................................",  # 3
    "..........................................................................",  # 4
    "..........................................................................",  # 5
    "..........................................................................",  # 6
    "..........................................................................",  # 7
    "..........................................................................",  # 8
    "..........................................................................",  # 9
    "................................OOOOOOOOOOOO......OOOOOOOO................",  # 10
    ".............................OOOhhhhhhllllllOOOOOOllhhhhllOOO.............",  # 11
    "..........................OOOhhhlllrrlllrrlllllllgllllllhhlllOO...........",  # 12
    "........................OOhhhlrrgggRRgggRRgglrrlgggggldddllhhllO..........",  # 13
    "....................OOOOhhlllgRRgggggggggggggRRggsgggdWedglllhllO.........",  # 14
    "................oooorrlllrrgggggggggggggggggggggssgggdeodgggllllllo.......",  # 15
    "............oooollllRRgggRRgggggggggggggggggggsssdsggsddsggggggldgo.......",  # 16
    "........oooolllrggggggggggggggggggggggggggssssssddssssssssggggggggo.......",  # 17
    "....oooollrlgggRggggssssssssssssssssssssssssssddddsoooooooooooooooo.......",  # 18
    ".ooogRggggggssssssssssssssssssssssssssssssssddddddocccccccccbbbo..........",  # 19
    "ogggssssssssddddddddddddddddddddssssssssssssdddddobbssssssooooo...........",  # 20
    ".oooooooooooooooooooooooooddddddddddddddddddddddo.oooooooo................",  # 21
    "..........................oooooooooooooooooooooo..........................",  # 22
    "..........................................................................",  # 23
    "..........................................................................",  # 24
    "..........................................................................",  # 25
    "..........................................................................",  # 26
    "..........................................................................",  # 27
    "..........................................................................",  # 28
    "..........................................................................",  # 29
    "..........................................................................",  # 30
    "..........................................................................",  # 31
]

# Which part each body pixel belongs to: T tail, B trunk, N neck, H head (jaw and throat included).
# The tail bends along its spine as a chain, the trunk bends side to side, the neck shears, the head is rigid.
PARTS = [
    "..........................................................................",  # 0
    "..........................................................................",  # 1
    "..........................................................................",  # 2
    "..........................................................................",  # 3
    "..........................................................................",  # 4
    "..........................................................................",  # 5
    "..........................................................................",  # 6
    "..........................................................................",  # 7
    "..........................................................................",  # 8
    "..........................................................................",  # 9
    "................................BBBBBBBBBBBB......HHHHHHHH................",  # 10
    ".............................BBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHH.............",  # 11
    "..........................BBBBBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHHHH...........",  # 12
    "........................TTBBBBBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHHHHH..........",  # 13
    "....................TTTTTTBBBBBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHHHHHH.........",  # 14
    "................TTTTTTTTTTBBBBBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHHHHHHHH.......",  # 15
    "............TTTTTTTTTTTTTTBBBBBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHHHHHHHH.......",  # 16
    "........TTTTTTTTTTTTTTTTTTBBBBBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHHHHHHHH.......",  # 17
    "....TTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHHHHHHHH.......",  # 18
    ".TTTTTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHHHHH..........",  # 19
    "TTTTTTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBBBBBBBBBBNNNNHHHHHHHHHHHHH...........",  # 20
    ".TTTTTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBBBBBBBBBBNNN.HHHHHHHH................",  # 21
    "..........................BBBBBBBBBBBBBBBBBBBBNN..........................",  # 22
    "..........................................................................",  # 23
    "..........................................................................",  # 24
    "..........................................................................",  # 25
    "..........................................................................",  # 26
    "..........................................................................",  # 27
    "..........................................................................",  # 28
    "..........................................................................",  # 29
    "..........................................................................",  # 30
    "..........................................................................",  # 31
]
HIP_X, SHOULDER_X = 29, 43    # the girdles: the columns the hind and the front legs join the body at
HEAD_X = 50                   # the head's first column (the neck is the columns between the trunk and it)
EYE_X = 53                    # head columns from here forward hold the eye (the middle stage of a head lift)
FACE_X = 58                   # head columns from here forward (snout, nostril, the front of the jaw) lead a head lift

# The legs: origin (x, y) of the top-left cell, the rows ("." is air), the pivot row (the shoulder or hip, which
# stays on the body), the foot's rows, and which side. Each is drawn whole. The far legs are drawn behind the body
# and reach up from it; the near legs are drawn in front of the flank and reach down. Diagonal pairs step together.
FAR_HIND = {"origin": (21, 4), "pivot": 8, "foot": 2, "far": True, "rows": [
    ".o.o.o......",
    "odododo.....",
    ".odsssdoo...",
    "..oodssddo..",
    "....oodsdso.",
    "......odsgo.",
    ".....odssgo.",
    ".....odssgo.",
    ".....odssgo.",
]}
FAR_FRONT = {"origin": (39, 3), "pivot": 8, "foot": 3, "far": True, "rows": [
    ".......o.o.o.",
    "......odododo",
    "....oodsssdo.",
    "..oodsdsoo...",
    ".odsdoo......",
    ".odsso.......",
    "..odsso......",
    "..odssgo.....",
    "..odssgo.....",
]}
NEAR_HIND = {"origin": (25, 19), "pivot": 2, "foot": 3, "far": False, "rows": [
    "...ogllgo....",
    "..oglllggo...",
    "..ogllggso...",
    "...oggggso...",
    "....oggsso...",
    "...ogggsdo...",
    "..ogggsdo....",
    ".oglggso.....",
    "ogllggso.....",
    "ogogogoo.....",
    ".o.o.o.......",
]}
NEAR_FRONT = {"origin": (40, 19), "pivot": 2, "foot": 4, "far": False, "rows": [
    "..ogllgo.....",
    ".ogllggso....",
    ".ogllggso....",
    "..oggsgso....",
    "...oggssdo...",
    "....oggsso...",
    ".....ogglgo..",
    "....oogllggo.",
    "....ogllggso.",
    "....ogogogogo",
    ".....o.o.o.o.",
]}
LEGS = {"far_hind": FAR_HIND, "far_front": FAR_FRONT, "near_hind": NEAR_HIND, "near_front": NEAR_FRONT}

# The face, on the head (origins in the rest pose; they move with the head).
LID = {"origin": (54, 14), "rows": ["ss"]}                  # a half-blink: the upper lid over the eye's top row
TONGUE_OUT = [                                               # the flick: out, forked, out (the fork stays joined)
    {"origin": (66, 18), "rows": ["tt"]},
    {"origin": (66, 17), "rows": ["....t", "tttt.", "....t"]},
]

for _grid in (BODY, PARTS):
    assert len(_grid) == H and all(len(_r) == W for _r in _grid)
assert all((BODY[y][x] == ".") == (PARTS[y][x] == ".") for y in range(H) for x in range(W))
for _leg in LEGS.values():
    assert len({len(_r) for _r in _leg["rows"]}) == 1, "a leg's rows must have one width"


def paste(grid, origin, rows):
    """Draw rows onto a grid (a list of lists of keys) at origin; "." is air."""
    x0, y0 = origin
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c != "." and 0 <= y0 + j < len(grid) and 0 <= x0 + i < len(grid[0]):
                grid[y0 + j][x0 + i] = c
    return grid


def rest():
    """The drawing as it stands: far legs, body, near legs."""
    g = [["."] * W for _ in range(H)]
    paste(g, FAR_HIND["origin"], FAR_HIND["rows"])
    paste(g, FAR_FRONT["origin"], FAR_FRONT["rows"])
    paste(g, (0, 0), BODY)
    paste(g, NEAR_HIND["origin"], NEAR_HIND["rows"])
    paste(g, NEAR_FRONT["origin"], NEAR_FRONT["rows"])
    return ["".join(r) for r in g]


def to_image(rows, scale=1):
    from PIL import Image
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != ".":
                v = PALETTE[c]
                im.putpixel((x, y), (int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16), 255))
    return im.resize((im.width * scale, im.height * scale), 0) if scale > 1 else im


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    rows = rest()
    ys = [y for y, r in enumerate(rows) if r.strip(".")]
    xs = [x for r in rows for x, c in enumerate(r) if c != "."]
    crop = [r[max(0, min(xs) - 1):max(xs) + 2] for r in rows[max(0, ys[0] - 1):ys[-1] + 2]]   # a pixel of air round
    to_image(crop, 8).save(os.path.join(here, f"{KEY}_art_8x.png"))
    print(f"wrote {KEY}_art_8x.png: {max(xs) - min(xs) + 1}x{ys[-1] - ys[0] + 1} px, {len(PALETTE)} colours")
