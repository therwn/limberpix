"""The beast: an original small four-legged walker, drawn by hand pixel by pixel and kept as data.

A dusk fox of no real species: big ears with dark tips, dark stockings, a teal eye, a white bib and a full brush of
a tail with a white tip. Side view, facing right, light from the top left, 16 colours.

One character is one pixel; '.' is empty. Every part that moves is its own layer, drawn whole (also where a part in
front of it covers it), so a part that moves never opens a hole:
  T tail, B body (torso), K neck, cheek ruff and bib, H head (skull, face, eye, jaw), F far ear, N near ear.
Each layer is (first row, rows); every row starts at column 0 of the frame, so the layers line up as written.

The legs are their own small drawings: eight hand-drawn poses each for the hind and the front legs (one walk
stride; pose 2 is the standing one), with a bent hock on the hind legs, a shaped paw, dark stockings, and the far
legs in the same shapes a clear tone darker. They are placed under the body's fur but over its outline (compose), so
a leg runs into the body with no line across it.

    python creature.py           # writes beast_art_8x.png next to this file: the drawing at rest, 8x
"""
import os

KEY = "beast"
W, H = 52, 36            # the canvas of the drawing and of every frame
GROUND = 34              # the ink row the paws stand on

PALETTE = {
    "o": "#2a1a2c",   # ink: outline, nose, pupil, mouth
    "O": "#6b3343",   # lit ink: the outline where the light falls (back, head, ears, tail)
    "a": "#7c2f40",   # fur, shadow (cool, toward plum)
    "b": "#b44a33",   # fur, dark
    "c": "#dc7333",   # fur, mid
    "d": "#f19b46",   # fur, light
    "e": "#fcc874",   # fur, highlight (warm, toward gold)
    "f": "#a68d9f",   # cream, shadow (cool)
    "g": "#dcc6b2",   # cream, mid
    "h": "#fdf3df",   # cream, light
    "i": "#503952",   # stockings and ear tips, dark
    "j": "#7b5c74",   # stockings and ear tips, light
    "k": "#34253f",   # the far legs' stockings (a step darker than the near ones)
    "p": "#c9707b",   # inside of the ear
    "E": "#3ad3a0",   # the eye (only the eye uses it: the check follows it)
    "W": "#f4fff2",   # the eye's glint
}
INK = "oO"
EYE = PALETTE["E"]

LAYERS = {
    "T": (5, [
        "........OO",
        ".......OhhO",
        "......OhhhhO",
        ".....OhhhhgO",
        "....OhhhhgdeO",
        "...OhhhhgddeO",
        "...OhhhgccddeO",
        "...OhhgbccccdeO",
        "....OgccbcccddeO",
        "....obbcccbcccdeO",
        ".....oabcccbcccddO",
        ".....oabbccccbcccdO",
        "......oabbccccbcccc",
        ".......oaabbcccccc",
        "........oaaabbccc",
        ".........ooaabbb",
        "...........oooo",
    ]),
    "B": (13, [
        "..................................OOOO",
        "..............................OOOOeeeeo",
        "..................OOOO.....OOOeeeeddddo",
        ".................OeeeeOOOOOeeedddccccco",
        "................Oedddddddddddddccccccco",
        "...............Oeddddccccccdddcccccccco",
        "..............Odddcccccccccccccccccccbo",
        "..............ocdcccccccccccccccccccbbo",
        "..............occccccbbbaaaabcccccccbbo",
        "...............obccccbbbooooabccccccbbo",
        "...............obbbbbbao....oabbbbbbbo",
        "................oaaaaao......oaaaaaaao",
        ".................ooooo........ooooooo",
    ]),
    "K": (12, [
        "................................Oddd",
        "...............................Oedddc",
        "..............................Oedddcghhho",
        "..............................edddccghhhho",
        "..............................dccccccghhho",
        "...............................ccccghhhho",
        "................................cccghhho",
        ".................................ccghhgo",
        ".................................ccghgo",
        ".................................bbggfo",
        ".................................abffo",
        "..................................afo",
        "...................................oo",
    ]),
    "H": (7, [
        "..................................OeeeeeeeeeeO",
        ".................................OedddddddddddO",
        ".................................OddddddoooddddOO",
        ".................................OccccccEWodddddoo",
        ".................................occcccbghhhhhhoo",
        ".................................occccbghhhhgooo",
        "..................................occbghhhgggo",
        "...................................obghhhoooo",
    ]),
    "F": (2, [
        "...................................oo",
        "..................................oiio",
        "..................................oaao",
        ".................................obaa",
        ".................................obba",
    ]),
    "N": (0, [
        "........................................oo",
        ".......................................Ojio",
        ".......................................Ojio",
        "......................................Odcpo",
        "......................................Odcpco",
        ".....................................Oedphco",
        ".....................................Oedhhcco",
    ]),
}

# The legs, drawn by hand: eight poses each for the hind and the front legs, one walk stride (see animate.py), the
# standing pose being pose 2. Each pose is rows from LEG_TOP down; column 0 is the leg's hip column minus 6. The
# top row runs on up under the body (the thigh), so a body that rises never shows a gap. '1' '2' are the fur's light
# and dark, '3' '4' the stocking's, 'o' ink; LEG_TONES maps them for the near and the (a tone darker) far legs.
LEG_TOP = 25
THIGH_TOP = 23
LEG_TONES = {"near": {"1": "c", "2": "b", "3": "j", "4": "i"}, "far": {"1": "b", "2": "a", "3": "i", "4": "k"}}
STAND = 2
LEG_POSES = {
    "hind": [
        [".....o1122o",          # 0 the paw meets the ground, reaching forward
         "......o1122o",
         "......o122o",
         ".......o12o",
         ".......o34o",
         "........o34o",
         "........o34o",
         ".........o34o",
         ".........o344o",
         ".........ooooo"],
        [".....o1122o",          # 1
         ".....o1122o",
         "......o122o",
         "......o12o",
         ".....o34o",
         "......o34o",
         "......o34o",
         ".......o34o",
         ".......o344o",
         ".......ooooo"],
        [".....o1122o",          # 2 under the hip: standing
         ".....o122o",
         "....o122o",
         "....o12o",
         "....o34o",
         ".....o34o",
         ".....o34o",
         ".....o34o",
         ".....o344o",
         ".....ooooo"],
        [".....o1122o",          # 3
         ".....o122o",
         "....o122o",
         "...o12o",
         "..o34o",
         "..o34o",
         "...o34o",
         "...o34o",
         "...o344o",
         "...ooooo"],
        [".....o1122o",          # 4 pushing off, on its toes
         "....o1122o",
         "...o122o",
         "..o12o",
         ".o34o",
         "o34o",
         "o34o",
         ".o34o",
         ".o34o",
         ".oooo"],
        [".....o1122o",          # 5 lifted behind, the hock bent
         "....o1122o",
         "...o122o",
         "..o12o",
         "..o34o",
         "...o34o",
         "...o344o",
         "....oooo"],
        [".....o1122o",          # 6 passing under, folded
         ".....o122o",
         "....o122o",
         "....o34o",
         ".....o34o",
         ".....o344o",
         "......oooo"],
        [".....o1122o",          # 7 reaching forward
         "......o1122o",
         "......o122o",
         ".......o12o",
         ".......o34o",
         "........o34o",
         "........o34o",
         "........o344o",
         "........ooooo"],
    ],
    "front": [
        ["....o1122o",           # 0 the paw meets the ground, reaching forward
         ".....o1122o",
         "......o122o",
         "......o12o",
         ".......o34o",
         ".......o34o",
         "........o34o",
         "........o34o",
         ".........o344o",
         ".........ooooo"],
        ["....o1122o",           # 1
         ".....o122o",
         ".....o122o",
         "......o12o",
         "......o34o",
         "......o34o",
         "......o34o",
         ".......o34o",
         ".......o344o",
         ".......ooooo"],
        ["....o1122o",           # 2 under the shoulder: standing
         ".....o122o",
         ".....o12o",
         ".....o12o",
         ".....o34o",
         ".....o34o",
         ".....o34o",
         ".....o34o",
         ".....o344o",
         ".....ooooo"],
        ["....o1122o",           # 3
         "....o122o",
         "....o12o",
         "....o12o",
         "...o34o",
         "...o34o",
         "...o34o",
         "...o34o",
         "...o344o",
         "...ooooo"],
        ["....o1122o",           # 4 pushing off, on its toes
         "....o122o",
         "...o12o",
         "...o12o",
         "..o34o",
         "..o34o",
         ".o34o",
         ".o34o",
         ".o34o",
         ".oooo"],
        ["....o1122o",           # 5 lifted, the wrist bent back
         "....o122o",
         "....o12o",
         "....o34o",
         "....o34o",
         "...o34o",
         "..o34o",
         "..oooo"],
        ["....o1122o",           # 6 passing under, folded
         ".....o122o",
         ".....o122o",
         "......o34o",
         "......o34o",
         ".....o34o",
         ".....oooo"],
        ["....o1122o",           # 7 reaching forward
         ".....o1122o",
         "......o122o",
         "......o12o",
         ".......o34o",
         ".......o34o",
         "........o34o",
         "........o344o",
         "........ooooo"],
    ],
}
HIPS = {"1": 24, "2": 38, "3": 18, "4": 32}            # far hind, far front, near hind, near front
LEG_KIND = {"1": "hind", "3": "hind", "2": "front", "4": "front"}
LEG_DEPTH = {"1": "far", "2": "far", "3": "near", "4": "near"}


def leg_pixels(part, pose, dy=0):
    """{(x, y): char} for one leg in one of its poses; dy moves the hidden thigh (a body that rises shows more)."""
    rows = LEG_POSES[LEG_KIND[part]][pose]
    tones = LEG_TONES[LEG_DEPTH[part]]
    x0 = HIPS[part] - 6
    out = {}
    for r, row in enumerate(rows):
        for k, ch in enumerate(row):
            if ch != ".":
                out[(x0 + k, LEG_TOP + r)] = tones.get(ch, ch)
    for y in range(THIGH_TOP + dy, LEG_TOP):           # the thigh, under the body
        for k, ch in enumerate(rows[0]):
            if ch != ".":
                out[(x0 + k, y)] = tones.get(ch, ch)
    return out


def stand_legs():
    return {p: leg_pixels(p, STAND) for p in HIPS}


def layer_pixels(part, dx=0, dy=0):
    y0, rows = LAYERS[part]
    return {(x + dx, y0 + r + dy): ch for r, row in enumerate(rows) for x, ch in enumerate(row) if ch != "."}


BODY_ORDER = ["T", "B", "F", "K", "H", "N"]     # back to front; the legs go in under the fur (see compose)


def compose(body, legs_far, legs_near):
    """One frame from placed pixels. body: list of {(x, y): ch} back to front. The legs sit under the body's fur
    but over its outline, so a leg runs into the body with no line across it; near legs cover far ones."""
    canvas, owner = {}, {}
    for px in body:
        for k, ch in px.items():
            canvas[k] = ch
            owner[k] = "body"
    for depth, legs in (("far", legs_far), ("near", legs_near)):
        for px in legs:
            for k, ch in px.items():
                if owner.get(k) == "body" and canvas[k] not in INK:
                    continue
                if depth == "far" and owner.get(k) == "near":
                    continue
                canvas[k] = ch
                owner[k] = depth
    frame = [["."] * W for _ in range(H)]
    for (x, y), ch in canvas.items():
        if 0 <= x < W and 0 <= y < H:
            frame[y][x] = ch
    for y in range(H):                                   # the outline last: an edge a pose opened gets ink
        for x in range(W):
            ch = frame[y][x]
            if ch == "." or ch in INK:
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if not (0 <= nx < W and 0 <= ny < H) or frame[ny][nx] == ".":
                    frame[y][x] = "o"
                    break
    return ["".join(r) for r in frame]


def rest():
    legs = stand_legs()
    return compose([layer_pixels(p) for p in BODY_ORDER], [legs["1"], legs["2"]], [legs["3"], legs["4"]])


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
    print(f"wrote {KEY}_art_8x.png ({len(PALETTE)} colours)")
