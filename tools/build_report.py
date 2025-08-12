from __future__ import annotations

import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from gamecore import board, ai, rules, saveio, config as gconfig


def _rss_mb() -> float:
    with open('/proc/self/statm') as fh:
        rss = int(fh.readline().split()[1]) * os.sysconf('SC_PAGE_SIZE')
    return rss / (1024 * 1024)


def main() -> None:
    rules.set_seed(0)
    state = board.create_game(width=50, height=50, zombies=0)
    frames = 60
    times: list[float] = []
    start = time.perf_counter()
    for _ in range(frames):
        t0 = time.perf_counter()
        board.player_move(state, 'd')
        ai.zombie_turns(state)
        board.end_turn(state)
        times.append(time.perf_counter() - t0)
    total = time.perf_counter() - start
    avg_fps = frames / total
    min_fps = 1.0 / max(times) if times else 0.0
    ram = _rss_mb()
    save_path = gconfig.quicksave_path()
    saveio.save_game(state, save_path)
    save_size = save_path.stat().st_size
    log_dir = gconfig.CONFIG_DIR / 'logs'
    errors: list[str] = []
    if log_dir.exists():
        for path in log_dir.glob('*.log'):
            errors.extend(path.read_text().splitlines())
    report = [
        'Hardware',
        f'OS: {platform.platform()}',
        f'CPU: {os.cpu_count()}',
        '',
        'FPS',
        f'avg: {avg_fps:.2f}',
        f'min: {min_fps:.2f}',
        '',
        'RAM',
        f'peak: {ram:.2f} MB',
        '',
        'Errors',
        '\n'.join(errors[-10:]) if errors else 'none',
        '',
        'SaveSize',
        f'{save_size} bytes',
        '',
    ]
    Path('release_report.txt').write_text('\n'.join(report), encoding='utf-8')


if __name__ == '__main__':
    main()
