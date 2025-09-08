from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Core Models
class Question(BaseModel):
    id: str
    type: str  # "multiple_choice", "read_aloud", "quick_response", "translation"
    text: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    time_limit: int = 30
    difficulty: str = "medium"

class Exam(BaseModel):
    title: str
    description: str
    questions: List[Question]
    total_questions: int

# API Request/Response Models
class GradeRequest(BaseModel):
    question_id: str
    question_type: str  # "multiple_choice", "read_aloud", "quick_response", "translation"
    student_answer: str
    correct_answer: Optional[str] = None
    question_text: str
    options: Optional[List[str]] = None # ["A:6","B:7","C:8","D:9"], for multiple choice

class GradeResponse(BaseModel):
    score: float
    feedback: str
    explanation: str
    is_correct: bool
    suggested_answer: Optional[str] = None  # For quick response and translation questions

# Speech Processing Models
class SpeechToTextResponse(BaseModel):
    transcription: str
    confidence: float
    language: str

class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "female"
    language: str = "en"
    speed: float = 1.0

class TextToSpeechResponse(BaseModel):
    audio_data: str  # base64 encoded audio
    duration: float
    text: str

class SpeechToTextRequest(BaseModel):
    audio_data: str  # base64 encoded audio
    language: str = "en"

class SpeechToTextResponse(BaseModel):
    transcription: str
    confidence: float
    language: str

class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "female"
    language: str = "en"
    speed: float = 1.0

class TextToSpeechResponse(BaseModel):
    audio_data: str  # base64 encoded audio
    duration: float
    text: str

# Session Management Models
class SessionStartRequest(BaseModel):
    exam_filename: str
    student_name: Optional[str] = "Student"

class SessionResponse(BaseModel):
    session_id: str
    exam_title: str
    total_questions: int
    started_at: str

class AnswerSubmission(BaseModel):
    question_id: str
    student_answer: str
    score: float
    feedback: str
    time_taken: Optional[int] = None

class SessionResults(BaseModel):
    session_id: str
    student_name: str
    total_score: float
    total_questions: int
    percentage: float
    answers: List[AnswerSubmission]
    completed_at: str

# File Conversion Models
class DocxConversionRequest(BaseModel):
    filename: str
    output_format: str = "yaml"

class DocxConversionResponse(BaseModel):
    success: bool
    output_filename: str
    questions_extracted: int
    message: str

# Error Models
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None