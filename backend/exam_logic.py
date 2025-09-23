import yaml
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
try:
    from .models import (
        Question, Exam, GradingInput, GradingResult, TTSInput, STTInput,
        SessionStartRequest, SessionResponse, QuestionResponse, AnswerSubmission,
        AnswerResponse, FinalResult
    )
    from .llm_client import LLMClient
    from .speech_client import SpeechClient
except ImportError:
    from models import (
        Question, Exam, GradingInput, GradingResult, TTSInput, STTInput,
        SessionStartRequest, SessionResponse, QuestionResponse, AnswerSubmission,
        AnswerResponse, FinalResult
    )
    from llm_client import LLMClient
    from speech_client import SpeechClient


class ExamSession:
    def __init__(self, session_id: str, exam_file_path: str, exam: Exam):
        self.session_id = session_id
        self.exam_file_path = exam_file_path
        self.exam = exam
        self.current_question_index = 0
        self.results = []
        self.start_time = datetime.now()
        self.end_time = None
        self.audio_files = {}  # question_id -> audio_file_path
        
    def is_completed(self) -> bool:
        return self.current_question_index >= len(self.exam.questions)
    
    def get_current_question(self) -> Optional[Question]:
        if self.is_completed():
            return None
        return self.exam.questions[self.current_question_index]
    
    def advance_to_next_question(self):
        self.current_question_index += 1
    
    def add_result(self, result: GradingResult):
        self.results.append(result)
    
    def complete(self):
        self.end_time = datetime.now()


class ExamManager:
    def __init__(self):
        self.sessions: Dict[str, ExamSession] = {}
        self.llm_client = LLMClient()
        self.speech_client = SpeechClient()
    
    async def start_session(self, request: SessionStartRequest) -> SessionResponse:
        """Start a new exam session"""
        # Load exam from YAML file
        exam = await self._load_exam_from_yaml(request.exam_file_path)
        
        # Create session
        session_id = str(uuid.uuid4())
        session = ExamSession(session_id, request.exam_file_path, exam)
        self.sessions[session_id] = session
        
        # Prepare audio files for all questions
        await self._prepare_audio_files(session)
        
        return SessionResponse(
            session_id=session_id,
            exam_title=exam.title,
            total_questions=len(exam.questions),
            message=f"Exam session started with {len(exam.questions)} questions"
        )
    
    async def get_current_question(self, session_id: str) -> QuestionResponse:
        """Get current question for a session"""
        session = self._get_session(session_id)
        question = session.get_current_question()
        
        if question is None:
            raise ValueError("No more questions available")
        
        audio_file_path = session.audio_files.get(question.id)
        
        return QuestionResponse(
            question=question,
            audio_file_path=audio_file_path,
            question_index=session.current_question_index,
            is_last=session.current_question_index == len(session.exam.questions) - 1
        )
    
    async def submit_answer(self, session_id: str, answer_data: AnswerSubmission) -> AnswerResponse:
        """Submit answer and process asynchronously"""
        session = self._get_session(session_id)
        question = session.get_current_question()
        
        if question is None:
            raise ValueError("No current question to answer")
        
        # Start async processing (don't wait for it)
        asyncio.create_task(self._process_answer_async(session, question, answer_data))
        
        # Advance to next question immediately
        session.advance_to_next_question()
        
        # Check if exam is completed
        if session.is_completed():
            session.complete()
        
        return AnswerResponse(
            message="Answer submitted and processing",
            question_index=session.current_question_index - 1,
            processing=True
        )
    
    async def get_final_results(self, session_id: str) -> FinalResult:
        """Get final exam results"""
        session = self._get_session(session_id)
        
        if not session.is_completed():
            raise ValueError("Exam not completed")
        
        total_score = sum(result.score for result in session.results)
        max_score = len(session.results)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Prepare question results
        question_results = []
        for i, (question, result) in enumerate(zip(session.exam.questions, session.results)):
            question_results.append({
                "question_index": i,
                "question_id": question.id,
                "question_type": question.type,
                "question_text": question.text,
                "score": result.score,
                "feedback": result.feedback,
                "explanation": result.explanation,
                "suggested_answer": result.suggested_answer
            })
        
        return FinalResult(
            session_id=session_id,
            exam_title=session.exam.title,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            question_results=question_results,
            start_time=session.start_time,
            end_time=session.end_time,
            duration_seconds=int((session.end_time - session.start_time).total_seconds())
        )
    
    async def list_available_exams(self) -> List[str]:
        """List all available exam files"""
        exam_dir = Path("../exams")
        if not exam_dir.exists():
            return []
        
        exam_files = []
        for file in exam_dir.glob("*.yaml"):
            exam_files.append(file.name)
        for file in exam_dir.glob("*.yml"):
            exam_files.append(file.name)
        
        return sorted(exam_files)
    
    async def _load_exam_from_yaml(self, file_path: str) -> Exam:
        """Load exam from YAML file and sort questions by type"""
        full_path = Path("../exams") / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"Exam file not found: {file_path}")

        with open(full_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if 'exam' in data:
            exam_data = data['exam']
        else:
            exam_data = data

        questions = []
        original_indices = {}  # Store original positions for stable sorting
        for i, q_data in enumerate(exam_data.get('questions', [])):
            question = Question(
                id=q_data['id'],
                type=q_data['type'],
                text=q_data['text'],
                options=q_data.get('options'),
                reference_answer=q_data.get('reference_answer'),
                time_limit=q_data.get('time_limit', 30),
                tts=q_data.get('tts')
            )
            questions.append(question)
            original_indices[question.id] = i  # Store original index

        # Sort questions by type in the specified order
        type_order = {
            'read_aloud': 0,
            'multiple_choice': 1,
            'quick_response': 2,
            'translation': 3
        }

        # Sort questions: first by type order, then by original order for same types
        questions.sort(key=lambda q: (type_order.get(q.type, 99), original_indices.get(q.id, 0)))

        print(f"Questions sorted by type order: {[q.type for q in questions]}")

        return Exam(
            title=exam_data['title'],
            description=exam_data.get('description', ''),
            questions=questions
        )
    
    async def _prepare_audio_files(self, session: ExamSession):
        """Prepare TTS audio files for all questions"""
        for question in session.exam.questions:
            if question.tts:
                try:
                    tts_request = TTSInput(text=question.tts, voice="female")
                    tts_result = await self.speech_client.text_to_speech(tts_request)
                    session.audio_files[question.id] = tts_result.audio_file_path
                except Exception as e:
                    print(f"Failed to generate audio for question {question.id}: {e}")
    
    async def _process_answer_async(self, session: ExamSession, question: Question, answer_data: AnswerSubmission):
        """Process answer asynchronously"""
        try:
            # Transcribe audio if needed
            answer_text = answer_data.answer_text
            if answer_data.audio_data and not answer_text:
                stt_request = STTInput(
                    audio_data=answer_data.audio_data,
                    session_id=session.session_id,
                    question_id=question.id
                )
                stt_result = await self.speech_client.speech_to_text(stt_request)
                answer_text = stt_result.text
            
            # Grade the answer
            grading_input = GradingInput(
                question_type=question.type,
                student_answer=answer_text or "",
                correct_answer=question.reference_answer,
                question_text=question.text,
                options=question.options
            )
            
            grading_result = await self.llm_client.grade_answer(grading_input)
            session.add_result(grading_result)
            
        except Exception as e:
            print(f"Error processing answer for question {question.id}: {e}")
            # Add a default result if processing fails
            default_result = GradingResult(
                score=0.0,
                feedback="Processing error",
                explanation=f"Unable to process answer: {str(e)}"
            )
            session.add_result(default_result)
    
    def _get_session(self, session_id: str) -> ExamSession:
        """Get session by ID"""
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")
        return self.sessions[session_id]
