# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Frontend build
        ('frontend/dist', 'frontend/dist'),
        # Configuration and data files
        ('config.yaml.example', '.'),
        ('prompts', 'prompts'),
        ('exams', 'exams'),
        # Include audio_cache directory structure (empty directories will be created)
        ('audio_cache', 'audio_cache'),
    ],
    hiddenimports=[
        'websockets',
        'aiohttp',
        'soundfile',
        'pillow',
        'pydub',
        'numpy',
        'scipy',
        'yaml',
        'markdown',
        'docx',
        'json_repair',
        'uvicorn',
        'fastapi',
        'pydantic',
        'pathlib',
        'ctypes',
        'threading',
        'webbrowser',
        'typing',
        'datetime',
        'uuid',
        'base64',
        'io',
        'traceback',
        'sys',
        'os',
        'time',
        'signal',
        'socket',
        'json',
        'asyncio',
        'shutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'pytest',
        'unittest',
        'test',
        'tests',
    ],
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
    name='Echo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='echo.ico',
    # uac_admin=True,  # Uncomment if admin privileges are needed
)