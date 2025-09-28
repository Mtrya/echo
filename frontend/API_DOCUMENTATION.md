# Echo Exam Platform - API Documentation

## Base URL

```base url
http://localhost:8000
```

## API Endpoints

### 1. Root Endpoint

**GET** `/`

API information.

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

Check API status.

**Response:**

```json
{
  "status": "healthy"
}
```

### 3. API Key Status

**GET** `/api-key-status`

Check API key configuration.

**Response:**

```json
{
  "has_api_key": true,
  "message": "API key configured"
}
```

### 4. List Available Exams

**GET** `/exams/list?include_completed=true`

List available exam files.

**Response:**

```json
{
  "exams": ["exam-2098.yaml", "exam-2099.yaml", "test.yaml"]
}
```

### 5. Get Completed Exams

**GET** `/exams/completed`

Get completed exam files.

**Response:**

```json
{
  "completed_exams": ["exam-2098.yaml"]
}
```

### 6. Start Exam Session

**POST** `/session/start`

Start new exam session.

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

### 7. Get Current Question

**GET** `/session/{session_id}/question`

Get current question with audio.

**Response:**

```json
{
  "question": {
    "id": "q1",
    "type": "multiple_choice",
    "text": "What is 2+2?",
    "options": ["A: 4", "B: 5", "C: 6", "D: 7"],
    "reference_answer": "A"
  },
  "time_limit": 30,
  "audio_file_path": "tts/bea39faa84a9823d21818aa1e104ecdd.mp3",
  "question_index": 0,
  "is_last": false,
  "instruction": {
    "text": "This is a multiple choice section.",
    "tts": "This is a multiple choice section."
  },
  "instruction_audio_file_path": "tts/f4496987dabd9f56fa5c336c2ab63ff0.mp3"
}
```

### 8. Submit Answer

**POST** `/session/{session_id}/answer`

Submit answer for current question.

**Request:**

```json
{
  "answer_text": "A",
  "student_answer_audio": "base64-encoded-audio-data"
}
```

**Response:**

```json
{
  "message": "Answer submitted and processing",
  "question_index": 0,
  "processing": true
}
```

### 9. Get Audio Generation Status

**GET** `/session/{session_id}/audio-status`

Check audio generation progress.

**Response:**

```json
{
  "audio_generation": "completed",
  "session_id": "a2a15ac2-f38b-406c-bd9b-ed53f8ad1d26"
}
```

### 10. Get Final Results

**GET** `/session/{session_id}/results`

Get exam results with progressive processing.

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
      "feedback": "Excellent work!",
      "explanation": "The correct answer is A: 4.",
      "student_answer": "A",
      "reference_answer": "A"
    }
  ]
}
```

### 11. File Conversion

**POST** `/convert/file`

Convert files to exam format.

**Request:**

```json
{
  "filenames": ["document.pdf", "image.png"],
  "file_contents": ["base64-encoded-content-1", "base64-encoded-content-2"]
}
```

**Response:**

```json
{
  "success": true,
  "message": "Successfully extracted 15 questions",
  "extracted_questions": [...],
  "yaml_output": "exam:\n  title: 'Generated Exam'\n  questions: [...]",
  "output_filename": "generated_exam_20241225_143022.yaml"
}
```

### 12. Rename Exam File

**POST** `/rename-exam`

Rename exam file.

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
  "message": "Exam file renamed successfully"
}
```

### 13. Delete Exam File

**POST** `/delete-exam`

Delete exam file.

**Request:**

```json
{
  "exam_filename": "exam-2099.yaml"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Exam file deleted successfully"
}
```

### 14. Settings Management

**GET** `/settings`

Get configuration.

**Response:**

```json
{
  "success": true,
  "config": {
    "api": {"dashscope_key": "your-api-key"},
    "models": {
      "omni_model": "qwen3-omni-flash",
      "vision_model": "qwen3-vl-plus"
    },
    "time_limits": {
      "multiple_choice": 30,
      "read_aloud": 15,
      "quick_response": 15,
      "translation": 30
    },
    "ui": {"theme": "green"}
  },
  "options": {
    "omni_models": ["qwen3-omni-flash", "qwen-omni-turbo"],
    "vision_models": ["qwen3-vl-plus", "qwen3-vl-235b-a22b-thinking"],
    "voice_options": ["Cherry", "Ethan", "Aria"]
  }
}
```

**POST** `/settings`

Update configuration.

**Request:**

```json
{
  "config": {
    "api": {"dashscope_key": "new-api-key"},
    "models": {"omni_model": "qwen3-omni-flash"},
    "time_limits": {"multiple_choice": 30},
    "ui": {"theme": "blue"}
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "Settings updated successfully"
}
```

### 15. Test API Connection

**POST** `/test-api`

Test API credentials.

**Request:**

```json
{
  "api_key": "your-api-key-to-test"
}
```

**Response:**

```json
{
  "success": true,
  "message": "API connection successful",
  "model_info": {
    "model": "qwen3-omni-flash",
    "capabilities": ["text", "audio", "vision"]
  }
}
```

### 16. Get Available Voices

**GET** `/voices/{omni_model}`

Get voices for model.

**Response:**

```json
{
  "success": true,
  "voices": ["Cherry", "Ethan", "Aria", "Oliver", "Sophia", "Liam"]
}
```

## Question Types

### Multiple Choice (`multiple_choice`)

- Time: 30s (configurable)
- Input: Mouse click (A, B, C, D)
- Response: `student_answer`, `reference_answer`

### Read Aloud (`read_aloud`)

- Time: 15s (configurable)
- Input: Voice recording
- Response: `student_audio_path`

### Quick Response (`quick_response`)

- Time: 15s (configurable)
- Input: Voice recording
- Response: `student_audio_path`

### Translation (`translation`)

- Time: 30s (configurable)
- Input: Voice recording
- Response: `student_audio_path`

## Static Files

### Audio Cache

**GET** `/audio_cache/{file_path}`

Serve TTS audio and student recordings.

Examples:

- `/audio_cache/tts/question_1.mp3`
- `/audio_cache/student_answers/session_id/q1_1234567890.mp3`

## Interactive Documentation

**GET** `/docs`

Swagger UI for testing API endpoints.
