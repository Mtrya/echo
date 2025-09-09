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

## Development Timeline (2 Weeks)

### Week 1: Frontend Learning & Implementation (10 Days) (Learning and Implementation are equally important!)

#### Day 1-2: Vue.js Fundamentals

- **Goal**: Understand basic Vue.js concepts
- **Learn**: Components, templates, data binding, events
- **Build**: Simple static question display

#### Day 3-4: Interactive Components

- **Goal**: Build interactive question components
- **Learn**: Event handling, state management, conditional rendering
- **Build**: Multiple choice questions with timers

#### Day 5-6: Audio Integration

- **Goal**: Add voice recording and playback
- **Learn**: Web Audio API, mediaRecorder, audio blobs
- **Build**: Recording components for all question types

#### Day 7-8: API Integration

- **Goal**: Connect frontend to backend APIs
- **Learn**: HTTP requests, async/await, error handling
- **Build**: API service layer, data flow

#### Day 9-10: Polish & Integration

- **Goal**: Complete frontend, integrate with mock backend
- **Learn**: Component composition, routing, final styling
- **Build**: Complete exam flow from start to finish

### Week 2: Backend Implementation (4 Days) ✅ **COMPLETED**

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
│   ├── llm_client.py        # LLM client with streaming API calls
│   ├── speech_client.py     # Speech-to-text and text-to-speech
│   ├── file_conversion.py   # File processing and exam creation
│   ├── exam_logic.py        # Session management and state tracking
│   └── utils.py             # Helper functions
├── frontend/                # 🚧 IN PROGRESS
│   └── src/
│       ├── components/      # Vue components
│       │   ├── QuestionTypes/
│       │   │   ├── MultipleChoice.vue
│       │   │   ├── ReadAloud.vue
│       │   │   ├── QuickResponse.vue
│       │   │   └── Translation.vue
│       │   ├── Timer.vue
│       │   ├── AudioRecorder.vue
│       │   └── ExamResults.vue
│       ├── composables/     # Vue 3 composables
│       │   ├── useAudio.js
│       │   ├── useTimer.js
│       │   └── useExam.js
│       ├── services/        # API services
│       │   └── examService.js
│       ├── stores/          # Pinia stores
│       │   └── examStore.js
│       ├── App.vue
│       └── main.js
├── exams/                   # ✅ COMPLETED
│   ├── sample_test.yaml     # Sample exam configuration
│   ├── comprehensive_test.yaml  # Comprehensive test with all question types
│   └── english_math_1.yaml  # Real exam data
├── pyproject.toml           # Python project configuration
├── uv.lock                 # Dependency lock file
├── .env                    # Environment variables
├── package.json            # Frontend package configuration
├── vite.config.js          # Frontend build configuration
└── CLAUDE.md               # This file
```

## Frontend Learning Path (Beginner Friendly)

### Level 1: Building Blocks (Day 1-2)

```vue
<!-- This is a Vue component - like a LEGO block -->
<template>
  <div class="question-box">
    <h2>{{ question.text }}</h2>
    <button @click="selectAnswer('A')">A</button>
  </div>
</template>

<script>
// This is like the brain of your LEGO block
export default {
  data() {
    return {
      question: { text: "What is 2+2?" }
    }
  },
  methods: {
    selectAnswer(answer) {
      console.log("You selected:", answer)
    }
  }
}
</script>
```

### Level 2: Making Things Interactive (Day 3-4)

```vue
<template>
  <div v-if="!timeUp">
    <p>Time left: {{ seconds }} seconds</p>
    <!-- This timer counts down like a kitchen timer -->
  </div>
  <div v-else>
    <p>Time's up!</p>
  </div>
</template>

<script>
export default {
  data() {
    return {
      seconds: 30,
      timeUp: false
    }
  },
  mounted() {
    // Start the timer when the component appears
    this.startTimer()
  },
  methods: {
    startTimer() {
      setInterval(() => {
        this.seconds--
        if (this.seconds <= 0) {
          this.timeUp = true
        }
      }, 1000)
    }
  }
}
</script>
```

## Frontend-Backend Communication

### Simple API Call (Explained Simply)

```javascript
// This is like sending a letter to the backend
async function getQuestion() {
  try {
    // Send request to backend
    const response = await fetch('http://localhost:8000/question')
    
    // Open the letter to see what's inside
    const data = await response.json()
    
    // Use the data we got back
    return data
  } catch (error) {
    // If the letter gets lost in the mail
    console.error('Oops, something went wrong!', error)
  }
}
```

## Success Criteria

1. ✅ All 4 question types working
2. ✅ Voice interaction functional
3. ✅ LLM grading accurate
4. ✅ Clean, simple UI for kids
5. ✅ Complete exam flow (start → questions → results)
6. ✅ Windows .exe deployment ready

## Risk Assessment

- **Voice recording complexity**: High
- **LLM API reliability**: Low, the user has experience about it
- **Cross-platform deployment**: Medium, but PyInstaller works well
- **Frontend learning**: High, though Vue.js is very beginner-friendly, the user is a total beginner. The user is highly concerned about it.

## Windows Deployment Strategy

### Packaging Steps

1. Build Vue.js frontend to static files
2. Use PyInstaller to package FastAPI + static files
3. Test on Windows target machine
4. Create simple installer if needed

### Development Workflow

- Linux development environment
- Regular testing of cross-platform compatibility
- Final Windows build using PyInstaller with Wine or CI/CD

## Teaching Philosophy: Zero-Prior-Knowledge Approach

### What This Means

- **No assumptions**: I won't assume you know any frontend-related concepts
- **Ultra-specific**: Every line of code will be explained in detail
- **Analogies first**: Complex concepts explained with simple analogies
- **Visual thinking**: Code as building blocks, not abstract text
- **Step-by-step**: One tiny concept at a time, no jumping ahead
- **Introduce-first**: Whenever a new concept is involved, introduce it first

### How I should Teach

1. **Show the user the code** (the what)
2. **Explain what it does** (the why)
3. **Break it down piece by piece** (the how)
4. **Answer any questions** (the clarification)

### The user's Job

- **Stop me immediately** if anything doesn't make sense
- **Ask "why"** for everything - there are no stupid questions
- **Experiment** - change things and see what happens
- **Take your time** - learning isn't a race

## Engineering Style

- No over engineering, even dumb implementation is better than over engineering.

- Always ask the user to start or restart the server.
