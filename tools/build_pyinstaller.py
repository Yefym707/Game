import argparse
import os
import subprocess
from pathlib import Path

RUNTIME_DIRS = ["data", "data/locales"]
RUNTIME_FILES = ["board_layout.json", "decks.json", "textures.json"]
ICON_MAP = {"win": "data/icon.ico", "mac": "data/icon.icns", "linux": "data/icon.png"}


def build(target: str) -> None:
    dist_dir = Path("dist") / target
    dist_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        f"--distpath={dist_dir}",
        "scripts/run_gui.py",
    ]

    for directory in RUNTIME_DIRS:
        p = Path(directory)
        if p.exists():
            cmd.extend(["--add-data", f"{p}{os.pathsep}{p}"])

    for file in RUNTIME_FILES:
        p = Path(file)
        if p.exists():
            cmd.extend(["--add-data", f"{p}{os.pathsep}{p}"])

    icon = Path(ICON_MAP.get(target, ""))
    if icon.is_file():
        cmd.append(f"--icon={icon}")

    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the GUI with PyInstaller")
    parser.add_argument("--target", choices=["win", "mac", "linux"], required=True)
    args = parser.parse_args()
    build(args.target)


if __name__ == "__main__":  # pragma: no cover
    main()
