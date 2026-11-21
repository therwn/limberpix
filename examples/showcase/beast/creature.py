"""The beast: an original young wolf of no real breed, drawn pixel by pixel and kept as data.

Slate-blue fur over the back and the haunch, ash on the legs, a thick pale ruff from the cheeks down the throat to
the chest, long legs with big paws, a bushy tail that curves off the croup with a pale tip, an amber eye. A young
animal: the head and the paws a little big for the body. Side view, facing right, light from the top left.

The colours: one fur ramp of ten tones, a..j, from an indigo shadow through slate blue (d, e, f) and a cool grey (g)
to a neutral (h), a warm pale (i) and cream (j), so the slate, the ash and the ruff are one material lit
differently: shadows cool, lights warm. Ink (o) outlines the shadow side; top and left edges keep a lit line of the
ramp (c, d, e) instead. The far legs sit two to three tones darker (FAR_TONE). 21 colours in all.

The value plan at 1x: the ruff, the cheek and the top planes of the head, the croup and the back are the lightest
masses; the flank and the legs sit in the middle; the far legs, the belly's core shadow (with a step of bounce light
under it) and the underside of the tail are the darks. Fur is drawn as a few long locks along the flow, each lit on
its upper left with a dark under-edge, and the outline breaks into tufts at the throat, the nape, the belly and the
tail.

One character is one pixel; '.' is empty. Every part that moves is its own layer, drawn whole, also where a part in
front of it covers it, so a part that moves never opens a hole. A layer is (x0, y0, rows): its first column and row
on the canvas. Back to front (ORDER):
  far legs (1 hind, 2 front), T tail, B torso, near foreleg (4), K neck and ruff, near hind leg (3, its thigh over
  the haunch), F far ear, M mouth (its dark inside, the gums and the upper fang), G tongue, J lower jaw (with the
  gums and the lower fang along its top), H head (skull, muzzle, nose, eye, the cheek ruff, the upper lip and the
  lip line), N near ear.
The mouth, the tongue and the jaw's top rows lie hidden under the head at rest; they show only when the jaw opens.

Each leg is cut where it bends, at an overlap or a change of form: the hind leg at the hock (the thigh and the
gaskin above; the metatarsus and the paw below), the foreleg at the elbow (the upper arm, mostly under the ruff) and
at the wrist (the forearm; then the pastern, angled forward, and the paw with two toe splits). The tones run on
across every cut, so a cut never shows at rest. The far legs are the near drawings moved and darker.

The three loops (animate.py describes each in full; PIVOTS holds every joint, in canvas pixels):
  idle    three breaths: the torso, one piece, rises a pixel whole and falls; the head rides each on the neck as
          a chain (the neck and the back of the head, then the muzzle, then the ears, a pose apart); the tail
          swings as a chain cut across its length (root, middle, the pale tip), each link a pose behind the one
          before; each ear flicks once, the jaw parts once to scent, the eye glances back.
  move    a lateral-sequence walk: the upper legs turn at the hips and the shoulders, the lower legs at the hocks
          and the elbows, and a lifted forepaw folds back at the wrist; a planted paw slides back with the ground;
          the torso rises a pixel whole twice a stride, the head nods on the neck as a chain after it, the tail last.
  attack  a lunge and a bite, timed 5:1:7 (anticipation : strike : recovery): the wolf sinks back onto its hind
          legs (the thighs turn at the hips, the hocks fold lower, the forelegs lean back), the head drops and the
          jaw stays shut; then a fast lunge, the forelegs reaching and the body stretched on one line from the hind
          paws to the nose, the jaw open about its hinge (behind and below the eye) to bare the fangs and the
          tongue, the tail's root whipping up while its tip trails; the bite held as a moving hold (the jaw shuts,
          the torso sinks a pixel whole, the head follows a pose later); then back to stand, ending on the rest pose.

    python creature.py           # writes beast_art_8x.png next to this file: the drawing at rest, 8x
"""
import os

KEY = "beast"
W, H = 96, 54            # the canvas of the drawing and of every frame (room in front for the lunge)
GROUND = 52              # the ink row the paws stand on

PALETTE = {
    "o": "#120f19",   # ink: the shadow-side outline, the nose, the pupil, the lip line
    "a": "#191a2e",   # fur, deepest shadow (indigo)
    "b": "#242844",   # fur, core shadow
    "c": "#323a5c",   # slate, dark; the lit line on dark edges
    "d": "#404e78",   # slate, dark mid; the lit line on slate edges
    "e": "#566594",   # slate, mid
    "f": "#7480aa",   # slate, light
    "g": "#9c9eb2",   # ash, cool grey: the lit top of the slate, the ruff's shade
    "h": "#bbb7ba",   # ash, neutral
    "i": "#d8cfc6",   # ash, warm pale: the ruff and the cheek
    "j": "#f0e6d4",   # cream: the ruff's and the croup's lights
    "k": "#f6edd9",   # the fangs
    "w": "#5e6488",   # the light on the nose
    "p": "#4a3047",   # inside of the ear, dark
    "q": "#8b5d6c",   # inside of the ear, light
    "m": "#34111f",   # the mouth's inside
    "n": "#7a2838",   # gums
    "t": "#b84c61",   # tongue
    "u": "#e08a90",   # tongue, lit
    "E": "#f2aa3c",   # the eye, amber (only the eye uses it: the check follows it)
    "Y": "#b3631f",   # the eye's lower half, in the lid's shadow
}
INK = "o"
EYE = PALETTE["E"]

LAYERS = {
    "T": (4, 20, [
        "..........ddddddc.d",
        "........ddgghggfcdc",
        "......ddghggfcdgcdb",
        ".....dgghgffcdgbcbb",
        "....dghggffeodgbcc",
        "...dgggfgfeo.d",
        "...dgfgffeeo",
        "..dgggffedo",
        "..dgfffedco",
        ".dgfffeedco",
        ".dgfefeddco",
        ".dfeefddco",
        ".dfedefdcbo",
        "defeddedcbo",
        ".defeddccbo",
        ".deefeccbbo",
        ".degeedcco",
        ".dfgfedccbo",
        "..dggfedcco",
        ".dghgeedcco",
        "..dhhgfedco",
        "..dhihgedco",
        "...eiihgedco",
        "....eiihgfdo",
        ".....eihgeo",
        "......ehgo",
        ".......oo",
    ]),
    "B": (18, 20, [
        ".....dddddd.................hgggggf",
        "....ghhihhggdddddd......ddfghhhhhgfgf",
        "..hggggggffgggggggddddddgffghhhhhgggfe",
        ".hhggggggfggfeggggggfgggggffeegghgggffe",
        ".hhggggggffggeefffffefffffeeedefggggffee",
        "hhggggggfffgggeeffeefdeeeeeeddcfggfffdee",
        "fggffgdddddddddeeeefdeedeeddddcfceeefddee",
        "fcccbbbdddbdbbddeefdeeddddddddcfddeeeeebb",
        "cccbbbbbbbbbbbbddfdedddcdddcdccfddddddbbb",
        ".ccbbbbbbbbbbbbceddddcdddccccccfdddddbbbb",
        ".cccccccccccccccbccdccccccccbccfcccdbbbcb",
        "...ccccccccccccccbbbcccccbbbbccfbcbbbbbcc",
        "................ocbbbbbcbbbbbbcfbbbbbbcc",
        ".................ooccbbbbbabbbcabbbbbccf",
        "...................coccbccbccccaccccccgf",
        "...................oooocdcddcdccccccc",
        ".......................oodcooo.c",
        ".........................co",
        ".........................o",
    ]),
    "K": (45, 10, [
        "............o",
        "...........dfge",
        ".........ddfgffji",
        ".......ddeffffjjii",
        "......defefeejjjiii",
        "....deefeeedejjjiiii",
        ".....defededehjiiiiii",
        "...ddeffeddhiiiiiiihh",
        "..ddeefedehhiiiiiiiiii",
        ".dfefeedehihiiijjiiihi",
        "dfeeffedhiijiihjjiiihh",
        "gfeefeedgijjiihijiffgfo",
        "gfeeefeddhiijihhgihgghgo",
        "...feedehhiiihghijihghhgo",
        ".....edhhihhhghiiihghgoo",
        "......ghihghihhhghihgo",
        ".......hhghihghihghhhgo",
        "........gghhgghhgghggfo",
        ".........hgghgghggfo",
        "..........ghgggghgggo",
        "...........ghgfgghgfo",
        "...........ggfggggfo",
        "............ggfgfo",
        ".............gfeo",
        ".............ooo",
    ]),
    "F": (58, 5, [
        "...o",
        "..oc",
        ".occb",
        ".odcf",
        "odcbbc",
        "edbbbb",
        ".bbbbb",
    ]),
    "M": (64, 18, [
        ".nnnnnnnn",
        "mmmmmmmkm",
        ".mmmmmmm",
    ]),
    "G": (65, 19, [
        "tuuut",
        "tttttt",
    ]),
    "J": (63, 18, [
        ".nnnnnnknn",
        "gghgefggfeo",
        "....oooooo",
    ]),
    "H": (58, 9, [
        "....hhf",
        "..cfihfff",
        ".hggihggfe.o",
        "gffghfeefgggddo",
        "effeeedcccfggggdd",
        "feedefdcEEoffggggwoo",
        "edehhghhYohfeeeffooo",
        "hiiijiihhihghhhggoo",
        "ijjiijiihhgghhggo",
        ".ihiihhggfoooooo",
        "jiihhghgf",
        "..ihgggfe",
        "...hg",
        "...i",
    ]),
    "N": (62, 4, [
        "..do",
        ".dgqo",
        "bfgqo",
        ".fhpqo",
        ".ghpqo",
        "fghppqo",
        "ghhppqho",
        "hhgfefg",
        "g",
    ]),
}

# The legs: one drawing each, near side, standing: the hind leg above and below the hock, the foreleg above the
# elbow, from the elbow to the wrist, and the pastern with the paw.
LEG_DRAWINGS = {
    "hind_u": (17, 22, [
        "....hhihhhgg",
        "...hghhghgggf",
        "..ghgggggfgfff",
        ".fgggfgffffffed",
        "dfgffffgffffede",
        "dffgffffffedeecd",
        "dffffeffffedfedc",
        "defffdffedfeeddc",
        "defedfeedfeedddcc",
        "deedfeedfeedddccc",
        "dededddfeedddcccc",
        "cdeeedeeeddcdccco",
        "cddededdddcdccco",
        ".cdedddeddcccco",
        ".defeddddcdco",
        "..dfeedddcco",
        "...dfeeddco",
        "....dfeddo",
        "....dfeddo",
        "...dffedo",
        "..dfeeddo",
        "...feedco",
        "...feecc",
    ]),
    "hind_l": (18, 43, [
        "oeeddd",
        ".oeddco",
        ".oeddco",
        "..oeddco",
        "..oeddco",
        "...oeddco",
        "...oeddfggfo",
        "...oedecfcfeo",
        "....oddcecedo",
        "....ooooooooo",
    ]),
    "front_u": (48, 23, [
        "....eeh",
        "...eehhhh",
        "..eehhhhg",
        "..ehhhhggg",
        "..eghhgggg",
        "..fegggggf",
        "..fedgggff",
        "..fedggfff",
        "..feddggg",
        "..feddfgf",
        ".feedcfgf",
        ".ffeeddc",
        ".ffeedccoo",
        "oefeedcco",
        "..eeedc",
        "....e",
    ]),
    "front_l": (49, 36, [
        ".ffeed",
        ".effedo",
        ".effedo",
        ".egfedo",
        ".egfedo",
        ".egfedo",
        ".effedo",
        ".effedo",
        ".effedo",
        "oeffed",
        "...fed",
    ]),
    "front_p": (50, 45, [
        "..fedo",
        "oefedco",
        ".oeffdco",
        ".oeefgggo",
        ".odecfcgfo",
        ".odecfcfeo",
        ".ocdcecedo",
        ".ooooooooo",
    ]),
}
LEG_AT = {"3": ("hind", 0), "1": ("hind", 6), "4": ("front", 0), "2": ("front", -4)}   # leg: drawing, x offset
FAR_LEGS = "12"
FAR_TONE = {"j": "d", "i": "d", "h": "d", "g": "d", "f": "c", "e": "c", "d": "b", "c": "a", "b": "a"}

ORDER = ["1u", "1l", "2u", "2l", "2p", "T", "B", "4u", "4l", "4p", "K", "3u", "3l", "F", "M", "G", "J", "H", "N"]

PIVOTS = {
    "tail_root": (20, 22), "neck_base": (48, 23), "head": (59, 15), "jaw_hinge": (64, 18), "tongue": (65, 19),
    "ear_near": (65, 11), "ear_far": (60, 11),
    "hip_near": (24, 25), "hip_far": (30, 25), "stifle_near": (32, 33), "stifle_far": (38, 33),
    "hock_near": (20, 43), "hock_far": (26, 43),
    "shoulder_near": (52, 26), "shoulder_far": (48, 26), "elbow_near": (51, 36), "elbow_far": (47, 36),
    "wrist_near": (52, 45), "wrist_far": (48, 45),
}
SEGMENTS = {"u": "_u", "l": "_l", "p": "_p"}


def leg_layer(key):
    """(x0, y0, rows) of a leg segment: "3u" is the near hind's upper leg, "2p" the far forepaw."""
    kind, dx = LEG_AT[key[0]]
    x0, y0, rows = LEG_DRAWINGS[kind + SEGMENTS[key[1]]]
    if key[0] in FAR_LEGS:
        rows = ["".join(FAR_TONE.get(ch, ch) for ch in r) for r in rows]
    return x0 + dx, y0, rows


def layer(key):
    return leg_layer(key) if key[0] in LEG_AT else LAYERS[key]


def layer_pixels(key, dx=0, dy=0):
    x0, y0, rows = layer(key)
    return {(x0 + c + dx, y0 + r + dy): ch for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != "."}


def compose(placed):
    """One frame from placed layers, back to front: a list of (key, {(x, y): char}). Two rules follow:
    a far leg's pixel beside a near leg's fill turns to ink, so the legs read apart; and a pixel on the silhouette
    that is not on its own layer's edge (a fill that a pose has uncovered) turns to ink."""
    frame = [["."] * W for _ in range(H)]
    owner = [[None] * W for _ in range(H)]
    for i, (key, px) in enumerate(placed):
        for (x, y), ch in px.items():
            if 0 <= x < W and 0 <= y < H:
                frame[y][x] = ch
                owner[y][x] = i
    near_leg = {i for i, (k, _) in enumerate(placed) if k[0] in "34"}
    far_leg = {i for i, (k, _) in enumerate(placed) if k[0] in FAR_LEGS}
    out = [r[:] for r in frame]
    for y in range(H):
        for x in range(W):
            i = owner[y][x]
            if i is None or frame[y][x] == "o":
                continue
            px = placed[i][1]
            sil = edge = False
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                inside = 0 <= nx < W and 0 <= ny < H
                if not inside or frame[ny][nx] == ".":
                    sil = True
                if (nx, ny) not in px:
                    edge = True
                if i in far_leg and inside and owner[ny][nx] in near_leg and frame[ny][nx] != "o":
                    out[y][x] = "o"
            if sil and not edge:
                out[y][x] = "o"
    return ["".join(r) for r in out]


def rest():
    return compose([(k, layer_pixels(k)) for k in ORDER])


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
    used = sorted({ch for row in ART for ch in row} - {"."})
    print(f"wrote {KEY}_art_8x.png ({len(PALETTE)} colours in the palette, {len(used)} at rest)")
