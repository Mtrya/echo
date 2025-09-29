# Echo - LLM-Powered English+Math Exam Platform for Chinese Kids

## Project Vision

Simple, straightforward exam simulation platform for 10-year-old Chinese students learning English and Math. Features voice interaction, LLM-powered grading, and TTS capabilities.

## Core Requirements

- **Target**: 10-year-old Chinese students (non-native English speakers)
- **Subjects**: English + Math (mixed exams)
- **Scope**: Simple, focused, no unnecessary complexity
- **Deployment**: Local development → Windows echo.exe via PyInstaller

## Tech Stack

### Backend

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Package Management**: uv
- **APIs**: Dashscope (Qwen3-Omni-Flash & Qwen3-VL-Plus)

### Frontend

Learning frontend techniques via implementation.

- **Framework**: Vue.js 3
- **Build Tool**: Vite
- **Language**: HTML + CSS + JavaScript
- **UI**: Simple green/white theme
- **Audio**: Web Audio API for recording/playback

## Current File Structure

```file structure
echo/
├── backend/                 # ✅ COMPLETED
│   ├── main.py              # FastAPI app with all endpoints
│   ├── models.py            # Pydantic models for data validation
│   ├── omni_client.py       # Unified LLM client for all AI processing
│   ├── config.py            # Configuration management with AppData support
│   ├── paths.py             # Centralized path management for cross-platform
│   ├── file_conversion.py   # File processing and exam creation
│   └── exam_logic.py        # Session management and state tracking
├── frontend/                # ✅ COMPLETED
│   ├── API_DOCUMENTATION.md  # API documentation
│   ├── package.json         # Frontend package configuration
│   ├── package-lock.json    # Frontend dependency lock file
│   ├── vite.config.js       # Frontend build configuration
│   └── src/
│       ├── components/      # Vue components
│       │   ├── AudioTest.vue      # Audio testing component
│       │   ├── HomePage.vue       # Exam selection page
│       │   ├── InstructionPage.vue # Section instruction player
│       │   ├── MultipleChoice.vue  # Multiple choice questions
│       │   ├── QuickResponse.vue  # Quick response questions
│       │   ├── ReadAloud.vue      # Read aloud practice
│       │   ├── Results.vue        # Exam results display
│       │   ├── Settings.vue       # Settings management
│       │   └── Translation.vue    # Translation questions
│       ├── App.vue          # Main application component
│       ├── main.js          # Application entry point
│       └── utils/           # Utility functions
│           └── mp3Recorder.js      # Audio recording utility
├── exams/
│   ├── exam-2098.yaml
│   └── exam-2099.yaml
├── prompts/
│   ├── file_conversion.txt
│   ├── multiple_choice_grading.txt
│   ├── quick_response_grading.txt
│   ├── read_aloud_grading.txt
│   ├── text_to_speech.txt
│   └── translation_grading.txt
├── audio_cache/             # Generated audio files cache
│   ├── student_answers/     # Student audio recordings by session
│   └── tts/                 # Text-to-speech cache
├── build.py                 # PyInstaller build script
├── launch.py                # Application launcher
├── .gitignore               # Git ignore rules
├── .python-version          # Python version specification
├── config.yaml.example      # Configuration example
├── pyproject.toml           # Python project configuration
├── uv.lock                  # Python dependency lock file
├── echo.ico                 # Project icon
├── echo.spec                # Packaging
├── README.md                # Project README
└── CLAUDE.md               # This file
```

## Engineering Style

- No over engineering, even dumb implementation is better than over engineering.
- Always ask the user to start or restart the server.
- Don't ever return mock data. If there's an error, let it expose naturally instead of pretending that everything is working all right.
- Always check API_DOCUMENTATION.md when implementing frontend services.

## todos

- enhance file-conversion prompt with examples
- convert to Chinese interface
- update README with new images of interface with highlights
