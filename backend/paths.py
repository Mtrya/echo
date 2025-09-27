"""
Path management for Echo application.
Handles runtime path resolution for both development and packaged environments.
"""

import os
import sys
from pathlib import Path
from typing import Optional


class AppPaths:
    """Centralized path management for Echo application."""

    def __init__(self, base_path: Optional[Path] = None):
        if base_path:
            self.base_path = base_path
        else:
            self.base_path = self._get_base_path()

        # Initialize all paths
        self.audio_cache = self.base_path / "audio_cache"
        self.student_answers = self.audio_cache / "student_answers"
        self.tts_cache = self.audio_cache / "tts"
        self.exams_dir = self.base_path / "exams"
        self.prompts_dir = self.base_path / "prompts"
        self.config_file = self.base_path / "config.yaml"
        self.completed_exams_file = self.base_path / "completed_exams.json"

        # Ensure directories exist
        self._ensure_directories()

    def _get_base_path(self) -> Path:
        """Get the base path for application data."""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
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
        else:
            # Running in development environment
            return Path(__file__).parent.parent

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.audio_cache,
            self.student_answers,
            self.tts_cache,
            self.exams_dir,
            self.prompts_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def copy_default_files(self, source_base: Path):
        """Copy default files from bundled resources."""
        # Copy default config if it doesn't exist
        if not self.config_file.exists():
            source_config = source_base / "config.yaml"
            source_config_example = source_base / "config.yaml.example"

            if source_config.exists():
                import shutil
                shutil.copy(source_config, self.config_file)
            elif source_config_example.exists():
                import shutil
                shutil.copy(source_config_example, self.config_file)
                print(f"Created config from template. Please edit {self.config_file} to add your API key.")

        # Copy default prompts if they don't exist
        if not any(self.prompts_dir.glob("*.txt")):
            source_prompts = source_base / "prompts"
            if source_prompts.exists():
                import shutil
                shutil.copytree(source_prompts, self.prompts_dir, dirs_exist_ok=True)

        # Copy default exams if they don't exist
        if not any(self.exams_dir.glob("*.yaml")):
            source_exams = source_base / "exams"
            if source_exams.exists():
                for exam_file in source_exams.glob("*.yaml"):
                    import shutil
                    shutil.copy(exam_file, self.exams_dir)

        # Copy audio-test.mp3 if it doesn't exist
        audio_test_file = self.tts_cache / "audio-test.mp3"
        if not audio_test_file.exists():
            source_audio_test = source_base / "audio_cache" / "tts" / "audio-test.mp3"
            if source_audio_test.exists():
                import shutil
                shutil.copy(source_audio_test, audio_test_file)
                print(f"Copied audio-test.mp3 to {audio_test_file}")

    def get_bundled_path(self, relative_path: str) -> Path:
        """Get path to bundled resources (for PyInstaller)."""
        if getattr(sys, 'frozen', False):
            # In PyInstaller bundle, resources are in the same directory as the executable
            return Path(sys._MEIPASS) / relative_path
        else:
            # In development, use relative paths from project root
            return Path(__file__).parent.parent / relative_path


# Global paths instance
_paths: Optional[AppPaths] = None


def get_paths() -> AppPaths:
    """Get the global AppPaths instance."""
    global _paths
    if _paths is None:
        _paths = AppPaths()
    return _paths


def initialize_paths(base_path: Optional[Path] = None, copy_from: Optional[Path] = None):
    """Initialize the global AppPaths instance."""
    global _paths
    _paths = AppPaths(base_path)
    if copy_from:
        _paths.copy_default_files(copy_from)
    return _paths