# Echo Exam Platform - API Documentation

## Overview

The Echo Exam Platform provides a RESTful API for managing and taking English+Math exams for Chinese students. The API uses JSON for requests and responses.

## Base URL

```url
http://localhost:8000
```

## Authentication

Currently no authentication is required (for development).

## API Endpoints

### 1. List Available Exams

**GET** `/exams/list`

List all available exam YAML files.

**Response:**

```json
{
  "exams": ["sample_test.yaml", "comprehensive_test.yaml", "exam-2099.yaml"]
}
```

### 2. Start Exam Session

**POST** `/session/start`

Start a new exam session. This loads the exam file and prepares all audio files.

**Request:**

```json
{
  "exam_file_path": "exam-2099.yaml"
}
```

**Response:**

```json
{
  "session_id": "a2a15ac2-f38b-406c-bd9b-ed53f8ad1d26",
  "exam_title": "Comprehensive English and Math Exam",
  "total_questions": 20,
  "message": "Exam session started with 20 questions"
}
```

### 3. Get Current Question

**GET** `/session/{session_id}/question`

Get the current question for the session. Includes audio file path if available.

**Response:**

```json
{
  "question": {
    "id": "q1",
    "type": "multiple_choice",
    "text": "What is 2+2?",
    "options": ["A: 4", "B: 5", "C: 6", "D: 7"],
    "reference_answer": "A",
    "time_limit": 30,
    "tts": "What is 2 plus 2?"
  },
  "audio_file_path": "../audio_cache/tts/bea39faa84a9823d21818aa1e104ecdd.mp3",
  "question_index": 0,
  "is_last": false,
  "instruction": {
    "text": "This is a multiple choice section. Please listen to each question and select the correct answer.",
    "tts": "This is a multiple choice section. Please listen to each question and select the correct answer."
  },
  "instruction_audio_file_path": "../audio_cache/tts/f4496987dabd9f56fa5c336c2ab63ff0.mp3"
}
```

### 4. Submit Answer

**POST** `/session/{session_id}/answer`

Submit an answer for the current question. Processing happens asynchronously.

**Request:**

```json
{
  "answer_text": "A",  // For text-based answers (optional)
  "audio_data": "base64-encoded-audio-data"  // For voice answers (optional)
}
```

**Note:** Audio data should be base64-encoded and sent as a string in the JSON payload. The backend will automatically decode it to bytes for processing. Only one of `answer_text` or `audio_data` should be provided based on question type.

**Response:**

```json
{
  "message": "Answer submitted and processing",
  "question_index": 0,
  "processing": true
}
```

### 5. Get Session Status

**GET** `/session/{session_id}/status`

Get the current status of a session (audio generation and STT/LLM processing).

**Response:**

```json
{
  "audio_generation": "completed",
  "processing": "idle"
}
```

**Status Values:**

- `audio_generation`: "generating" | "completed"
- `processing`: "idle" | "processing"

### 6. Get Final Results

**GET** `/session/{session_id}/results`

Get the final exam results after all questions are completed.

**Response:**

```json
{
  "session_id": "a2a15ac2-f38b-406c-bd9b-ed53f8ad1d26",
  "exam_title": "Comprehensive English and Math Exam",
  "total_score": 18.5,
  "max_score": 20,
  "percentage": 92.5,
  "question_results": [
    {
      "question_index": 0,
      "question_id": "q1",
      "question_type": "multiple_choice",
      "question_text": "What is 2+2?",
      "score": 1.0,
      "feedback": "Correct! Well done!",
      "explanation": "Detailed explanation here...",
      "suggested_answer": null
    }
  ],
  "start_time": "2025-09-09T17:36:50.608006",
  "end_time": "2025-09-09T17:38:07.679053",
  "duration_seconds": 77
}
```

## Question Types

### 1. Multiple Choice (`multiple_choice`)

- **Time Limit**: 30 seconds
- **Input**: Mouse click (A, B, C, D)
- **Answer Format**: Single letter ("A", "B", "C", "D")
- **Features**: Automatic scoring, LLM provides explanations

### 2. Read Aloud (`read_aloud`)

- **Time Limit**: 15 seconds
- **Input**: Voice recording
- **Answer Format**: Audio data (transcribed automatically)
- **Features**: Text matching accuracy, pronunciation feedback

### 3. Quick Response (`quick_response`)

- **Time Limit**: 15 seconds
- **Input**: Voice recording
- **Answer Format**: Audio data (transcribed automatically)
- **Features**: LLM grades relevance and grammar

### 4. Translation (`translation`)

- **Time Limit**: 30 seconds
- **Input**: Voice recording
- **Answer Format**: Audio data (transcribed automatically)
- **Features**: LLM grades translation accuracy

## Audio File Handling

### TTS (Text-to-Speech) Audio

- Generated at session start for all questions with `tts` field
- Cached to avoid repeated API calls
- File path provided in question response
- Format: MP3

### Student Audio Recordings

- Saved during answer submission
- Organized by session ID and question ID
- Format: WebM
- Automatically transcribed using STT

## Error Handling

### Common Error Responses

#### 400 Bad Request

```json
{
  "detail": "Session not found: session_id"
}
```

#### 404 Not Found

```json
{
  "detail": "No more questions available"
}
```

#### 500 Internal Server Error

```json
{
  "detail": "Error starting session: error details"
}
```

## Frontend Implementation Guide

### 1. Exam Flow

1. **Start**: Call `/session/start` with exam file path
2. **Questions**: Loop through questions using `/session/{id}/question`
3. **Answers**: Submit answers using `/session/{id}/answer`
4. **Results**: Get final results using `/session/{id}/results`

### 2. Audio Integration

- **TTS Audio**: Use provided `audio_file_path` to play question audio
- **Voice Recording**: Record audio and send as blob in `audio_data` field
- **Audio Formats**: TTS = MP3, Student recordings = WebM

### 3. Timer Implementation

- Use `time_limit` from question data
- Start timer when question is displayed
- Auto-submit when timer expires

### 4. State Management

- Store `session_id` for all subsequent calls
- Track `question_index` to know current position
- Use `is_last` to determine when to show results

### 5. Error Handling

- Handle 400/404 errors gracefully
- Show user-friendly error messages
- Implement retry logic for network issues

## Example Implementation

```javascript
// Start exam
async function startExam(examFile) {
  const response = await fetch('/session/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exam_file_path: examFile })
  });
  const session = await response.json();
  return session.session_id;
}

// Get question
async function getQuestion(sessionId) {
  const response = await fetch(`/session/${sessionId}/question`);
  const data = await response.json();
  return data;
}

// Submit answer
async function submitAnswer(sessionId, answer) {
  const response = await fetch(`/session/${sessionId}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(answer)
  });
  return await response.json();
}

// Get results
async function getResults(sessionId) {
  const response = await fetch(`/session/${sessionId}/results`);
  return await response.json();
}
```

## Testing Endpoints

### Health Check

**GET** `/health`

```json
{
  "status": "healthy"
}
```

### Root Endpoint

**GET** `/`

```json
{
  "message": "Echo - LLM-Powered Exam Platform API"
}
```
