# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None
root = Path(SPECPATH).resolve().parent

ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")

a = Analysis(
    [str(root / 'src' / 'kesit' / 'ui' / 'app.py')],
    pathex=[str(root / 'src')],
    binaries=ctk_binaries,
    datas=[
        (str(root / 'config'), 'config'),
        (str(root / 'assets' / 'branding'), 'assets/branding'),
        (str(root / 'src' / 'kesit' / 'locales'), 'locales'),
        *ctk_datas,
    ],
    hiddenimports=[
        'ezdxf',
        'ezdxf.acc',
        'shapely',
        'yaml',
        'customtkinter',
        'PIL',
        'kesit',
        'kesit.app',
        'kesit.ui',
        'kesit.rendering',
        *ctk_hiddenimports,
    ],
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
    [],
    exclude_binaries=True,
    name='Kotline',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / 'assets' / 'branding' / 'app_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Kotline',
)
