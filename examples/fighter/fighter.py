"""An original fighter, side view facing right, drawn at game size from a skeleton, and its idle fighting stance
built the Pixelblog 52 way (Slynyrd): one bounce of 8 poses, the whole body moving on every pose, the limbs further
from the body moving more, the head lagging at the turns, slow over the rise and the top, quick on the drop.

    python fighter.py OUT_DIR

The drawing is the rest pose of the skeleton below. Every pose is drawn by the same function from its joints, so the
look never changes between poses: only where the joints are. Light comes from the upper left: each limb is a capsule
shaded by which way its surface faces, the near limbs a step lighter than the far ones, an ink line round the
figure (the lit side a lighter ink) and where a near part crosses a farther one. The light comes from above and a
little ahead of the fighter, so the face it turns to the fight is lit and its back falls into shade.

Writes fighter_art_8x.png (the drawing), fighter_art.png (the drawing at game size: the check's --palette and
--ref), fighter_idle.png (the strip, 20 frames at 30 fps), fighter_idle_parts.png (each part one flat colour, for
pixel-anim-check --parts) and fighter_idle_4x.gif (the loop at its own timing). The idle checks clean (0 faults,
0 warnings), its lit-side ink declared with the dark one:

    python -I skills/pixel-anim-check/pixel_anim_check.py --loop idle=OUT_DIR/fighter_idle.png --frame 48
        --eye "#3a1a14" --ink "#1b1420,#4a3346" --parts idle=OUT_DIR/fighter_idle_parts.png
        --palette OUT_DIR/fighter_art.png --ref OUT_DIR/fighter_art.png --out out --name fighter
"""
import math
import os
import sys

from PIL import Image

W, H = 48, 64
GROUND = 62                                    # the soles' row

PAL = {
    "ink": "#1b1420", "lit": "#4a3346",
    "skin": ("#f4cfa2", "#dc9f70", "#ad6c4c", "#743f33"),
    "hair": ("#6a5288", "#463457", "#2c2038", "#1e1626"),
    "top": ("#7fd2bc", "#46a08f", "#2d716b", "#1f4b4f"),
    "pants": ("#6b7a9c", "#4a5675", "#333c58", "#222842"),
    "wrap": ("#f6ead0", "#d8c59c", "#ab9470", "#7a6a50"),
    "band": ("#f2665a", "#c8403a", "#8e2a30", "#5e1c26"),
    "shoe": ("#6a5462", "#4a3a48", "#33283a", "#221a28"),
    "eye": "#3a1a14", "white": "#f6f2e8",
}
LIGHT = (0.45, -0.89)                          # towards the light: up and a little ahead, so the face is lit

# The skeleton at rest (x right, y down): a fighting stance, the lead (near, left) leg forward, the lead fist out
# at chin height, the rear fist guarding the jaw.
REST = {
    "head": (31, 12), "neck": (29, 19),
    "chest": (28, 24), "waist": (26, 32), "hip": (25, 37),
    "n_shoulder": (30, 23), "n_elbow": (36, 30), "n_fist": (41, 22),
    "f_shoulder": (25, 23), "f_elbow": (30, 31), "f_fist": (37, 24),
    "n_hip": (27, 38), "n_ankle": (36, 58), "f_hip": (23, 38), "f_ankle": (15, 58),
}
THIGH, SHIN = 13.0, 12.5                       # the leg's bone lengths: longer than the hip-ankle reach at the top
                                               # of the bounce, so the knees stay bent and never pop straight


def knee(hip, ankle, forward):
    """Two-bone IK: the knee bent towards `forward` (+1 the face's side, -1 behind)."""
    hx, hy = hip
    ax, ay = ankle
    d = min(math.hypot(ax - hx, ay - hy), THIGH + SHIN - 0.01)
    a = (THIGH ** 2 - SHIN ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(max(0.0, THIGH ** 2 - a ** 2))
    ux, uy = (ax - hx) / d, (ay - hy) / d
    mx, my = hx + a * ux, hy + a * uy
    px, py = -uy, ux                              # the side the knee goes: forward for both legs in a crouch
    if px * forward < 0:
        px, py = -px, -py
    return (mx + h * px, my + h * py)


def capsule(a, b, r0, r1=None):
    """{(x, y): (nx, ny)} the pixels within the capsule a-b (radius r0 at a, r1 at b), each with its surface normal
    (from the bone to the pixel, unit length at the surface)."""
    r1 = r0 if r1 is None else r1
    ax, ay = a
    bx, by = b
    out = {}
    L2 = (bx - ax) ** 2 + (by - ay) ** 2 or 1e-9
    for y in range(int(min(ay, by) - max(r0, r1)) - 1, int(max(ay, by) + max(r0, r1)) + 2):
        for x in range(int(min(ax, bx) - max(r0, r1)) - 1, int(max(ax, bx) + max(r0, r1)) + 2):
            t = max(0.0, min(1.0, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2))
            cx, cy = ax + t * (bx - ax), ay + t * (by - ay)
            r = r0 + (r1 - r0) * t
            dx, dy = x - cx, y - cy
            dd = math.hypot(dx, dy)
            if dd <= r:
                out[(x, y)] = (dx / r, dy / r) if dd else (0.0, 0.0)
    return out


def shade(n, ramp, near=True):
    """The ramp's tone for a surface normal: lit, mid, shade or deep, a step darker on a far limb."""
    lam = n[0] * LIGHT[0] + n[1] * LIGHT[1]
    i = 0 if lam > 0.45 else 1 if lam > -0.15 else 2 if lam > -0.55 else 3
    return ramp[min(3, i + (0 if near else 1))]


def body_parts(j):
    """[(part, {(x, y): colour})] back to front for joints j."""
    sk, hr, tp, pa, wr, bd, sh = (PAL[k] for k in ("skin", "hair", "top", "pants", "wrap", "band", "shoe"))
    parts = []

    def limb(name, segs, near):
        px = {}
        for a, b, r0, r1, ramp in segs:
            for q, n in capsule(a, b, r0, r1).items():
                px[q] = shade(n, ramp, near)
        parts.append((name, px))

    nk = knee(j["n_hip"], j["n_ankle"], +1)
    fk = knee(j["f_hip"], j["f_ankle"], +1)
    # the far leg: thigh and shin in the trousers, the shoe on the ground pointing forward
    fa = j["f_ankle"]
    limb("far_leg", [(j["f_hip"], fk, 3.6, 3.0, pa), (fk, fa, 3.0, 2.4, pa),
                     ((fa[0] - 2, fa[1] + 2), (fa[0] + 4, fa[1] + 2.4), 1.8, 1.6, sh)], False)
    # the far arm: behind the body, its fist in front of the jaw
    limb("far_arm", [(j["f_shoulder"], j["f_elbow"], 2.6, 2.2, tp), (j["f_elbow"], j["f_fist"], 2.0, 2.0, sk),
                     (j["f_fist"], j["f_fist"], 2.7, 2.7, wr)], False)
    # the headband's two tails, flying back off the back of the head (free tips: they trail the head)
    hx, hy = j["head"]
    tails = {}
    for (tx, ty), w in (((j["tail1"][0], j["tail1"][1]), 1.3), ((j["tail2"][0], j["tail2"][1]), 1.0)):
        for q, n in capsule((hx - 5, hy - 2), (tx, ty), 1.4, w).items():
            tails[q] = shade(n, bd[:3] + (bd[2],), True)   # no deeper tone than the drawing's tails show
    parts.append(("band_tails", tails))
    # the torso: a tapering capsule chest to hip, the top over it; a belt at the waist
    torso = {}
    for q, n in capsule(j["waist"], j["hip"], 4.6, 4.8).items():
        torso[q] = shade(n, pa)
    for q, n in capsule(j["chest"], j["waist"], 6.4, 4.8).items():
        if q[1] <= j["waist"][1] or q not in torso:      # the top down to the waist, over the trousers' top
            torso[q] = shade(n, tp)
    bx, by = j["waist"]
    for q in list(torso):
        if abs(q[1] - (by + (q[0] - bx) * -0.15)) <= 1.0:      # the belt where the top ends
            torso[q] = wr[1] if q[1] - by < 0 else wr[2]
    parts.append(("torso", torso))
    # the near leg: thigh, shin, shoe, a step lighter
    na = j["n_ankle"]
    limb("near_leg", [(j["n_hip"], nk, 3.8, 3.2, pa), (nk, na, 3.2, 2.5, pa),
                      ((na[0] - 2, na[1] + 2), (na[0] + 5, na[1] + 2.4), 1.9, 1.6, sh)], True)
    # the head: skin, the hair over its back and top in spikes, the headband round the brow, the eye at the front
    head = {}
    def face(n):                                           # the face turned to the light: lit, a shade only
        return sk[0] if n[0] > 0.2 and n[1] < 0.5 else sk[1] if n[1] < 0.75 else sk[2]   # under the jaw
    for q, n in capsule((hx, hy), (hx, hy), 6.8).items():
        head[q] = face(n)
    for q, n in capsule((hx + 3, hy + 3), (hx + 3, hy + 3), 2.8).items():   # the jaw, forward and down
        head.setdefault(q, face(n))
    for q, n in capsule((hx - 1.5, hy - 2.5), (hx - 1.5, hy - 2.5), 7.0).items():
        if q[1] <= hy - 2 or q[0] <= hx - 3:               # the hair: top and back
            head[q] = shade(n, hr)
    for sx, sy in ((-6, -7), (-2, -9), (2, -8), (-8, -3)):  # spikes
        for q, n in capsule((hx - 1, hy - 4), (hx + sx, hy + sy), 2.2, 0.6).items():
            head[q] = shade(n, hr)
    for q in list(head):                                    # the headband across the brow
        if abs(q[1] - (hy - 2)) <= 0.6 and q[0] >= hx - 5:
            head[q] = bd[1] if q[0] < hx + 4 else bd[0]
    for q in ((hx - 1, hy + 1), (hx - 1, hy + 2), (hx, hy + 2)):   # the ear
        head[q] = sk[2]
    head[(hx + 4, hy)] = PAL["eye"]                         # the eye, looking ahead, a white behind it
    head[(hx + 3, hy)] = PAL["white"]
    head[(hx + 3, hy - 1)] = hr[2]                          # the brow, set
    head[(hx + 4, hy - 1)] = hr[2]
    head[(hx + 5, hy + 4)] = sk[3]                          # the mouth, shut
    head[(hx + 6, hy + 4)] = sk[2]
    parts.append(("head", head))
    # the near arm: upper arm in the sleeve, forearm, the wrapped fist out front
    limb("near_arm", [(j["n_shoulder"], j["n_elbow"], 2.8, 2.4, tp), (j["n_elbow"], j["n_fist"], 2.2, 2.1, sk),
                      (j["n_fist"], j["n_fist"], 2.9, 2.9, wr)], True)
    return parts


ORDER = ["far_leg", "far_arm", "band_tails", "torso", "near_leg", "head", "near_arm"]
PART_RGB = {"far_leg": "#208040", "far_arm": "#909020", "band_tails": "#e0a040", "torso": "#c8c8c8",
            "near_leg": "#50d060", "head": "#e05050", "near_arm": "#e0e050"}


def render(j):
    """{(x, y): (colour, part)}: the parts back to front, then the ink: round the figure (the lit ink where the air
    is above or to the left) and where a nearer part meets a farther one (so the near limbs read across the body)."""
    canvas = {}
    rank = {}
    for name, px in body_parts(j):
        for q, c in px.items():
            if 0 <= q[0] < W and 0 <= q[1] < H:
                canvas[q] = (c, name)
                rank[q] = ORDER.index(name)
    out = dict(canvas)
    for (x, y), (c, name) in canvas.items():
        nb = [(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)]
        air = [q for q in nb if q not in canvas]
        if air:
            lit = all(q in ((x, y - 1), (x - 1, y)) for q in air) and name not in ("far_leg", "far_arm")
            out[(x, y)] = (PAL["lit"] if lit else PAL["ink"], name)
        elif name in ("near_arm", "near_leg", "head") and any(rank[q] < rank[(x, y)] and canvas[q][1] != name
                                                               and canvas[q][1] not in ("head",) for q in nb):
            if name != "head" or any(canvas[q][1] == "torso" for q in nb):
                out[(x, y)] = (PAL["ink"], name)
    return out


# ---- the idle: Pixelblog 52, the male idle's per-part offsets (up negative), held 3 frames over the rise and the
# top and 2 on the drop (100 ms and about 67 ms at 30 fps: a 50 ms frame cannot be shown at 30 fps)
TORSO = [0, -1, -2, -1, 0, 1, 2, 1]            # the torso (and the hips): 2 px up, 2 px down
HEAD = [0, -1, -2, -2, -1, 0, 1, 1]            # the head: with the torso, but holding at the turns (it lags)
ARM = [0, -2, -3, -2, 0, 1, 3, 2]              # the shoulders' load on the elbows: 2 px a step
N_FIST = [0, -2, -3, -2, 0, 2, 4, 3]           # the lead fist
F_FIST = [0, -4, -5, -3, 0, 2, 4, 3]           # the rear fist: the furthest out, the most
HOLDS = [3, 3, 3, 3, 2, 2, 2, 2]


def pose(P):
    """The joints of pose P (0-7): the feet planted, the knees taking the bounce."""
    j = dict(REST)
    t, h, a, nf, ff = TORSO[P], HEAD[P], ARM[P], N_FIST[P], F_FIST[P]
    for k in ("chest", "waist", "hip", "neck", "n_hip", "f_hip", "n_shoulder", "f_shoulder"):
        j[k] = (REST[k][0], REST[k][1] + t)
    j["head"] = (REST["head"][0], REST["head"][1] + h)
    j["n_elbow"] = (REST["n_elbow"][0], REST["n_elbow"][1] + a)
    j["f_elbow"] = (REST["f_elbow"][0], REST["f_elbow"][1] + a)
    j["n_fist"] = (REST["n_fist"][0], REST["n_fist"][1] + nf)
    j["f_fist"] = (REST["f_fist"][0], REST["f_fist"][1] + ff)
    hp = HEAD[P - 1]                               # the headband's tails: a pose behind the head, swinging wider
    j["tail1"] = (REST["head"][0] - 11, REST["head"][1] + 1 + hp + (1 if hp > h else -1 if hp < h else 0))
    j["tail2"] = (REST["head"][0] - 10, REST["head"][1] + 4 + hp)
    return j


def image(fr, parts=False, Z=1):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (x, y), (c, name) in fr.items():
        v = PART_RGB[name] if parts else c
        im.putpixel((x, y), tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    return im.resize((W * Z, H * Z), Image.NEAREST) if Z > 1 else im


def main(out):
    os.makedirs(out, exist_ok=True)
    rest = pose(0)
    art = render(rest)
    image(art, Z=8).save(os.path.join(out, "fighter_art_8x.png"))
    image(art).save(os.path.join(out, "fighter_art.png"))
    frames = [render(pose(P)) for P in range(8) for _ in range(HOLDS[P])]
    for name, parts in (("fighter_idle.png", False), ("fighter_idle_parts.png", True)):
        strip = Image.new("RGBA", (W * len(frames), H), (0, 0, 0, 0))
        for k, fr in enumerate(frames):
            strip.paste(image(fr, parts), (k * W, 0))
        strip.save(os.path.join(out, name))
    gif = []
    for fr in frames:
        bg = Image.new("RGBA", (W, H), (74, 66, 84, 255))
        bg.alpha_composite(image(fr))
        gif.append(bg.convert("RGB").resize((W * 4, H * 4), Image.NEAREST))
    edges = [int(round(k * 100 / 30)) * 10 for k in range(len(gif) + 1)]
    gif[0].save(os.path.join(out, "fighter_idle_4x.gif"), save_all=True, append_images=gif[1:],
                duration=[b - a for a, b in zip(edges, edges[1:])], loop=0)
    print(f"wrote {len(frames)} frames ({W}x{H}) to {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)))
