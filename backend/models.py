from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Core Models
class Question(BaseModel):
    id: str
    type: str  # "multiple_choice", "read_aloud", "quick_response", "translation"
    text: str
    options: Optional[List[str]] = None # only for multiple-choice questions
    reference_answer: Optional[str] = None # only for multiple-choice questions
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
    student_answer_audio: Optional[str] = None # base64 string of student answer audio (mp3 format)
    reference_answer: Optional[str] = None
    question_text: str
    options: Optional[List[str]] = None # ["A:6","B:7","C:8","D:9"], for multiple choice

class GradingResult(BaseModel):
    score: float
    feedback: str
    explanation: str
    suggested_answer: Optional[str] = None  # For quick response and translation questions
    student_answer: Optional[str] = None  # For multiple choice questions
    student_audio_path: Optional[str] = None  # Path to cached student audio file

class TTSInput(BaseModel):
    text: str
    voice: str = "Cherry"

class TTSResult(BaseModel):
    text: str
    audio_file_path: str  # path to saved audio file (.mp3)

class ConversionInput(BaseModel):
    texts: Optional[List[str]]
    images: Optional[List[str]] # list of base64 image strings for input images, must be png format

class ConversionResult(BaseModel):
    success: bool
    message: str
    extracted_questions: List[Question]

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
    all_processed: bool
    processed_count: int
    total_questions: int

class AudioGenerationStatus(BaseModel):
    audio_generation: str  # "generating", "completed"
    session_id: str

class FileConversionRequest(BaseModel):
    filenames: List[str]
    file_contents: List[str]  # base64 encoded

class FileConversionResponse(BaseModel):
    success: bool
    message: str
    extracted_questions: List[Question]
    yaml_output: Optional[str] = None
    output_filename: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None