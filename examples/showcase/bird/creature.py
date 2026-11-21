"""The bird: an original river diver, drawn by hand pixel by pixel and kept as data.

A kingfisher-like bird of no real species, big-headed and heavy-bodied: a deep teal back, a rust-orange breast
brightest high under the throat and darkening past a clear terminator to a plum underside, a white throat, a round
teal cap with faint lighter bars, highest over the eye and falling in a curve to the nape, a white flash running back
and down from behind the rust cheek toward the nape, a crest swept back off the rear of the cap as one tapered strand
(a teal root on the cap, a darker underside, an azure tip), a rust face band round a dark eye, a long dagger bill
(dark, the lower mandible orange at its base), a short tail whose pale band is shaded across its form (lit on top,
slate below) and whose dark tip is forked into two tines, and two coral feet, each a short tarsus and a toe tapering
forward to one dark claw. Side view, facing right, light from the top left. 31 colours in hue-shifted ramps: the
teal's shadows lean toward navy and its lights toward mint, the rust's shadows toward plum and its lights toward gold,
the whites' shadows toward slate blue, the azure's shadow toward deep blue, the underwing's slate toward teal, the
coral feet's shadow toward plum.

One character is one pixel; '.' is empty. Every layer is ((x, y) of its first character, rows) on the W x H frame,
drawn whole where a part in front covers it, so a part that moves never opens a hole. The parts carry no outline:
compose() draws it last, round what is on the frame (see there). The rig, back to front:

    wing_far   the far wing: its own drawn key where WINGS has one (up_far), else the near key set back by
               FAR_OFFSET; always one tone darker (FAR_TONES: one step down the same ramp, so its feather bars and
               lit edges stay), showing only as a rim of feather tips behind the near wing
    tail       a short banded tail, forked at the tip; its root runs under the rump, so it can turn and lift
    body       the torso (back, flank, breast) as one piece: lit along the back, the flank's rust darkening
               past a terminator that runs from the front of the breast down to the vent
    foot_far   } the feet, tucked in flight; their top rows run up under the belly; open air parts them (no
               pocket closed between them), the far one a tone darker and shorter
    foot_near  }
    wing       the near wing: one of the hand-drawn keys (WINGS, in bird_wings.py), pivoting at SHOULDER
    neck       the neck: the nape's teal at the back, the bright upper breast in front; drawn whole under the head
               and over the body's breast (strips of overlap both ways), so the head can be carried on it: it bends
               to carry the head (its upper rows ride the head, the lower ones the body)
    nape       the crest: one strand swept back and a little up off the rear of the cap, tapering to an azure
               tip lit over a darker step; a child of the head (it follows a pose late)
    head       cap, face, eye and the white throat; it rides on the neck
    bill_low   the lower mandible: the jaw, hinged at the gape's base (JAW_HINGE), so the bill can open
    bill_up    the upper mandible, the gape line its bottom row

Cuts sit where the drawing changes material or one part overlaps another: the neck under the white throat, the tail
under the rump, the wing at the shoulder, the jaw on the gape line. Head, nape, neck and body join with no line
between them (MERGE); every other part is set off from what is behind it by a line.

The wing keys are drawings, not squeezes made at run time: at this size a wing pressed flat by numbers loses its
feathers. Keys (bird_wings.py): up (+1, the upper side), half_up (+0.5), level (0, a thin blade seen edge-on),
half_down (-0.5) and down (-1, the underside) for the beat; cock, cock_far, sweep and fold (closed along the flank)
for the attack. The up key
is a fan: four primaries radiating from the wrist (the outermost the highest and longest, each further one lower and
swung further back) and four secondaries radiating from the elbow into a scalloped trailing edge, every feather a
band with a lit front edge and a shadow line where it lies on the next, under a lit covert band along the leading
edge with mint glints. up_far is the same fan turned a little forward and raised, kept only where it shows behind
the near wing: a rim of staggered feather tips above and behind it.

The loops (animate.py describes each in full). In all of them the torso moves as one piece (the body layer whole,
the neck bending between it and the head), and the head rides the neck as a chain on the body's beat: the body
first, the head a pose later, the bill and the crest a pose after it, the bill's lag drawn as a small turn of the
head (the nod keys in bird_heads.py), never a lone step of the head as a block.
    idle   a hover: three slow beats through the beat keys, the body rising a pixel on the downstroke and the head,
           the bill, the crest, the tail and the hanging feet following as chains; a call on the second beat (the
           bill opens about JAW_HINGE), a look down at the water on the third (the head turned down, the nods 3
           and 6)
    move   level flight: two quicker beats, the body bobbing, the head a pixel lower and the tail a pixel higher,
           the head nodding on the beat, the tail steering as a chain, the feet tucked away
    attack a dive strike: the head pitched nose up and the wings cocked up and back (anticipation), swept back for
           a run forward, then folded for the drop along the bill's line (strike), the head carried whole as one
           of its drawn dive keys (bird_heads.py); held at the end of the thrust, then a recoil on an arc in small
           turns, the head turning back up with the body a pose behind it (a drawn key every pose), the wings
           unfolding through the swept key, and one beat back to hover

    python creature.py           # writes bird_art_8x.png next to this file: the drawing at rest, 8x
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bird_wings import WINGS  # noqa: E402

KEY = "bird"
W, H = 80, 64                 # the frame: room ahead of the bill and below the belly for the dive
SHOULDER = (39, 31)           # the near wing's pivot (every wing key is drawn on it)
JAW_HINGE = (55, 29)          # the lower mandible turns about the gape's base
FAR_OFFSET_DEFAULT = (-3, -1)  # the far wing sits a little back and up, so it peeks past the near one;
FAR_OFFSET = {"fold": (-1, -1),  # folded it shows only as a sliver above the back, edge-on as a rim over the near
              "level": (-1, -1),  # blade (its rear never reaching past the tail root),
              "half_down": (-2, 1), "down": (-2, 1)}   # and on the downstroke it peeks below the near wing

PALETTE = {
    "o": "#0e0a16",   # ink: the outline on shadow sides, the gape line
    "O": "#1f5d68",   # lit outline on teal, white and slate (edges facing the light): a dark teal, not ink
    "P": "#5a1f2c",   # lit outline on rust, white and the feet
    "a": "#101a31",   # teal ramp: shadow (navy)
    "b": "#15314d",   #   dark
    "c": "#17525f",   #   low
    "d": "#1c767a",   #   mid
    "e": "#2d9d93",   #   light
    "f": "#5ac8ae",   #   highlight (toward mint)
    "g": "#b2efd3",   #   spots and glints
    "z": "#43cfe9",   # azure: the crest's glowing tips, lit
    "Z": "#2386b4",   #   and their shadow step
    "r": "#4a1c2e",   # rust ramp: shadow (plum)
    "s": "#82312c",   #   dark
    "t": "#b44d27",   #   low
    "u": "#da732e",   #   mid
    "v": "#f29d46",   #   light
    "x": "#ffd27c",   #   highlight (toward gold)
    "n": "#3d6274",   # underwing: the flight feathers' slate, leaning teal toward the upper side
    "N": "#5e8e98",   #   and their lit vanes
    "q": "#6c7a96",   # white ramp: shadow (slate), also the underwing's lit vanes
    "W": "#c0c8d0",   #   mid
    "w": "#f5f3e8",   #   light
    "h": "#7c2c45",   # feet, coral: shadow (toward plum)
    "i": "#d9606e",   #   mid
    "j": "#ff9c8c",   #   light
    "k": "#272133",   # bill: dark, also the claws
    "l": "#4d4661",   #   mid
    "m": "#7d7791",   #   highlight
    "E": "#22110f",   # the eye (only the eye uses it: the check follows it)
    "G": "#fffbea",   # the eye's glint
}
INK = "oOP"
EYE = PALETTE["E"]
TEAL, RUST, WHITE, BILL, FEET = set("abcdefgnNzZ"), set("rstuvx"), set("qWw"), set("klm"), set("hij")
GLOW = set("zZ")   # the crest's bright tips: they keep their colour on the edge instead of taking the outline
FAR_TONES = {"g": "f", "f": "e", "e": "d", "d": "c", "c": "b", "b": "a", "a": "a", "z": "Z", "Z": "c",   # one step
             "x": "v", "v": "u", "u": "t", "t": "s", "s": "r", "r": "r", "w": "W", "W": "q", "q": "n", "N": "n",
             "n": "b", "j": "i", "i": "h", "h": "h"}

LAYERS = {
    "tail": ((7, 34), [
        "................eeeed",
        "...........weeeeedddd",
        "......eeeewwdddddddcc",
        "deeeeeeeeewWddddccccc",
        "dddddddddddWWcccccccbb",
        "cccccccccccWqccbbbbbb",
        "....bccccccqqbbbbbbbb",
        ".ccccccccccqbbbbbbb",
        ".bbbbbbbbbbbbbb",
        "..bbbbbbbbb",
    ]),
    "body": ((20, 27), [
        "...............eeeddd",
        "...........eeeeedddddccc",
        ".........eeeeeddddddccuvvv",
        ".......eeeeeddddddddcuvvvvvu",
        ".....deeeeddddddddddcuuvvxxvvu",
        "...edeeeedddddddddcuuuvvxxxvvu",
        "...ddeeedddddddddcuuuuvvvxvvvut",
        "..dddeedddddddccuuuuuuvvvvvuuut",
        ".ddddddddddcuvvuuuuuuvvuuuuuutt",
        ".cdddddddcctuuuuuuvvuuuuuuuttts",
        "ddddddddcctuuuuvuuuuuuuuuttttts",
        "dddddcccuuvvuuuuuuuuuutttttsss",
        "cdddcccuuuuttuuuuuutttttttssss",
        "cccbbbtuuuuuuuuututtttttsssrr",
        ".cbbbtuuttuuuuuuuttttttsssrr",
        ".bbbttuuuuuuutttttttssssrrr",
        "..bttttuuuuuutttttsssssrrr",
        "...rstttttttttsssssssrrr",
        ".....rrsssssssssrrrr",
        "........rrrrrrr",
    ]),
    "foot_far": ((33, 44), [
        "hhhi",
        "hhhii",
        ".hhhii",
        ".hhhiii",
        "..hhhik",
    ]),
    "foot_near": ((39, 43), [
        ".hiij",
        ".hiij",
        "..hiij",
        "..hhiijjj",
        "...hhiiijjjkk",
        "....hhhhiii",
    ]),
    "nape": ((33, 15), [
        "..zzOOO....",
        "..oZeeefOO.",
        "....occdde.",
        ".....oobc..",
    ]),
    "neck": ((39, 26), [
        "bcc............",
        "bccd...........",
        "bccdd..........",
        "bccddt.........",
        "bccdtuuu.......",
        "bccdtuuvvvu....",
        "bcdtuuvvvvvvuut",
        "bcttuvvxxvvvuut",
        ".ctuvvxxxvvvuut",
        "..tuvvxxvvvuuts",
        "..tuuvvvvvuutts",
        "...tuuvvuuutts.",
        "....ttuuuttss..",
        "......tttss....",
    ]),
    "head": ((39, 15), [
        "......dffee",
        "....deffgffed",
        "..cdeffeeffgfee",
        ".cdeffgeeeffeeed",
        "cddeefffeeeeffedd",
        "ccddeeeeffeeeeedd",
        "ccddeeffeeeeedddcc",
        "cccdddeeeeeedddccc",
        ".cccdtuuuvvvuuuucc",
        ".bcctuuvvvvvuuuuuc",
        ".bccwwvvvvuGEvvutc",
        ".bcwwWuuvuuEEuuttc",
        ".bwWWquuuuuuuuutts",
        ".wWqccccccccccccc",
        ".bcccccbbbbcccbbbb",
        "..bcccWwwwwwwWWq",
        "..bccWwwwwwwWWqq",
        "...ccWwwwwWWWq",
        "....cWWWWWqq",
    ]),
    "bill_low": ((55, 29), [
        "tuuuutlllkkkk",
        "stttskkkk",
        "rssk",
    ]),
    "bill_up": ((55, 24), [
        "kkkk",
        "lmmmkkkk",
        "llllmmmmkkkk",
        "kkkkllllmmmmkkk",
        "oooooooooolllkkk",
    ]),
}

ORDER = ["wing_far", "tail", "body", "neck", "foot_far", "foot_near", "wing", "nape", "head", "bill_low", "bill_up"]
MERGE = {frozenset(p) for p in (("head", "body"), ("nape", "head"), ("nape", "body"), ("bill_low", "bill_up"),
                                ("neck", "body"), ("neck", "head"), ("nape", "neck"))}
SHADE_LINE = {"t": "a", "r": "r", "w": "q", "b": "o", "f": "o"}   # an inner line on a lit side: the darkest of the material
SOFT = {("wing", "body"): "b"}   # the near wing's lower edge on the back: a dark teal, not ink, so the wing grows out of it


def material(ch):
    return "t" if ch in TEAL else "r" if ch in RUST else "w" if ch in WHITE else "f" if ch in FEET else "b"


def layer_pixels(name, dx=0, dy=0):
    (x0, y0), rows = LAYERS[name]
    return {(x0 + i + dx, y0 + r + dy): ch for r, row in enumerate(rows) for i, ch in enumerate(row) if ch != "."}


def wing_pixels(key, far=False, dx=0, dy=0):
    """A wing key as pixels. The far wing is its own drawing where one exists (KEY_far: the same feathers turned
    forward about the shoulder and a little smaller, so its fingertips fan out past the near wing's), else the near
    key set back by FAR_OFFSET; either way a tone darker (FAR_TONES)."""
    if far and key + "_far" in WINGS:
        key, far_drawn = key + "_far", True
    else:
        far_drawn = False
    (x0, y0), rows = WINGS[key]
    if far and not far_drawn:
        ox, oy = FAR_OFFSET.get(key, FAR_OFFSET_DEFAULT)
        dx, dy = dx + ox, dy + oy
    return {(x0 + i + dx, y0 + r + dy): (FAR_TONES.get(ch, ch) if far else ch)
            for r, row in enumerate(rows) for i, ch in enumerate(row) if ch != "."}


def compose(parts):
    """One frame (a list of strings) from placed parts: [(group, {(x, y): ch}), ...] in ORDER. The outline is drawn
    last, on the parts' own edge pixels: toward the air it is a lit line where the edge faces the light (air above or
    to the left, unless the pixel is also open below and to the right): O, a dark teal, on teal, white and slate, P,
    a plum, on rust and the feet; and ink where it faces away. Where a part lies over another it does not MERGE
    with, its edge gets a line too: ink on its shadow sides (a dark teal where the near wing lies on the back, SOFT),
    its own darkest tone on the lit ones (a selective outline). The crest's glowing tips (GLOW) and pixels the
    drawing marks as ink stay as drawn."""
    canvas, owner = {}, {}
    rank = {g: i for i, g in enumerate(ORDER)}
    for group, px in sorted(parts, key=lambda p: rank[p[0]]):
        for k, ch in px.items():
            canvas[k] = ch
            owner[k] = group
    out = dict(canvas)
    for (x, y), ch in canvas.items():
        if ch in INK or ch in GLOW:
            continue
        me, mat = owner[(x, y)], material(ch)
        air = {d: (x + dx, y + dy) not in canvas for d, dx, dy in (("d", 0, 1), ("r", 1, 0), ("l", -1, 0), ("u", 0, -1))}
        line = None
        if any(air.values()):
            lit = (air["u"] or air["l"]) and not (air["d"] and air["r"])
            line = ("O" if mat in "tw" else "o" if mat == "b" else "P") if lit else "o"
        else:
            for nx, ny, lit in ((x, y + 1, False), (x + 1, y, False), (x - 1, y, True), (x, y - 1, True)):
                other = owner[(nx, ny)]
                if other != me and frozenset((me, other)) not in MERGE and rank[other] < rank[me]:
                    line = SHADE_LINE[mat] if lit else SOFT.get((me, other), "o")
                    if not lit:
                        break
        if line:
            out[(x, y)] = line
    frame = [["."] * W for _ in range(H)]
    for (x, y), ch in out.items():
        if 0 <= x < W and 0 <= y < H:
            frame[y][x] = ch
    return ["".join(r) for r in frame]


def rest(near="up", far="up"):
    """The drawing at rest: both wings raised, the far one set back and darker, every part in place."""
    parts = [("wing_far", wing_pixels(far, far=True)), ("wing", wing_pixels(near))]
    parts += [(name, layer_pixels(name)) for name in LAYERS]
    return compose(parts)


ART = rest()


def to_image(rows, scale=1):
    from PIL import Image
    im = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                h = PALETTE[ch]
                im.putpixel((x, y), tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST) if scale != 1 else im


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{KEY}_art_8x.png")
    to_image(ART, 8).save(path)
    used = {ch for row in ART for ch in row if ch != "."}
    print(f"wrote {KEY}_art_8x.png ({len(PALETTE)} colours, {len(used)} in the rest pose)")
