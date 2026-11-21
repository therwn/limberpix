"""The showcase creature as data: a small round songbird (a "tuftwing"), side view, facing right.

Everything here is hand-placed pixels. A palette maps one character to one colour; each part is a list of strings,
one character per pixel ("." is empty), placed on the frame at `at`. The parts are cut where they will move apart:

    tail_root  the tail where it leaves the rump; tail_up, tail_mid, tail_low are the fan's three feathers, its
               children: a chain (the fan turns a tick after the root) that spreads and closes
    body       the round body; the breast is shaded in curved clusters round the ball, lit from the top left
    head       cap, cheek and throat; `beak` and `crest` are its children (the crest follows the head a tick late)
    WINGS      the near wing in five hand-drawn keys of its stroke (pixel-animate 3.5: a side-on wing seen
               foreshortened): raised (+1), half up (+0.5), edge-on (0), half down (-0.5) and down under the belly
               (-1). Up and half up show the upper side (coverts, then four primaries, one dark line between each);
               edge-on is a tapered blade with one highlight row; the down keys show the pale underside, the
               feathers spreading down and back. The far wing is the same keys a tone darker (FAR_TONES).
    EYE        the eye with its glint, laid down whole at the head's place after everything else

At 50 px a wing squeezed by numbers collapses into dashes when edge-on and into a mirror when down, so the wing's
foreshortening is drawn, once per key, and the rig only picks the key and moves it by whole pixels.

The parts carry no outline: animate.py draws a one-pixel outline round each group as it lays them down, back to
front (the pixel-animate method: draw the outline last), and gives the edges facing the light a lighter outline
(M on blue, N on warm). Sixteen colours. The ramps shift hue: the blue's shadow leans violet and its light green,
the warm shadow leans rose and its light yellow.

    python creature.py           # writes bird_art_8x.png next to this file: the drawing at rest, 8x
    python animate.py            # the loops (see there)
"""
import os
from collections import namedtuple

Layer = namedtuple("Layer", "at rows")

W, H = 50, 54                                             # the frame, in game pixels
KEY = "bird"                                              # file stem of everything written

PALETTE = {
    "K": "#1b1424",   # outline: plum black (shadow side)
    "M": "#2b4180",   # outline on lit edges of the blue plumage
    "N": "#8c3a2e",   # outline on lit edges of the warm plumage and the beak
    "e": "#120c1c",   # the eye
    "w": "#fbf0d6",   # cream: cheek, the eye's glint, the underwing's light
    "a": "#2a2c66",   # blue ramp: shadow (violet-blue)
    "b": "#2f5c9c",   #            base
    "c": "#3f90c2",   #            light
    "d": "#8ad8c8",   #            highlight (toward green)
    "u": "#a9c6e0",   # underwing: pale blue
    "r": "#a3354d",   # warm ramp: shadow (rose)
    "o": "#d9623a",   #            base
    "p": "#f2a04c",   #            light
    "y": "#ffd88a",   #            highlight (toward yellow)
    "S": "#3a3348",   # ground shadow
    "T": "#544b63",   # ground shadow, faded (its ends while the bird is up)
}
OUTLINE, OUTLINE_LIT, OUTLINE_WARM = "K", "M", "N"
BLUES, WARMS = set("abcduw"), set("ropy")
INK = ("K", "M", "N")                                     # what pixel_anim_check is told is outline (--ink)
EYE_COLOUR = PALETTE["e"]                                 # --eye
SHADOWS = ("S", "T")                                      # --shadow
FAR_TONES = {"d": "c", "c": "b", "b": "a", "a": "a", "u": "c", "w": "u"}   # the far wing: a step darker

PARTS = {
    "tail_root": Layer(at=(13, 35), rows=[
        "....bbb",
        "...bbab",
        "..bbaab",
        ".bbaaab",
        "bbaaaa.",
        "baaaa..",
    ]),
    "tail_up": Layer(at=(4, 38), rows=[
        "........ccc",
        ".....cccbbb",
        "..cccbbbaaa",
        "dcbbbaaa...",
        ".baaa......",
    ]),
    "tail_mid": Layer(at=(5, 39), rows=[
        "........cc",
        "......ccbb",
        "....ccbbaa",
        "..ccbbaa..",
        "dcbbaa....",
        ".baa......",
    ]),
    "tail_low": Layer(at=(7, 41), rows=[
        "......cc",
        ".....cbb",
        "...ccbaa",
        "..cbba..",
        "dcbaa...",
        ".ba.....",
    ]),
    "body": Layer(at=(15, 23), rows=[
        "..........cccc..........",
        ".......cdddccbb.........",
        ".....cddddddccbb........",
        "....cdddddddcccbb.......",
        "...cddddddddcccbbb......",
        "..ccdddddddccccbbbp.....",
        "..cccdddddcccccbbppp....",
        ".ccccccccccccbbbppyypp..",
        ".cccccccccccbbbppyyyyppo",
        "cbccccccccbbbpppyyyyppoo",
        "cbbcccccbbbbppppyyyppppo",
        "cbbbbbbbbbppppppppppppoo",
        "abbbbbbbpppppppppppppooo",
        ".abbbbooppppppppppppooor",
        ".aaboooopppppppppppooor.",
        "..arooooopppppppppoorrr.",
        "..rroooooooppppppoorrr..",
        "...rrroooooooooooorrrr..",
        ".....rrrrooooooorrrr....",
        "......rrrrrrrrrrrrr.....",
        "..........rrrrr.........",
    ]),
    "head": Layer(at=(28, 15), rows=[
        ".....cdddcc.....",
        "...cddddddccc...",
        "..cddddddcccbb..",
        ".cdddddcccccbbb.",
        ".ccdddccccccbbb.",
        "ccccccccccccbbbb",
        "bccccccwwwwwwbbb",
        "bbccccwwwwwwwwwb",
        "abbcccwwwwwwwwww",
        ".abbcwwwwwwwwwy.",
        ".abbbwwwwwwwyyp.",
        "..abpyyyyyyyppo.",
        "...bppyyyyyppo..",
        ".....pppppppo...",
    ]),
    "beak": Layer(at=(44, 21), rows=[
        "yp..",
        "yppo",
        "or..",
    ]),
    "crest": Layer(at=(29, 9), rows=[
        "c........",
        "dd.......",
        ".cdd.d...",
        "..ccddd..",
        "...bccddc",
        "....bcccc",
    ]),
}

# The near wing's five keys, from raised to down. Each is placed on the frame as drawn (then lifted with the body).
WINGS = {
    1.0: Layer(at=(7, 5), rows=[
        "....c..............",
        "....ddc............",
        ".....ddc...........",
        "..c..ddc...........",
        "..ccaddc...........",
        "...ccaddc..........",
        "...ccaddc..........",
        ".c..ccaddc.........",
        ".ccaccaddc.........",
        "..ccaccaddc........",
        "..ccaccaddc........",
        "c..ccaccaddc.......",
        "ccaccaccaddc.......",
        ".ccaccaccaddc......",
        ".ccaccaccaddc......",
        "..ccaccaccaddb.....",
        "..ccaccacbddcb.....",
        "...ccaccaddcccb....",
        "...ccacbddccccb....",
        "....ccaddccccccb...",
        "....cbddcccccccb...",
        ".....ddcccccccccb..",
        "......cccccccbbbbb.",
        "........ccccbbbbbb.",
        "...........bbbbbb..",
    ]),
    0.5: Layer(at=(8, 17), rows=[
        "....c.............",
        "..c.ddc...........",
        "..ccaddc..........",
        ".c.ccaddc.........",
        ".ccaccaddc........",
        "c.ccaccaddc.......",
        "ccaccaccaddc......",
        ".ccaccaccaddc.....",
        "..ccaccaddcccb....",
        "...ccacddcccccb...",
        "....cbddcccccccb..",
        ".....dccccccbbbbb.",
        "......cccccbbbbbbb",
    ]),
    0.0: Layer(at=(9, 25), rows=[
        "cddd..............",
        "bbccdddd..........",
        "..aabbccdddd......",
        "......aabbccdddddd",
        "..........aabbbccb",
        ".............aaaa.",
    ]),
    -0.5: Layer(at=(8, 26), rows=[
        "............uuuwwc..",
        ".........uuuuuuuuwwc",
        ".......uuuuuuuuuuwwc",
        "......cccccccccccwc.",
        ".....uuucuucuucwuu..",
        "...uuucuuucuucwuu...",
        ".uuuucuucuuucwuu....",
        "cuucuuucuuucwuu.....",
        "..uuuucuuucwuu......",
        "..cuucuuucwuu.......",
        "....uuuucwuu........",
        "....cuucwuu.........",
        ".......cuc..........",
    ]),
    -1.0: Layer(at=(8, 26), rows=[
        "............uuuwwc..",
        ".........uuuuuuuuwwc",
        ".......uuuuuuuuuuwwc",
        "......cuuuuuuuuuuwc.",
        "......cccccccccccwc.",
        "......uucuucuucwuu..",
        ".....uucuuucuucwuu..",
        "....uuucuucuuucwu...",
        "...uuucuuucuucwuu...",
        "..uuucuuucuuucwu....",
        ".uuuucuuucuuucwu....",
        ".cuucuuucuuucwu.....",
        "....uuuucuuucwu.....",
        "...uuuucuuuucwu.....",
        "....cuucuuucwu......",
        ".......uuuucwu......",
        "......uuuucwu.......",
        ".......cuucwu.......",
        "..........wuc.......",
        "..........cc........",
    ]),
}

# The eye is laid down last at the head's place, whole, so the head's tilt never smears it: the glint top left.
EYE = Layer(at=(37, 19), rows=["we", "ee", "ee"])

# Pivots, in frame coordinates (pixel x covers x..x+1, so its centre is x + 0.5).
PIVOT = {
    "tail_root": (17.0, 38.0),    # where the tail leaves the rump
    "tail_fan": (14.5, 39.5),     # the fan's joint on the root: its three feathers spread about it
    "head": (38.0, 20.5),         # the head turns about the eye, so the eye stays put
    "crest": (34.5, 14.5),        # the tuft's root on the crown
}
FAR_WING_OFFSET = (5, -2)         # the far wing sits a little ahead and higher, seen past the body

# The ground shadow: fixed rows at the bottom of the frame (a flier's shadow never slides; its bottom row keeps its
# columns). While the bird is up it fades: the top row loses a pixel each end, the bottom row's ends turn pale.
SHADOW = Layer(at=(18, 51), rows=[
    "..SSSSSSSSSSSS..",
    "SSSSSSSSSSSSSSSS",
])
SHADOW_UP = Layer(at=(18, 51), rows=[
    "...SSSSSSSSSS...",
    "TTSSSSSSSSSSSSTT",
])

# Back to front. Each group is laid down inside one outline, so the head and body read as one silhouette.
GROUPS = [["far_wing"], ["tail_root", "tail_low", "tail_mid", "tail_up"], ["body", "beak", "head", "crest"],
          ["wing"]]
# Parts too small to turn (a turned 3-px beak loses its point): they follow their parent by whole pixels only.
RIGID = {"beak": (45.0, 22.5)}    # the point whose place, rounded, carries the part


def pixels(layer):
    """{(x, y): char} of a layer, placed on the frame."""
    x0, y0 = layer.at
    return {(x0 + i, y0 + j): ch for j, row in enumerate(layer.rows) for i, ch in enumerate(row) if ch != "."}


def rgb(ch):
    v = PALETTE[ch]
    return int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16)


def _selfcheck():
    named = list(PARTS.items()) + [(f"wing {s:+}", lay) for s, lay in WINGS.items()]
    for name, layer in named + [("eye", EYE), ("shadow", SHADOW), ("shadow up", SHADOW_UP)]:
        widths = {len(r) for r in layer.rows}
        assert len(widths) == 1, f"{name}: rows of different widths {sorted(widths)}"
        bad = {ch for r in layer.rows for ch in r if ch != "." and ch not in PALETTE}
        assert not bad, f"{name}: characters not in the palette {sorted(bad)}"
        for (x, y) in pixels(layer):
            assert 0 <= x < W and 1 <= y < H, f"{name}: pixel ({x}, {y}) off the frame"
    assert len(PALETTE) <= 16, "the palette has grown past 16 colours"


_selfcheck()

if __name__ == "__main__":
    import animate
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{KEY}_art_8x.png")
    animate.art_preview(path)
    print("wrote", os.path.basename(path))
