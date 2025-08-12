from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    loc_dir = Path(__file__).resolve().parents[1] / 'data' / 'locales'
    files = list(loc_dir.glob('*.json'))
    locales = {f.name: json.loads(f.read_text(encoding='utf-8')) for f in files}
    all_keys = set().union(*(data.keys() for data in locales.values()))
    ok = True
    for name, data in locales.items():
        missing = all_keys - set(data.keys())
        if missing:
            print(f'{name} missing keys: {sorted(missing)}')
            ok = False
    if not ok:
        raise SystemExit(1)
    print('All locale keys present.')


if __name__ == '__main__':
    main()
