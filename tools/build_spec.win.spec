# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows build

from pathlib import Path

block_cipher = None
PROJECT_DIR = Path(__file__).resolve().parent.parent

datas_files = [
    (str(PROJECT_DIR / 'board_layout.json'), '.'),
    (str(PROJECT_DIR / 'decks.json'), '.'),
    (str(PROJECT_DIR / 'textures.json'), '.'),
    (str(PROJECT_DIR / 'data'), 'data'),
]

a = Analysis(
    [str(PROJECT_DIR / 'scripts' / 'run_gui.py')],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=datas_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='gamecore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='gamecore',
)
