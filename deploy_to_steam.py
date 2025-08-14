#!/usr/bin/env python3
"""Upload the packaged game build to Steam using steamcmd.

This script generates temporary VDF files describing the app and depot
configuration for each platform and then invokes ``steamcmd`` to upload the
build.  It assumes the game has already been packaged into executables (for
example via PyInstaller) and placed in ``dist/<platform>`` directories.

Before running, set the following environment variables:

    STEAM_USERNAME - Steam account used for uploading
    STEAM_PASSWORD - password for that account
    STEAM_GUARD    - (optional) Steam Guard code if required

Update ``STEAM_APP_ID`` and ``DEPOT_IDS`` with the values for your game from
Steamworks before using the script.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
import textwrap

# ---------------------------------------------------------------------------
# Steam configuration -- replace the IDs below with real values from
# Steamworks for the game and its depots.
STEAM_APP_ID = "480"  # dummy app id
DEPOT_IDS = {
    "win": "4801",
    "mac": "4802",
    "linux": "4803",
}
BUILD_DESCRIPTION = "Automated build upload"
# ---------------------------------------------------------------------------

TEMPLATES = {
    "app": textwrap.dedent(
        """
        "appbuild"
        {
            "appid" "{app_id}"
            "desc" "{desc}"
            "buildoutput" "build/tmp"
            "setlive" "public"
            "depots"
            {
                "{depot_id}" "{depot_vdf}"
            }
        }
        """
    ).strip(),
    "depot": textwrap.dedent(
        """
        "DepotBuild"
        {
            "DepotID" "{depot_id}"
            "contentroot" "{content_root}"
            "FileMapping"
            {
                "LocalPath" "*"
                "DepotPath" "."
                "recursive" "1"
            }
        }
        """
    ).strip(),
}


def build_vdf(platform: str, depot_id: str, content_root: Path, out_dir: Path) -> Path:
    """Create app and depot VDF files for ``platform`` and return the app VDF."""
    depot_vdf = out_dir / f"depot_build_{platform}.vdf"
    depot_vdf.write_text(
        TEMPLATES["depot"].format(depot_id=depot_id, content_root=content_root)
    )

    app_vdf = out_dir / f"app_build_{platform}.vdf"
    app_vdf.write_text(
        TEMPLATES["app"].format(
            app_id=STEAM_APP_ID,
            desc=BUILD_DESCRIPTION,
            depot_id=depot_id,
            depot_vdf=depot_vdf,
        )
    )
    return app_vdf


def steamcmd_command(username: str, password: str, guard: str | None, app_vdf: Path) -> list[str]:
    """Construct the ``steamcmd`` command used to upload ``app_vdf``."""
    cmd = ["steamcmd", "+login", username, password]
    if guard:
        cmd.append(guard)
    cmd += ["+run_app_build", str(app_vdf), "+quit"]
    return cmd


def main() -> None:
    username = os.environ.get("STEAM_USERNAME")
    password = os.environ.get("STEAM_PASSWORD")
    guard = os.environ.get("STEAM_GUARD")
    if not username or not password:
        raise SystemExit("STEAM_USERNAME and STEAM_PASSWORD must be set")

    out_dir = Path("build/steam")
    out_dir.mkdir(parents=True, exist_ok=True)

    for platform, depot_id in DEPOT_IDS.items():
        content_root = Path("dist") / platform  # packaged build location
        app_vdf = build_vdf(platform, depot_id, content_root.resolve(), out_dir)
        print(f"Uploading {platform} build to Steam...")
        subprocess.run(steamcmd_command(username, password, guard, app_vdf), check=True)


if __name__ == "__main__":
    main()
