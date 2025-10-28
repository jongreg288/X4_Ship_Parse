# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[
        ('../distro/XRCatTool.exe', '.'),
        ('../distro/XRCatToolGUI.exe', '.'),
    ],
    datas=[
        ('../src', 'src'),
        ('../README.md', '.'),
        ('../distro/Readme.txt', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'pandas',
        'xml.etree.ElementTree',
        'pathlib',
        're',
        'webbrowser',
        'subprocess',
        # Removed network-related imports to reduce size and dependencies:
        # 'requests', 'json', 'tempfile', 'zipfile'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='X4_Ship_Parser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=None,
)