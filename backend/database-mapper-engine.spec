# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

backend_dir = Path(SPECPATH).resolve()
project_dir = backend_dir.parent

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('python_calamine')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Include data used by PubMed locale handling and Entrez parsing.
for package in ('babel', 'pycountry', 'Bio'):
    datas += collect_data_files(package)
datas.append((str(backend_dir / 'features/pubmed_scraper/legacy/country_names.json'), 'backend/features/pubmed_scraper/legacy'))
hiddenimports += ['openpyxl', 'xlrd', 'uvicorn.logging', 'uvicorn.loops.auto', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan.on']


a = Analysis(
    [str(backend_dir / 'sidecar.py')],
    pathex=[str(project_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='database-mapper-engine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
