"""The lizard: an original crawling reptile, drawn by hand pixel by pixel and kept as data.

A chameleon-like lizard of no real species. The body is a laterally flat barrel lit from the top left: one lit mass on
the upper back over the rump, a core shadow along the lower flank, a warm olive bounce under it and a 1-px ochre
highlight where the barrel turns under, following the round of the belly as it sags between the front and the hind legs
and fading into the bounce. Three teal bands wrap the barrel at uneven gaps, each bowing toward the head across it and
narrowing and darkening toward the belly; small lit tubercles in loose clusters along the barrel's curve, thinning into
the shade, give the flank its grain; a row of small cones runs along the spine. The top value sits on the rump and the
back only (two glints on the casque's rim); the legs' lit faces stay a step lower and end in a shadow tone at the
joints. A tall casque with a lit rim; a turret eye drawn as its own cone (a lit rim on the top left, a shaded ring on
the lower right, its opening and the pupil set toward the front); one mouth line from the snout back to below the eye.
Below the eye the head is modelled as rounded masses: a lit cheek under the turret and behind the mouth corner turns
into a core shadow toward the throat, where two soft gular folds (a lit ridge over a dark crease, running down and back)
lie above the ochre gular stripe that runs on into the belly's highlight; the lower jaw, lit just under the mouth line,
darkens toward the chin. The tail tapers from a thick root, a shadow notch where it leaves the rump, into a round
one-turn curl lit on its outer top-left edge; its ochre underside stripe starts thin under the hip, follows the curl and
fades out. The legs crouch: each thigh or upper arm leaves the body with shaded mass and bends at a clear knee (forward)
or elbow (back), a short shin or forearm runs down to the foot, and each foot grips with two mitten pads, a back pair
and a front pair. A dark crease on the body marks the back of the near upper arm, and a shadow notch the point of its
elbow. The far legs are the near legs a full value step darker, inked all round with no lit rim, each standing 3 px
ahead of its near twin and turned the same way (FAR_SHIFT), so at rest only a dark edge of each shows past it and the
lizard reads as two legs a side; the walk carries them out from behind. Side view,
facing right; 21 colours in hue-shifted ramps (greens from deep blue-teal to pale yellow, teals for the bands, ochres
from plum-brown to ochre), the lit outline (a dark green) on the top-left contours and the near-black ink on the shadow
side and at contacts.

One character is one pixel; '.' is empty. Every part that moves is its own layer, drawn whole (also where a part in
front of it covers it), so a part that moves never opens a hole. A layer is (x, y, rows): its top-left pixel on the
canvas and its rows. Joints are cut where one part overlaps another or the material changes:
  the tail goes in under the rump; the torso is one layer; the neck (the nape under the casque and the throat
  behind the jaw, coloured as the drawing at rest) lies over the torso's front, so the head can be carried on it: it
  moves with the body or a pose after it, the head a pose later on it; the head (skull, casque and upper jaw) sits
  over the neck, which it overlaps;
  the jaw tucks under the head along the mouth line (the head's lowest row, a deep blue-teal line, not ink), its
  hinge behind and below the eye, its throat green in the head's shade over a narrow gular stripe; the turret sits
  on the head and the pupil (amber round a dark pupil at its front) in its opening;
  each leg is two layers, the upper limb and the lower limb with its foot, sharing the drawn knee or elbow (a disc
  of overlap in both). The near upper limbs carry a shaded crease on their back and lower edges where they lie
  over the body. The mouth (its inside) and the tongue lie under the
  jaw and the head and only show when the jaw drops. The tongue is drawn at full reach in its own colours (an
  effect-like part): to show it shorter, cut its rod and draw its club (the last 8 columns) at the new tip.

    python creature.py           # writes lizard_art_8x.png next to this file: the drawing at rest, 8x

The loops (animate.py describes each in full). The torso always moves as one piece, and the head is carried on the
neck as a chain, a band a pose from the bottom up (the jaw, the eye's band, the casque):
  idle    the back breathes along its whole length twice a loop, the neck and then the head's bands following it a
          pose apart; the turret rolls about (the pupil leading inside it), the throat's pouch swells once, and the
          tail's coil loosens and curls back in as a chain from the root. The feet never leave their pixels.
  move    a lateral-sequence walk: the near hind, the near front, then the far hind and the far front half a stride
          later, the legs posed by two-bone inverse kinematics (lizard_legs.py); a planted foot goes back with the
          road; the body rises a pixel twice a stride with the neck and the jaw, the eye's band and the casque a
          pose and two behind, the tail link by link.
  attack  a tongue strike. Anticipation: the turret locks on; the head draws back and down to aim in three steps,
          the body rocking back over its feet a pose after each. Strike: the jaw turns down about its hinge and the
          tongue shoots out straight (a 1-frame smear, then full reach). Held key: the club at full reach, sparks
          off it, the back settling and the head after it. Recovery: the tongue reels in and the jaw closes as the
          back rises, the head coming home a pose behind.
  Check:  the eye is "E"'s colour; the ink is "o" and "O"; the tongue's and the mouth's colours are effects (pass
          them as --effects), so the check does not take them for stray pieces of the creature.
"""
import os

KEY = "lizard"
W, H = 104, 44            # the canvas of every frame (room ahead of the snout for the tongue's full reach)
GROUND = 41               # the ink row the feet stand on

PALETTE = {
    "o": "#140f1e",   # ink: the outline on the shadow side and at contacts, the pupil
    "O": "#2f5634",   # lit ink: the outline where the light falls (back, crest, casque, snout, tail, near legs)
    "1": "#152b37",   # scales, green ramp from a cool deep blue-teal (also the mouth line) ...
    "2": "#1d4949",
    "3": "#2b6a47",
    "4": "#4c8c41",
    "5": "#86b343",
    "6": "#c6d769",   # ... to a warm yellow-green
    "7": "#f0f4b0",   # the brightest lit points (casque rim, back, turret)
    "Q": "#4a9c84",   # the bands' teal where the light falls ...
    "q": "#2b706c",   # ... in the half light ...
    "k": "#1f5257",   # ... and in the shade toward the belly
    "h": "#4e5a2c",   # olive: the warm bounce just above the belly
    "a": "#45262c",   # ochre ramp, from a plum-brown shadow ...
    "b": "#74422f",
    "c": "#a66a31",   # ... to ochre (the belly's and the throat's highlight)
    "E": "#ffaf2e",   # the eye's amber ring (only the eye uses it: the check follows it)
    "m": "#5e1830",   # the inside of the mouth
    "t": "#8e2347",   # the tongue, dark ...
    "u": "#d84a68",   # ... mid ...
    "v": "#ff8f97",   # ... and light
}
INK = "oO"
EYE = PALETTE["E"]
TONGUE = "tuv"            # the tongue's own colours (and "m", the mouth): effect colours for the check
EFFECTS = TONGUE + "m"

LAYERS = {
    "tail": (1, 16, [
        "...................65..",
        "...............O6777653",
        "...............77776653",
        "...........OOOO76666543",
        ".........OO775665555432",
        "......OOO77766552222221",
        "....OO777666522222222cc",
        "...OQQ666552222222bbbbc",
        "..OQQQ522222bbcccccccc.",
        "..OQQQk22cccooo........",
        ".O6QQkkcoooo...........",
        ".O65kkbo...............",
        "O6622ao..OOo...........",
        "O6522o..O555o..........",
        "O6522o.o4oo34o.........",
        "O5522o..o..o5o.........",
        "oQQkko.....o3o.........",
        ".OQQk2o...o25o.........",
        ".oqq222ooo223o.........",
        "..o44222kk242o.........",
        "...o3444qq32o..........",
        "....oo22kkoo...........",
        "......oooo.............",
    ]),
    "body": (14, 10, [
        ".............o...o...o....................",
        ".........o...OOOO4OOO3o..o................",
        ".........OOOO6666665555OOo................",
        ".......OO6666Q666666655555OOoo............",
        "......O6777766Q66666655Q555554o...........",
        "....OOQ7777666QQ66665555QQ55544Oo.........",
        "...O777QQ666665QQQ455555QQ5555454O3.......",
        "...7777Qqq66555Qqq656655Qqq4444444443.....",
        "..O7776Qqq66555Qqq4444544Qqq45454454432...",
        "..66666Qqq446555Qqqq56554Qqq44434444444332",
        ".666666qqq555554qqqq44444qqq44544444444333",
        ".555555qq4444444qqkk54444qqk33333333333333",
        ".555555qq444454qqk4445444qqk44333333333333",
        "345544q44444444qqk444354qq3332334333333333",
        ".43o33354544444qk4444333qk3332333333333332",
        ".oo.4444444344kk33334333k33323333222222222",
        "....4333333333k33333333k333422222222222222",
        "....223hh3333k3333333333222222222222222222",
        "....oohhhhhhh22222222222222222hh2222222222",
        "......ooohhhhhhhh2222222222hhhhhh222222222",
        ".........oooohbbbhhhh222hhhbhhoooooooooooo",
        ".............oooobbcchhhcbbooo............",
        ".................oooocccooo...............",
        ".....................ooo..................",
    ]),
    "neck": (47, 12, [
        "...6655",
        "..O6555",
        ".O65554",
        "OO55444",
        "O555555",
        "5555555",
        "5555444",
        "54444qq",
        "44qqqqq",
        "qqqq444",
        "4444554",
        "3344555",
        "3334455",
        "2333444",
        "2333444",
        "2233444",
        "3333333",
        "2223222",
        "2222344",
        "o22222.",
        "..322..",
    ]),
    "mouth": (57, 25, [
        "............m",
        "........mmmmm",
        "....mmmmmmmmm",
        ".mmmmmmmmmmm.",
        "mmmmmmmm.....",
        "mmmm.........",
        "m............",
    ]),
    "tongue": (60, 24, [
        "....................................tttt..",
        "...................................tuvvut.",
        "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvtuvvvuut",
        "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuutttttuuuuuut",
        "...................................tuuuut.",
        "....................................ttt...",
    ]),
    "jaw": (47, 26, [
        "3333444443............43o",
        "3333444333........44443o.",
        "3333333322....44433332o..",
        "2223222244.233332211oo...",
        "222234432222332221oo.....",
        "o22222334432bbaooo.......",
        ".ob222222bcbooo..........",
        "..obbcccbooo.............",
        "...oooooo................",
    ]),
    "head": (47, 5, [
        "......Oo.................",
        ".....O76o................",
        ".....O664o...............",
        "....O6654o...............",
        "....O66534o..............",
        "...O765534o..............",
        "...O6655534o.............",
        "..O665554434o............",
        "..O6555444434OOO.........",
        ".O65554444443666OO.......",
        ".O5544444433333336OO.....",
        "O5555555544333333366O....",
        "555555544433333333356O...",
        "55554444qq333333333545O..",
        "54444qqqqq333333333444O..",
        "44qqqqqq443333333334444o.",
        "qqqq44444433333333344o4o.",
        "444455444433333333344444o",
        "334455544443333333444443o",
        "333445544444444444334433o",
        "233344444443444333332211o",
        "2333444443333333221111...",
        "223344433332221111.......",
        "33333333222111...........",
        "222322224431.............",
    ]),
    "turret": (57, 15, [
        "..OOOOO..",
        ".O665542.",
        "O65422231",
        "O54222242",
        "O54222242",
        "O43222232",
        "O43344421",
        ".2333221.",
        "..21112..",
    ]),
    "pupil": (61, 18, [
        ".EE",
        "EEo",
        ".EE",
    ]),
    "near_hind_thigh": (18, 23, [
        "...45554.........",
        ".3455554O........",
        "o34555544O.......",
        "o234555443O......",
        "o2334554433O.....",
        ".o2334444433O....",
        "..o2233444433O...",
        "....o223333444O..",
        "......o22333445O.",
        "........o2223344O",
        "..........oo2233o",
        "............ooo..",
    ]),
    "near_hind_shin": (21, 31, [
        ".........445O..",
        ".........3344O.",
        ".......oO44322o",
        "......O5432o...",
        ".....O543o.....",
        "....O543o......",
        "...O54o........",
        "..O5443o.......",
        ".O543o43o......",
        "O543o.o43o.....",
        "oooo...ooo.....",
    ]),
    "near_front_arm": (41, 23, [
        "....455...",
        "...4555431",
        "..O4554321",
        "..O455431.",
        ".O454321..",
        ".O544313..",
        "O5443o....",
        "O4432o....",
        "o3322o....",
        ".ooo......",
    ]),
    "near_front_hand": (41, 30, [
        ".4432...........",
        "O4432o..........",
        "o12443O.........",
        ".o2344455OO.....",
        "..oo2344455OO...",
        ".....o234445OO..",
        ".......o23444O..",
        ".........O54o...",
        "........O5443o..",
        ".......O543o43o.",
        "......O543o.o43o",
        "......oooo...ooo",
    ]),
}
# The far legs are the near legs a value step darker (their lit ink turned to the shadow ink, so they are inked all
# round), set FAR_SHIFT px ahead of them: in a side view a far leg stands just behind its near twin, the same shape
# turned the same way, and shows only where the walk carries it out from behind. Drawn on their own between the
# near legs, as they once were, the two far legs read as two more near ones: a lizard of four legs a side.
FAR_SHIFT = 3
FAR_TONE = {"7": "6", "6": "5", "5": "4", "4": "3", "3": "2", "2": "1", "O": "o"}
for _far, _near in (("far_hind_thigh", "near_hind_thigh"), ("far_hind_shin", "near_hind_shin"),
                    ("far_front_arm", "near_front_arm"), ("far_front_hand", "near_front_hand")):
    _x, _y, _rows = LAYERS[_near]
    LAYERS[_far] = (_x + FAR_SHIFT, _y, ["".join(FAR_TONE.get(ch, ch) for ch in row) for row in _rows])

ORDER = ["far_hind_thigh", "far_hind_shin", "far_front_arm", "far_front_hand", "tail", "body", "neck", "mouth",
         "tongue", "jaw", "head", "turret", "pupil",
         "near_hind_thigh", "near_hind_shin", "near_front_arm", "near_front_hand"]
HIDDEN_AT_REST = ("mouth", "tongue")

# The rig's points, in canvas pixels (the drawing at rest). Each is where a part turns or what it aims from.
RIG = {
    "neck_root": (47, 24),            # where the neck layer joins the body (it moves a pose ahead of the head)
    "neck": (48, 22),                 # where the head sits on the neck
    "jaw_hinge": (56, 29),            # behind and below the eye: the jaw drops about this, never at the mouth corner
    "turret": (61, 19),               # the turret's centre pixel; the pupil (a dark pixel in an amber ring) looks out
    "pupil": (63, 19),                # the pupil's dark pixel at rest, looking ahead
    "mouth": (69, 26),                # the tongue leaves the mouth here: its rod is rows 26 (light) and 27
    "tongue_reach": 101,              # the club's last column at full reach
    # the tail's spine, root to tip (x, y, half-width), evenly spaced along it: cut the tail into links across it to
    # curl it as a chain
    "tail_spine": [(21.0, 20.6, 4.2), (16.3, 21.6, 3.7), (12.0, 23.5, 3.3), (7.4, 25.0, 3.1), (4.4, 28.5, 2.9),
                   (4.5, 33.2, 2.6), (8.0, 36.2, 2.4), (12.5, 35.2, 2.0), (13.2, 30.8, 1.6), (9.4, 30.7, 1.0)],
    # each leg: the hip or shoulder (it stays on the body), the knee or elbow (where its two layers meet), the
    # ankle or wrist, and the back and front pads' tips (their soles on the row above the ground ink)
    "near_hind": [(23, 26), (32, 32), (25, 37), (21, 40), (30, 40)],
    "near_front": [(47, 26), (43, 32), (51, 37), (47, 40), (56, 40)],
}
for _leg in ("hind", "front"):                    # the far legs' points: the near ones', FAR_SHIFT ahead
    RIG[f"far_{_leg}"] = [(x + FAR_SHIFT, y) for x, y in RIG[f"near_{_leg}"]]


def layer_pixels(part, dx=0, dy=0):
    """{(x, y): char} for one layer, moved by (dx, dy)."""
    x0, y0, rows = LAYERS[part]
    return {(x0 + i + dx, y0 + j + dy): ch for j, row in enumerate(rows) for i, ch in enumerate(row) if ch != "."}


def compose(placed):
    """One frame from placed pixels, a list of {(x, y): char} back to front. The outline is drawn last: a pixel of
    the creature that a pose left at an open edge gets ink (the tongue and the mouth keep their own colours)."""
    canvas = {}
    for px in placed:
        canvas.update(px)
    frame = [["."] * W for _ in range(H)]
    for (x, y), ch in canvas.items():
        if 0 <= x < W and 0 <= y < H:
            frame[y][x] = ch
    for y in range(H):
        for x in range(W):
            ch = frame[y][x]
            if ch == "." or ch in INK or ch in EFFECTS:
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if not (0 <= nx < W and 0 <= ny < H) or frame[ny][nx] == ".":
                    frame[y][x] = "o"
                    break
    return ["".join(r) for r in frame]


def rest():
    return compose([layer_pixels(p) for p in ORDER if p not in HIDDEN_AT_REST])


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


def crop(rows, pad=1):
    """The rows cut to the drawing's box, with pad pixels of air round it."""
    ys = [y for y, r in enumerate(rows) if r.strip(".")]
    xs = [x for r in rows for x, c in enumerate(r) if c != "."]
    return [r[max(0, min(xs) - pad):max(xs) + pad + 1] for r in rows[max(0, ys[0] - pad):ys[-1] + pad + 1]]


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{KEY}_art_8x.png")
    art = crop(ART)
    to_image(art, 8).save(path)
    print(f"wrote {KEY}_art_8x.png: {len(art[0]) - 2}x{len(art) - 2} px, {len(PALETTE)} colours")
