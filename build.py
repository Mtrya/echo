#!/usr/bin/env python3
"""
Echo Build Script
Automates the complete packaging process for deployment.
Supports both PyInstaller-only (default) and Tauri (--tauri) builds.
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*50}")
    print(f"Step: {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print('='*50)

    try:
        result = subprocess.run(cmd, check=True, shell=isinstance(cmd, str),
                              capture_output=True, text=True)
        print("Success!")
        if result.stdout:
            print("STDOUT:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("Failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def check_prerequisites(tauri=False):
    """Check if all prerequisites are installed."""
    print("Checking prerequisites...")

    # Check Python
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        print(f"  Python: {result.stdout.strip()}")
    except:
        print("  Python not found")
        return False

    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"  Node.js: {result.stdout.strip()}")
    except:
        print("  Node.js not found - required for frontend build")
        return False

    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        print(f"  npm: {result.stdout.strip()}")
    except:
        print("  npm not found - required for frontend build")
        return False

    # Check PyInstaller
    try:
        result = subprocess.run(['pyinstaller', '--version'], capture_output=True, text=True)
        print(f"  PyInstaller: {result.stdout.strip()}")
    except:
        print("  PyInstaller not found - installing...")
        if not run_command([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], "Installing PyInstaller"):
            return False

    if tauri:
        # Check Rust/Cargo
        try:
            result = subprocess.run(['cargo', '--version'], capture_output=True, text=True)
            print(f"  Cargo: {result.stdout.strip()}")
        except:
            print("  Cargo not found - required for Tauri build")
            return False

    return True

def build_frontend():
    """Build the Vue.js frontend."""
    print("\nBuilding frontend...")

    # Change to frontend directory
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("  Frontend directory not found")
        return False

    os.chdir(frontend_dir)

    # Install dependencies
    if not run_command("npm install", "Installing frontend dependencies"):
        return False

    # Build the application
    if not run_command("npm run build", "Building Vue.js application"):
        return False

    # Change back to project root
    os.chdir("..")

    # Check if dist was created
    if not (frontend_dir / "dist").exists():
        print("  Frontend build failed - dist directory not created")
        return False

    print("  Frontend build completed")
    return True

def build_executable():
    """Build the executable with PyInstaller."""
    print("\nBuilding executable...")

    # Clean previous builds
    dist_dir = Path("dist")
    build_dir = Path("build")

    if dist_dir.exists():
        print("Cleaning previous dist directory...")
        shutil.rmtree(dist_dir)

    if build_dir.exists():
        print("Cleaning previous build directory...")
        shutil.rmtree(build_dir)

    # Run PyInstaller
    if not run_command("pyinstaller echo.spec --clean --noconfirm", "Building executable"):
        return False

    # Check if executable was created
    executable_path = dist_dir / "echo.exe" if os.name == 'nt' else dist_dir / "echo"
    if not executable_path.exists():
        print("  Executable not created")
        return False

    print(f"  Executable created: {executable_path}")
    return True

def create_portable_package():
    """Create a portable package with necessary files."""
    print("\nCreating portable package...")

    dist_dir = Path("dist")
    portable_dir = dist_dir / "echo-portable"

    # Clean previous portable package
    if portable_dir.exists():
        shutil.rmtree(portable_dir)

    portable_dir.mkdir(parents=True)

    # Copy executable
    executable_name = "echo.exe" if os.name == 'nt' else "echo"
    executable_path = dist_dir / executable_name
    shutil.copy2(executable_path, portable_dir / executable_name)

    # Copy documentation
    readme_files = ["README.md"]
    for readme in readme_files:
        if Path(readme).exists():
            shutil.copy2(readme, portable_dir / readme)

    # Create a simple batch file for Windows
    if os.name == 'nt':
        batch_file = portable_dir / "Start echo.bat"
        with open(batch_file, 'w') as f:
            f.write('@echo off\n')
            f.write('echo Starting echo...\n')
            f.write('start "" "%~dp0echo.exe"\n')

    print(f"  Portable package created: {portable_dir}")
    return True

def build_sidecar():
    """Build the sidecar binary and copy to src-tauri/binaries/."""
    print("\nBuilding sidecar binary...")

    if not run_command(
        [sys.executable, 'scripts/build_sidecar.py'],
        "Building sidecar with PyInstaller"
    ):
        return False

    print("  Sidecar binary built successfully")
    return True

def build_tauri_app():
    """Build the Tauri application."""
    print("\nBuilding Tauri application...")

    os.chdir("frontend")

    if not run_command("npx tauri build", "Building Tauri app"):
        os.chdir("..")
        return False

    os.chdir("..")

    print("  Tauri app built successfully")
    return True

def main():
    """Main build process."""
    parser = argparse.ArgumentParser(description="Echo Build Script")
    parser.add_argument('--tauri', action='store_true',
                        help='Build as Tauri app instead of standalone PyInstaller exe')
    args = parser.parse_args()

    print("Echo Build Script")
    print("="*50)
    print(f"Build mode: {'Tauri' if args.tauri else 'PyInstaller (standalone)'}")

    # Check prerequisites
    if not check_prerequisites(tauri=args.tauri):
        print("Prerequisites check failed")
        sys.exit(1)

    if args.tauri:
        # Tauri build: sidecar + Tauri (frontend built by Tauri's beforeBuildCommand)
        if not build_sidecar():
            print("Sidecar build failed")
            sys.exit(1)

        if not build_tauri_app():
            print("Tauri build failed")
            sys.exit(1)

        print("\n" + "="*50)
        print("Tauri build completed successfully!")
        print("="*50)
        print("Output: frontend/src-tauri/target/release/bundle/")
    else:
        # Legacy PyInstaller build
        if not build_frontend():
            print("Frontend build failed")
            sys.exit(1)

        if not build_executable():
            print("Executable build failed")
            sys.exit(1)

        if not create_portable_package():
            print("Portable package creation failed")
            sys.exit(1)

        print("\n" + "="*50)
        print("Build completed successfully!")
        print("="*50)
        print("Output files:")
        print("  Executable: dist/echo.exe" if os.name == 'nt' else "  Executable: dist/echo")
        print("  Portable package: dist/echo-portable/")
        print("\nTo test the application:")
        print("  1. Run the executable directly")
        print("  2. Or extract the portable package and run from there")

if __name__ == "__main__":
    main()
