import argparse
import shutil
import stat
from pathlib import Path

EXCLUDE = {"tests", "__pycache__"}
SKIP_SUFFIXES = {".py", ".pyc"}


def package(target: str) -> None:
    dist_dir = Path("dist") / target
    staging_dir = Path("build/staging") / target

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    for item in dist_dir.iterdir():
        if item.name in EXCLUDE or item.suffix in SKIP_SUFFIXES:
            continue

        dest = staging_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
            if target != "win":
                mode = dest.stat().st_mode
                dest.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare release staging directory")
    parser.add_argument("--target", choices=["win", "mac", "linux"], required=True)
    args = parser.parse_args()
    package(args.target)


if __name__ == "__main__":  # pragma: no cover
    main()
