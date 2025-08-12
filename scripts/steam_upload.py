"""Upload a build to Steam using ``steamcmd``.

This script fills in VDF templates located in ``steam/`` and invokes the
``steamcmd`` tool.  It expects the following environment variables to be set:

* ``STEAM_USERNAME``
* ``STEAM_PASSWORD``
* ``STEAM_GUARD``
* ``STEAM_APP_ID``
* ``STEAM_DEPOT_WIN``
* ``STEAM_DEPOT_MAC``
* ``STEAM_DEPOT_LINUX``
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from tools.versioning import get_version


def _require_env(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError as exc:  # pragma: no cover - defensive programming
        raise SystemExit(f"Missing environment variable: {name}") from exc


def _build_vdf(template: Path, output: Path, replacements: dict[str, str]) -> None:
    text = template.read_text()
    for key, value in replacements.items():
        text = text.replace(f"${{{key}}}", value)
    output.write_text(text)


def main() -> None:  # pragma: no cover - CLI glue
    parser = argparse.ArgumentParser(description="Upload build to Steam")
    parser.add_argument("--platform", choices=["win", "mac", "linux"], required=True)
    parser.add_argument("--channel", choices=["beta", "public"], required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--dry-run", action="store_true", help="do not call steamcmd")
    args = parser.parse_args()

    username = _require_env("STEAM_USERNAME")
    password = _require_env("STEAM_PASSWORD")
    guard = _require_env("STEAM_GUARD")
    app_id = _require_env("STEAM_APP_ID")

    depot_env = {
        "win": "STEAM_DEPOT_WIN",
        "mac": "STEAM_DEPOT_MAC",
        "linux": "STEAM_DEPOT_LINUX",
    }
    depot_id = _require_env(depot_env[args.platform])

    version = get_version()
    build_desc = f"{version} {args.description}"

    steam_dir = Path(__file__).resolve().parent.parent / "steam"
    app_template = steam_dir / f"app_build_{args.platform}.vdf"
    depot_template = steam_dir / f"depot_build_{args.platform}.vdf"

    tmp_dir = Path("build/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    app_vdf_path = tmp_dir / f"app_build_{args.platform}.vdf"
    depot_vdf_path = tmp_dir / f"depot_build_{args.platform}.vdf"

    content_root = str(Path(f"build/staging/{args.platform}").resolve())

    _build_vdf(
        depot_template,
        depot_vdf_path,
        {"DEPOT_ID": depot_id, "CONTENT_ROOT": content_root},
    )
    _build_vdf(
        app_template,
        {
            "APP_ID": app_id,
            "BUILD_DESCRIPTION": build_desc,
            "CHANNEL": args.channel,
            "DEPOT_ID": depot_id,
        },
        app_vdf_path,
    )

    if args.dry_run:
        print(f"app vdf: {app_vdf_path}")
        print(f"depot vdf: {depot_vdf_path}")
        return

    cmd = [
        "steamcmd",
        "+login",
        username,
        password,
        guard,
        "+run_app_build",
        str(app_vdf_path),
        "+quit",
    ]
    subprocess.check_call(cmd)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
