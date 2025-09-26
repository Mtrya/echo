"""
Echo Application Launcher
Handles the complete application lifecycle including setup, directory management, and server startup.
"""

import sys
import os
import webbrowser
import threading
import time
import signal
from pathlib import Path
import uvicorn

# Add the project root to Python path
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    project_root = Path(sys._MEIPASS)
else:
    # Running in development environment
    project_root = Path(__file__).parent

sys.path.insert(0, str(project_root))


def get_app_data_path():
    """Get the application data directory for Echo."""
    if os.name == 'nt':  # Windows
        import ctypes
        from ctypes import wintypes

        CSIDL_LOCAL_APPDATA = 0x001c
        SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
        SHGetFolderPath.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.HANDLE, wintypes.DWORD, wintypes.LPCWSTR]
        SHGetFolderPath.restype = wintypes.HRESULT

        path_buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        result = SHGetFolderPath(0, CSIDL_LOCAL_APPDATA, 0, 0, path_buf)

        if result == 0:
            return Path(path_buf.value) / "Echo"
        else:
            return Path.home() / "AppData" / "Local" / "Echo"
    else:
        return Path.home() / ".echo"


def setup_directories():
    """Create necessary directories in AppData and copy default files."""
    app_data = get_app_data_path()
    print(f"Setting up Echo in: {app_data}")

    # Import path management
    from backend.paths import initialize_paths

    # Initialize paths with AppData location
    paths = initialize_paths(base_path=app_data)

    # Copy default files from project root
    source_base = project_root
    paths.copy_default_files(source_base)

    return paths


def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port."""
    import socket

    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            continue

    return start_port  # Return original if none found


def launch_browser(port):
    """Launch web browser after a short delay."""
    def delayed_launch():
        time.sleep(3)  # Wait for server to fully start
        try:
            webbrowser.open(f'http://127.0.0.1:{port}')
            print(f"Browser launched at http://127.0.0.1:{port}")
        except Exception as e:
            print(f"Failed to launch browser: {e}")
            print(f"Please open your browser and navigate to http://127.0.0.1:{port}")

    browser_thread = threading.Thread(target=delayed_launch, daemon=True)
    browser_thread.start()


def setup_signal_handler():
    """Setup signal handler for graceful shutdown."""
    def signal_handler(signum, frame):
        print("\nShutting down Echo gracefully...")
        sys.exit(0)

    if os.name != 'nt':  # Unix-like systems
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main application entry point."""
    print("Starting Echo Application...")

    try:
        # Setup signal handling
        setup_signal_handler()

        # Setup directories and copy default files
        paths = setup_directories()

        # Find available port
        port = find_available_port()
        print(f"Starting server on port {port}")

        # Set working directory to app data for consistent relative paths
        os.chdir(paths.base_path)

        # Add project root to Python path for imports
        sys.path.insert(0, str(project_root))

        # Import the app directly to avoid string import issues
        from backend.main import app

        # Launch browser in separate thread
        launch_browser(port)

        # Print startup message
        print("=" * 50)
        print("Echo is starting up...")
        print(f"Application data directory: {paths.base_path}")
        print(f"Server will be available at: http://127.0.0.1:{port}")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)

        # Run the server with direct app reference
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info",
            reload=False,  # Disable reload in packaged version
            access_log=False  # Reduce log noise
        )

    except KeyboardInterrupt:
        print("\nEcho stopped by user")
    except Exception as e:
        print(f"Error starting Echo: {e}")
        print("Please check the following:")
        print("1. All required files are in place")
        print("2. Port 8000 is not already in use")
        print("3. You have sufficient permissions")
        sys.exit(1)


if __name__ == "__main__":
    main()