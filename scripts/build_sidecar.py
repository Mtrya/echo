#!/usr/bin/env python3
"""
Build the Echo sidecar binary and copy it to src-tauri/binaries/ with the correct target triple name.
"""

import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path


def get_target_triple():
    """Detect the Rust-style target triple for the current platform."""
    machine = platform.machine().lower()
    system = platform.system().lower()

    arch_map = {
        'x86_64': 'x86_64',
        'amd64': 'x86_64',
        'aarch64': 'aarch64',
        'arm64': 'aarch64',
    }
    arch = arch_map.get(machine, machine)

    if system == 'windows':
        return f'{arch}-pc-windows-msvc'
    elif system == 'darwin':
        return f'{arch}-apple-darwin'
    elif system == 'linux':
        return f'{arch}-unknown-linux-gnu'
    else:
        raise RuntimeError(f'Unsupported platform: {system} {machine}')


def main():
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print('Building Echo sidecar binary...')
    print(f'Project root: {project_root}')

    # Run PyInstaller with sidecar spec
    result = subprocess.run(
        ['pyinstaller', 'sidecar.spec', '--clean', '--noconfirm'],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print('PyInstaller failed!')
        print('STDOUT:', result.stdout)
        print('STDERR:', result.stderr)
        sys.exit(1)

    print('PyInstaller build succeeded.')

    # Determine source and destination paths
    exe_ext = '.exe' if platform.system() == 'Windows' else ''
    source = project_root / 'dist' / f'echo-backend{exe_ext}'

    if not source.exists():
        print(f'ERROR: Built binary not found at {source}')
        sys.exit(1)

    target_triple = get_target_triple()
    binaries_dir = project_root / 'frontend' / 'src-tauri' / 'binaries'
    binaries_dir.mkdir(parents=True, exist_ok=True)

    dest = binaries_dir / f'echo-backend-{target_triple}{exe_ext}'

    print(f'Copying {source} -> {dest}')
    shutil.copy2(source, dest)

    print(f'Sidecar binary ready: {dest}')


if __name__ == '__main__':
    main()
