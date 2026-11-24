"""Exercise complete drawing result sets through the same entry points as the CLI."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from PIL import Image, ImageDraw

TOOLS = Path(__file__).resolve().parents[1] / "skills" / "pixel-animate"


def hashes(paths):
    return tuple(sha256(path.read_bytes()).hexdigest() for path in paths)


def selected(out, manifest, filenames):
    pointer = out / manifest
    if pointer.is_file():
        paths = json.loads(pointer.read_text(encoding="utf-8"))
        assert set(paths) == set(filenames), paths
        files = tuple(out / paths[name] for name in filenames)
        assert len({p.parent for p in files}) == 1, files
        return files
    return tuple(out / name for name in filenames)


def verify(root, tool, manifest, filenames, variants):
    def args(out, variant):
        return [*map(str, variants[variant]), "--out", str(out), "--name", "sample"]

    def run(out, variant):
        result = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(TOOLS / (tool + ".py")), *args(out, variant)],
                                capture_output=True, text=True, encoding="utf-8")
        return result.returncode, result.stdout + result.stderr

    live, other = root / "live", root / "other"
    expected = []
    for i, out in enumerate((live, other)):
        code, report = run(out, i)
        assert code == 0, report
        expected.append(hashes(selected(out, manifest, filenames)))
    assert all(a != b for a, b in zip(expected[0][-2:], expected[1][-2:])), tool

    originals = selected(live, manifest, filenames)
    pointer = live / manifest
    # Older executables fail on their final flat output. Once a manifest is available, it is the only publish point.
    locked = pointer if pointer.is_file() else originals[-1]
    pointer_bytes = locked.read_bytes()
    original_entries = set(live.iterdir())
    module = importlib.import_module(tool)
    replace = os.replace
    if os.name == "nt":
        with locked.open("rb"):
            code, report = run(live, 1)
    else:
        def refuse_locked(src, dst):
            if Path(dst).resolve() == locked.resolve():
                raise PermissionError(f"injected lock at {locked}")
            return replace(src, dst)

        with patch.object(os, "replace", side_effect=refuse_locked), redirect_stdout(io.StringIO()), \
                redirect_stderr(io.StringIO()) as err:
            code = module.main(args(live, 1))
            report = err.getvalue()
    assert code == 2, report
    assert hashes(originals) == expected[0], f"{tool} changed the previous set on failure: {report}"
    assert locked.read_bytes() == pointer_bytes and set(live.iterdir()) == original_entries

    attempts = 0

    def busy_once(src, dst):
        nonlocal attempts
        if Path(dst) == pointer:
            attempts += 1
            if attempts == 1:
                error = PermissionError("interrupted by a concurrent Windows rename")
                error.winerror = 5
                raise error
        return replace(src, dst)

    with patch.object(os, "replace", side_effect=busy_once), redirect_stdout(io.StringIO()), \
            redirect_stderr(io.StringIO()) as err:
        code = module.main(args(live, 1))
    assert code == 0 and attempts == 2, f"{tool} did not recover from a transient manifest lock: {err.getvalue()}"

    with originals[-1].open("rb"):
        code, report = run(live, 1)
    assert code == 0, report
    assert hashes(originals) == expected[0] and hashes(selected(live, manifest, filenames)) == expected[1]

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda i: run(live, i), range(2)))
    assert all(code == 0 for code, _ in results), results
    assert hashes(selected(live, manifest, filenames)) in expected, f"{tool} published a mixed set"
    assert hashes(originals) == expected[0], f"{tool} changed files a previous reader had resolved"


def main():
    sys.path.insert(0, str(TOOLS))
    failed = False
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        drawings = [root / f"drawing{i}.png" for i in range(2)]
        for path, color in zip(drawings, ("#d59c33", "#236da6")):
            im = Image.new("RGBA", (48, 24))
            pen = ImageDraw.Draw(im)
            pen.rectangle((4, 7, 27, 17), fill=color)
            pen.rectangle((28, 9, 41, 15), fill="#e6a036")
            im.save(path)
        parts = {"body": {"bone": [[8, 12], [24, 12]]},
                 "tail": {"parent": "body", "bone": [[28, 12], [38, 12]]}}
        marks = [root / f"marks{i}.json" for i in range(2)]
        for path, order in zip(marks, (parts, dict(reversed(list(parts.items()))))):
            path.write_text(json.dumps({"parts": order}), encoding="utf-8")
        cases = [
            ("body_parts", "sample_parts_manifest.json", ("sample_parts.png", "sample_patches.png",
             "sample_labels.png", "sample_parts.json"), [(drawings[0], m) for m in marks]),
            ("creature_map", "sample_map_manifest.json", ("sample_map.json", "sample_map.png"),
             [(drawings[0], "--eye-at", p) for p in ("38,12", "8,12")]),
            ("shrink", "sample_shrink_manifest.json", ("sample_shrunk.png", "sample_palette.png"),
             [(d, "--colours", "3", "--size", "12,6") for d in drawings]),
        ]
        for tool, manifest, filenames, variants in cases:
            try:
                verify(root / tool, tool, manifest, filenames, variants)
            except AssertionError as exc:
                failed = True
                print(f"{tool}: FAILED {exc}")
            else:
                print(f"{tool}: failed publication preserved the set, concurrent publication selected one set")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
