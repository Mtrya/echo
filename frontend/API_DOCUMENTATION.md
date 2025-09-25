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

### 1. Root Endpoint

**GET** `/`

Get API information and available endpoints.

**Response:**

```json
{
  "message": "Echo - LLM-Powered Exam Platform API",
  "version": "1.0.0",
  "docs": "/docs",
  "endpoints": {
    "exams": "/exams/list",
    "session": "/session/start",
    "health": "/health"
  }
}
```

### 2. Health Check

**GET** `/health`

Check if the API is running properly.

**Response:**

```json
{
  "status": "healthy"
}
```

### 3. List Available Exams

**GET** `/exams/list`

List all available exam YAML files.

**Response:**

```json
{
  "exams": ["sample_test.yaml", "comprehensive_test.yaml", "exam-2099.yaml"]
}
```

### 4. Start Exam Session

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

### 5. Get Current Question

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
  "audio_file_path": "tts/bea39faa84a9823d21818aa1e104ecdd.mp3",
  "question_index": 0,
  "is_last": false,
  "instruction": {
    "text": "This is a multiple choice section. Please listen to each question and select the correct answer.",
    "tts": "This is a multiple choice section. Please listen to each question and select the correct answer."
  },
  "instruction_audio_file_path": "tts/f4496987dabd9f56fa5c336c2ab63ff0.mp3"
}
```

### 6. Submit Answer

**POST** `/session/{session_id}/answer`

Submit an answer for the current question. Processing happens asynchronously.

**Request:**

```json
{
  "answer_text": "A",  // For text-based answers (optional)
  "student_answer_audio": "base64-encoded-audio-data"  // For voice answers (optional)
}
```

**Note:** Audio data should be base64-encoded and sent as a string in the JSON payload. The backend will automatically decode it to bytes for processing. Only one of `answer_text` or `student_answer_audio` should be provided based on question type.

**Response:**

```json
{
  "message": "Answer submitted and processing",
  "question_index": 0,
  "processing": true
}
```

### 7. Get Audio Generation Status

**GET** `/session/{session_id}/audio-status`

Get the audio generation status for a session.

**Response:**

```json
{
  "audio_generation": "completed",
  "session_id": "a2a15ac2-f38b-406c-bd9b-ed53f8ad1d26"
}
```

**Status Values:**

- `audio_generation`: "generating" | "completed"

### 8. Get Final Results

**GET** `/session/{session_id}/results`

Get the final exam results with progressive processing status.

**Response:**

```json
{
  "session_id": "a2a15ac2-f38b-406c-bd9b-ed53f8ad1d26",
  "exam_title": "Comprehensive English and Math Exam",
  "total_score": 18.5,
  "total_questions": 20,
  "processed_count": 15,
  "all_processed": false,
  "duration_seconds": 77,
  "question_results": [
    {
      "question_index": 0,
      "question_id": "q1",
      "question_type": "multiple_choice",
      "question_text": "What is 2+2?",
      "score": 5.0,
      "feedback": "Excellent work! You got this math question right!",
      "explanation": "The question asks what is 2+2. The correct answer is A: 4, which you selected correctly.",
      "suggested_answer": null,
      "student_answer": "A",
      "reference_answer": "A"
    },
    {
      "question_index": 1,
      "question_id": "q2",
      "question_type": "read_aloud",
      "question_text": "Read this sentence aloud: The cat is sleeping on the mat.",
      "score": 4.5,
      "feedback": "Great pronunciation! You read the sentence very clearly.",
      "explanation": "You pronounced all words correctly. The sentence was: The cat is sleeping on the mat.",
      "suggested_answer": null,
      "student_audio_path": "student_answers/session_id/q2_1234567890.mp3"
    },
    {
      "question_index": 2,
      "question_id": "q3",
      "question_type": "quick_response",
      "question_text": "What color is the sky on a clear day?",
      "score": 3.0,
      "feedback": "Good attempt! Your answer was mostly correct.",
      "explanation": "You said 'blue sky' which is correct. The sky is blue on clear days.",
      "suggested_answer": "The sky is blue.",
      "student_audio_path": "student_answers/session_id/q3_1234567890.mp3"
    },
    {
      "question_index": 3,
      "question_id": "q4",
      "question_type": "translation",
      "question_text": "Translate to English: 我喜欢学习数学",
      "score": 4.0,
      "feedback": "Very good translation! You captured the meaning well.",
      "explanation": "You translated '我喜欢学习数学' as 'I like to study math' which is accurate.",
      "suggested_answer": "I like to study math.",
      "student_audio_path": "student_answers/session_id/q4_1234567890.mp3"
    }
  ]
}
```

**Progressive Processing:**

- `all_processed`: `false` while questions are still being processed
- `processed_count`: Number of questions that have been graded
- `question_results`: Only includes processed questions

### 9. File Conversion

**POST** `/convert/file`

Convert file to exam format using qwen3-vl-plus.

**Request:**

```json
{
  "file_path": "path/to/document",
  "output_file": "output_exam.yaml"
}
```

**Response:**

```json
{
  "exam_file_path": "converted_exam.yaml",
  "message": "File converted successfully"
}
```

### 10. Rename Exam File

**POST** `/rename-exam`

Rename an exam file in the exams directory.

**Request:**

```json
{
  "old_name": "exam-2099.yaml",
  "new_name": "new-exam-name.yaml"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Exam file renamed successfully from 'exam-2099.yaml' to 'new-exam-name.yaml'"
}
```

## Question Types

### 1. Multiple Choice (`multiple_choice`)

- **Time Limit**: 30 seconds
- **Input**: Mouse click (A, B, C, D)
- **Answer Format**: Single letter ("A", "B", "C", "D")
- **Features**: Automatic scoring, LLM provides explanations
- **Response Data**: Includes `student_answer` and `reference_answer`

### 2. Read Aloud (`read_aloud`)

- **Time Limit**: 15 seconds
- **Input**: Voice recording
- **Answer Format**: Audio data (transcribed automatically)
- **Features**: Text matching accuracy, pronunciation feedback
- **Response Data**: Includes `student_audio_path` for playback

### 3. Quick Response (`quick_response`)

- **Time Limit**: 15 seconds
- **Input**: Voice recording
- **Answer Format**: Audio data (transcribed automatically)
- **Features**: LLM grades relevance and grammar
- **Response Data**: Includes `student_audio_path` for playback

### 4. Translation (`translation`)

- **Time Limit**: 30 seconds
- **Input**: Voice recording
- **Answer Format**: Audio data (transcribed automatically)
- **Features**: LLM grades translation accuracy
- **Response Data**: Includes `student_audio_path` for playback

## Audio File Handling

### TTS (Text-to-Speech) Audio

- Generated at session start for all questions with `tts` field
- Cached in `audio_cache/tts/` directory
- Served via `/audio_cache/` endpoint
- Format: MP3
- File paths are relative to `audio_cache/`

### Student Audio Recordings

- Saved during answer submission in `audio_cache/student_answers/`
- Organized by session ID and question ID with timestamp
- Format: MP3 (converted from WebM)
- Served via `/audio_cache/` endpoint
- File paths: `student_answers/{session_id}/{question_id}_{timestamp}.mp3`

## Static Files

### Audio Cache

- **GET** `/audio_cache/{file_path}`
- Serves cached TTS audio and student recordings
- Example: `/audio_cache/tts/question_1.mp3`
- Example: `/audio_cache/student_answers/session_id/q1_1234567890.mp3`

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
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "details": "Error details"
}
```

## Frontend Implementation Guide

### 1. Exam Flow

1. **Start**: Call `/session/start` with exam file path
2. **Questions**: Loop through questions using `/session/{id}/question`
3. **Answers**: Submit answers using `/session/{id}/answer`
4. **Results**: Get final results using `/session/{id}/results` (supports polling)

### 2. Audio Integration

- **TTS Audio**: Use provided `audio_file_path` to play question audio
- **Voice Recording**: Record audio and send as base64 in `student_answer_audio` field
- **Audio Playback**: Use `/audio_cache/{path}` for student answer playback
- **Audio Formats**: TTS = MP3, Student recordings = MP3

### 3. Timer Implementation

- Use `time_limit` from question data
- Start timer when question is displayed
- Auto-submit when timer expires

### 4. State Management

- Store `session_id` for all subsequent calls
- Track `question_index` to know current position
- Use `is_last` to determine when to show results
- Poll `/results` endpoint for progressive updates

### 5. Results Display

- Show "Processing X out of N questions" while `all_processed` is false
- Display questions progressively as they're processed
- Add audio playback buttons for questions with `student_audio_path`
- Show student vs reference answers for multiple choice
- Include AI disclaimer for generated feedback

### 6. Error Handling

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

// Get results with polling
async function getResults(sessionId) {
  const response = await fetch(`/session/${sessionId}/results`);
  return await response.json();
}

// Play student audio
function playStudentAudio(audioPath) {
  const audio = new Audio(`/audio_cache/${audioPath}`);
  audio.play();
}
```

## Environment Variables

The following environment variables are required:

- `SILICONFLOW_API_KEY`: API key for SiliconFlow services

## Testing Endpoints

### Interactive Documentation

**GET** `/docs`

Interactive Swagger UI documentation for testing API endpoints.

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
  "message": "Echo - LLM-Powered Exam Platform API",
  "version": "1.0.0",
  "docs": "/docs",
  "endpoints": {
    "exams": "/exams/list",
    "session": "/session/start",
    "health": "/health"
  }
}
```
