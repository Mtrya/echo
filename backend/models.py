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

# API Processing Models
class GradingInput(BaseModel):
    question_type: str  # "multiple_choice", "read_aloud", "quick_response", "translation"
    student_answer: str
    reference_answer: Optional[str] = None
    question_text: str
    options: Optional[List[str]] = None # ["A:6","B:7","C:8","D:9"], for multiple choice

class GradingResult(BaseModel):
    score: float
    feedback: str
    explanation: str
    suggested_answer: Optional[str] = None  # For quick response and translation questions

# Speech Processing Models
class TTSInput(BaseModel):
    text: str
    voice: str = "female" # female -> claire; male -> charles

class TTSOutput(BaseModel):
    text: str
    audio_file_path: str  # path to saved audio file (.mp3)

class STTInput(BaseModel):
    audio_data: bytes # direct binary data
    session_id: str
    question_id: str

class STTOutput(BaseModel):
    text: str
    audio_file_path: str # path to saved audio file (.webm)

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
    audio_data: Optional[bytes] = None

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