# Echo - LLM-Powered English+Math Exam Platform for Chinese Kids

## Project Vision

Simple, straightforward exam simulation platform for 10-year-old Chinese students learning English and Math. Features voice interaction, LLM-powered grading, and TTS capabilities.

## Core Requirements

- **Target**: 10-year-old Chinese students (non-native English speakers)
- **Subjects**: English + Math (mixed exams)
- **Timeline**: Full implementation in 2 weeks
- **Scope**: Simple, focused, no unnecessary complexity
- **Deployment**: Local development → Windows .exe via PyInstaller
- **Motivation**: A friend of the user asks me to develop this for his kid.

## Tech Stack

### Backend

- **Framework**: FastAPI (simple, modern, auto-documentation)
- **Language**: Python 3.11+
- **Package Management**: uv
- **APIs**: SiliconFlow, Modelscope (LLM, TTS, Speech-to-Text)

### Frontend

Learning frontend techniques via implementation.

- **Framework**: Vue.js 3 (beginner-friendly, great documentation)
- **Build Tool**: Vite (fast, simple)
- **Language**: HTML + CSS + JavaScript (explained to a total beginner)
- **UI**: Simple green/white theme
- **Audio**: Web Audio API for recording/playback

### Architecture

```file structure
echo/
├── backend/           # FastAPI server
├── frontend/          # Vue.js app
├── exams/            # Question banks (YAML)
└── CLAUDE.md         # This file
```

## Exam Question Types

### 1. Multiple Choice Questions

- **Format**: A/B/C/D selection
- **Timer**: 30 seconds per question
- **Input**: Mouse click
- **LLM Use**: Provide explanations

### 2. Read Aloud Practice

- **Format**: System displays English text, student reads aloud
- **Timer**: 15 seconds per question
- **Input**: Voice recording (Web Audio API)
- **LLM Use**: Transcribe speech (via speech-to-text model)

### 3. Quick Response

- **Format**: Audio question played, student responds verbally
- **Timer**: 15 seconds per question
- **Input**: Voice recording
- **LLM Use**: Transcribe speech (via speech-to-text model), grade answer relevance

### 4. Translation

- **Format**: Chinese text → English translation
- **Timer**: 30 seconds per question
- **Input**: Voice recording
- **LLM Use**: Transcribe speech (via speech-to-text model), grade translation quality

## API Integration Plan

### SiliconFlow & Modelscope APIs

- **LLM**: Question generation, grading, feedback, explanations
- **TTS**: Text-to-speech for questions and instructions
- **Speech-to-Text**: Voice answer transcription

### API Flow

1. TTS generates audio for questions
2. Student records audio responses
3. Speech-to-text transcribes responses
4. LLM grades answers and provides feedback
5. Results compiled and displayed

## Development Timeline Status

### Week 1: Frontend Learning & Implementation ✅ **COMPLETED**

#### Day 1-2: Vue.js Fundamentals ✅ **COMPLETED**

- **Goal**: Understand basic Vue.js concepts
- **Learn**: Components, templates, data binding, events
- **Build**: Simple static question display

#### Day 3-4: Interactive Components ✅ **COMPLETED**

- **Goal**: Build interactive question components
- **Learn**: Event handling, state management, conditional rendering
- **Build**: Multiple choice questions with timers

#### Day 5-6: Audio Integration ✅ **COMPLETED**

- **Goal**: Add voice recording and playback
- **Learn**: Web Audio API, mediaRecorder, audio blobs
- **Build**: Recording components for all question types

#### Day 7-8: API Integration ✅ **COMPLETED**

- **Goal**: Connect frontend to backend APIs
- **Learn**: HTTP requests, async/await, error handling
- **Build**: API service layer, data flow

#### Day 9-10: Polish & Integration ✅ **COMPLETED**

- **Goal**: Complete frontend, integrate with mock backend
- **Learn**: Component composition, routing, final styling
- **Build**: Complete exam flow from start to finish

### Week 2: Backend Implementation ✅ **COMPLETED**

#### Day 11-12: Core Backend Setup ✅ **COMPLETED**

- **Goal**: Build FastAPI backend with basic structure
- **Tasks**:
  - ✅ Initialize FastAPI project
  - ✅ Learn FastAPI basics
  - ✅ Set up SiliconFlow/Modelscope API clients
  - ✅ Create Pydantic models for questions/answers
  - ✅ Implement YAML exam configuration loading

#### Day 13-14: LLM Integration & Logic ✅ **COMPLETED**

- **Goal**: Implement LLM-powered features
- **Tasks**:
  - ✅ Create question generation endpoints
  - ✅ Implement grading logic for all question types
  - ✅ Add TTS and speech-to-text integration
  - ✅ Build exam session management

#### Day 15-16: Integration & Testing ✅ **COMPLETED**

- **Goal**: Connect frontend and backend
- **Tasks**:
  - ✅ Replace mock data with real API calls
  - ✅ Test complete exam flow
  - ✅ Fix bugs and polish UX
  - ✅ Prepare for Windows deployment

## Backend Status: ✅ **FULLY IMPLEMENTED**

The backend is now complete with all core functionality working:

- ✅ **FastAPI server** with auto-generated documentation at `/docs`
- ✅ **LLM integration** with streaming API calls to avoid rate limiting
- ✅ **Speech processing** with SiliconFlow APIs and fallback implementations
- ✅ **File conversion** for exam creation from various formats
- ✅ **Session management** with state tracking
- ✅ **All 4 question types** supported and tested
- ✅ **Comprehensive error handling** and logging
- ✅ **CORS middleware** for frontend integration

### Current Backend Architecture

```file structure
backend/
├── main.py              # FastAPI app with all endpoints
├── models.py            # Pydantic models for data validation
├── llm_client.py        # LLM client with streaming API calls
├── speech_client.py     # Speech-to-text and text-to-speech
├── file_conversion.py   # File processing and exam creation
├── exam_logic.py        # Session management and state tracking
└── utils.py             # Helper functions
```

## Future Backend Polish Tasks

### 1. LLM-Powered Smart File Conversion

- **Goal**: Use LLM to intelligently parse and convert various file formats into exam questions
- **Features**:
  - Extract questions from PDFs, Word documents, and images
  - Automatically identify question types and structure
  - Generate appropriate options and correct answers
  - Create exam metadata and difficulty levels

### 2. Audio Cache System

- **Goal**: Cache generated audio files to reduce API calls and improve performance
- **Features**:
  - Store generated TTS audio locally with hash-based keys
  - Implement cache invalidation and cleanup
  - Add audio compression and format optimization
  - Support for multiple voice options and languages

## Current File Structure

```file structure
echo/
├── backend/                 # ✅ COMPLETED
│   ├── main.py              # FastAPI app with all endpoints
│   ├── models.py            # Pydantic models for data validation
│   ├── omni_client.py       # Unified LLM client for all AI processing
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
│       │   └── Translation.vue    # Translation questions
│       ├── App.vue          # Main application component
│       ├── main.js          # Application entry point
│       └── utils/           # Utility functions
│           └── mp3Recorder.js      # Audio recording utility
├── exams/                   # ✅ COMPLETED
│   ├── exam-2098.yaml       # Comprehensive exam (2098)
│   ├── exam-2099.yaml       # Comprehensive exam (2099)
│   └── test.yaml            # Test exam file
├── audio_cache/             # Generated audio files cache
│   ├── student_answers/     # Student audio recordings by session
│   └── tts/                 # Text-to-speech cache
├── .env                     # Environment variables
├── .gitignore               # Git ignore rules
├── .python-version          # Python version specification
├── pyproject.toml           # Python project configuration
├── uv.lock                  # Python dependency lock file
├── README.md                # Project README
└── CLAUDE.md               # This file
```

## Engineering Style

- No over engineering, even dumb implementation is better than over engineering.
- Always ask the user to start or restart the server.
- Don't ever return mock data. If there's an error, let it expose naturally instead of pretending that everything is working all right.
- Always check API_DOCUMENTATION.md when implementing frontend services.
- try-except blocks are **FORBIDDEN**.

TODOs:

- settings (backend + frontend)
- get started (backend + frontend)
- audio testing page (frontend)
- packaging
