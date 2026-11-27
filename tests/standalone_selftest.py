"""Run the distributed commands with only the two skill directories installed."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    source = Path(__file__).resolve().parents[1] / "skills"
    failed = False
    with tempfile.TemporaryDirectory() as tmp:
        skills = Path(tmp) / "skills"
        for name in ("pixel-anim-check", "pixel-animate"):
            shutil.copytree(source / name, skills / name, ignore=shutil.ignore_patterns("__pycache__"))
        scripts = [skills / "pixel-anim-check" / name for name in ("pixel_anim_check.py", "prepare_sheet.py",
                                                                    "repair_sheet.py")]
        scripts.extend(skills / "pixel-animate" / (name + ".py") for name in ("body_parts", "creature_map", "shrink"))
        for script in scripts:
            result = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "-W", "error::DeprecationWarning",
                                     str(script), "--selftest"], cwd=tmp, capture_output=True, text=True, encoding="utf-8")
            passed = result.returncode == 0 and "selftest: all hold" in result.stdout
            print(f"{script.name} --selftest: exit {result.returncode}", flush=True)
            if not passed:
                print(result.stdout + result.stderr, flush=True)
                failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
