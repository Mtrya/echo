from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Core Models
class Question(BaseModel):
    id: str
    type: str  # "multiple_choice", "read_aloud", "quick_response", "translation"
    text: str
    options: Optional[List[str]] = None
    reference_answer: Optional[str] = None
    time_limit: int = 30

class SectionInstruction(BaseModel):
    text: str
    tts: Optional[str] = None

class Exam(BaseModel):
    title: str
    description: str
    section_instructions: Dict[str, SectionInstruction]  # Key: question type, value: instruction
    questions: List[Question]

# Omni Client Processing Models
class GradingInput(BaseModel):
    session_id: str
    question_id: str
    question_type: str  # "multiple_choice", "read_aloud", "quick_response", "translation"
    student_answer_text: Optional[str] = None
    student_answer_audio: Optional[str] = None
    reference_answer: Optional[str] = None
    question_text: str
    options: Optional[List[str]] = None # ["A:6","B:7","C:8","D:9"], for multiple choice

class GradingResult(BaseModel):
    score: float
    feedback: str
    explanation: str
    suggested_answer: Optional[str] = None  # For quick response and translation questions

class TTSInput(BaseModel):
    text: str
    voice: str = "Cherry"

class TTSOutput(BaseModel):
    text: str
    audio_file_path: str  # path to saved audio file (.mp3)

# Session Management Models
class SessionStartRequest(BaseModel):
    exam_file_path: str

class SessionResponse(BaseModel):
    session_id: str
    exam_title: str
    total_questions: int
    message: str

class QuestionResponse(BaseModel):
    question: Question
    audio_file_path: Optional[str] = None
    question_index: int
    is_last: bool
    instruction: Optional[SectionInstruction] = None
    instruct_audio_file_path: Optional[str] = None

class AnswerSubmission(BaseModel):
    answer_text: Optional[str] = None
    audio_data: Optional[str] = None  # base64-encoded audio data

class AnswerResponse(BaseModel):
    message: str
    question_index: int
    processing: bool

class FinalResult(BaseModel):
    session_id: str
    exam_title: str
    total_score: float
    max_score: float
    percentage: float
    question_results: List[dict]
    start_time: datetime
    end_time: datetime
    duration_seconds: int

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