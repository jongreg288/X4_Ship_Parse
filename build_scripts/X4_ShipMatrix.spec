# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../src', 'src'),
        ('../README.md', '.'),
        # Include matplotlib data files
        ('C:/Users/pheno/Code_Projects/X4_ShipMatrix/.venv/Lib/site-packages/matplotlib/mpl-data', 'matplotlib/mpl-data'),
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
        # Matplotlib and plotting dependencies
        'matplotlib',
        'matplotlib.backends',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends._backend_qtagg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'matplotlib.backend_bases',
        'matplotlib.font_manager',
        'numpy',
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
    name='X4 ShipMatrix',
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