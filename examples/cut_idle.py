"""Cut a flat sprite with body_parts, then pose its exported masks and check the resulting idle."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "skills" / skill) for skill in ("pixel-animate", "pixel-anim-check")]
import body_parts
import pixel_anim_check

SIZE = (28, 22)
INK, EYE = "#1a1216", "#ffcc33"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "out" / "cut-idle")
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    drawing, bones = out / "beacon.png", out / "beacon-marks.json"
    source = Image.new("RGBA", SIZE)
    pen = ImageDraw.Draw(source)
    pen.rounded_rectangle((5, 9, 22, 17), radius=2, fill="#5487b2", outline=INK)
    pen.rounded_rectangle((10, 3, 17, 11), radius=2, fill="#82adcb", outline=INK)
    pen.point((15, 6), fill=EYE)
    source.save(drawing)
    bones.write_text(json.dumps({
        "parts": {"body": {"bone": [[7, 13], [20, 13]]},
                  "head": {"parent": "body", "bone": [[14, 10], [14, 5]]}},
        "points": {"eye": [15, 6]},
    }, indent=2), encoding="utf-8")
    status = body_parts.main([str(drawing), str(bones), "--out", str(out)])
    if status:
        return status

    with Image.open(out / "beacon_labels.png") as image:
        labels = np.array(image)
    parts = json.loads((out / "beacon_parts.json").read_text(encoding="utf-8"))["parts"]
    with Image.open(drawing) as image:
        rgba = np.array(image)
    layers = [Image.fromarray(np.where((labels == p["label"])[..., None], rgba, 0)) for p in parts]
    width, height = SIZE
    hold = 8
    strip = Image.new("RGBA", (width * hold * 2, height))
    for key, dy in enumerate((0, -1)):
        pose = Image.new("RGBA", SIZE)
        for layer in layers:
            pose.alpha_composite(layer, (0, dy))
        for frame in range(key * hold, (key + 1) * hold):
            strip.paste(pose, (frame * width, 0))
    idle = out / "beacon_idle.png"
    strip.save(idle)
    return pixel_anim_check.main(["--loop", f"idle={idle}", "--frame", str(width), "--eye", EYE, "--flier",
                                  "--out", str(out), "--name", "beacon"])


if __name__ == "__main__":
    raise SystemExit(main())
