from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    try:
        tag = subprocess.check_output(
            ['git', 'describe', '--tags', '--abbrev=0'], stderr=subprocess.DEVNULL
        ).decode().strip()
    except subprocess.CalledProcessError:
        tag = None
    args = ['git', 'log', '--pretty=format:* %s', '--no-merges']
    if tag:
        args.append(f'{tag}..HEAD')
    log = subprocess.check_output(args).decode()
    out = ['# Changelog', '']
    if tag:
        out.append(f'## Unreleased')
    else:
        out.append('## Changes')
    out.append(log)
    Path('CHANGELOG.md').write_text('\n'.join(out).strip() + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
