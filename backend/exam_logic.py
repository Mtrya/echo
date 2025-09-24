import yaml
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
try:
    from .models import (
        Question, Exam, SectionInstruction, GradingInput, GradingResult, TTSInput, AudioGenerationStatus,
        SessionStartRequest, SessionResponse, QuestionResponse, AnswerSubmission,
        AnswerResponse, FinalResult
    )
    from .omni_client import OmniClient
except ImportError:
    from models import (
        Question, Exam, SectionInstruction, GradingInput, GradingResult, TTSInput, AudioGenerationStatus,
        SessionStartRequest, SessionResponse, QuestionResponse, AnswerSubmission,
        AnswerResponse, FinalResult
    )
    from omni_client import OmniClient


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
        self.seen_sections = set()  # Track which sections we've seen
        self.processing_tasks = set()  # Track active async processing tasks

    def is_completed(self) -> bool:
        return self.current_question_index >= len(self.exam.questions)

    def get_current_question(self) -> Optional[Question]:
        if self.is_completed():
            return None
        return self.exam.questions[self.current_question_index]

    def get_previous_question(self) -> Optional[Question]:
        if self.current_question_index <= 0:
            return None
        return self.exam.questions[self.current_question_index - 1]

    def is_first_in_section(self) -> bool:
        current_question = self.get_current_question()
        if not current_question:
            return False

        # Check if we've already seen this section type
        if current_question.type in self.seen_sections:
            return False

        # First question ever
        if self.current_question_index == 0:
            self.mark_section_seen(current_question.type)
            return True

        # Check if current question type is different from previous
        previous_question = self.get_previous_question()
        if previous_question and current_question.type != previous_question.type:
            self.mark_section_seen(current_question.type)
            return True

        return False

    def mark_section_seen(self, question_type: str):
        self.seen_sections.add(question_type)

    def advance_to_next_question(self):
        self.current_question_index += 1

    def add_result(self, result: GradingResult):
        self.results.append(result)

    def complete(self):
        self.end_time = datetime.now()

    def add_processing_task(self, task_id: str):
        """Add a processing task to track"""
        self.processing_tasks.add(task_id)

    def remove_processing_task(self, task_id: str):
        """Remove a completed processing task"""
        self.processing_tasks.discard(task_id)

    def is_processing(self) -> bool:
        """Check if there are any active processing tasks"""
        return len(self.processing_tasks) > 0


class ExamManager:
    def __init__(self):
        self.sessions: Dict[str, ExamSession] = {}
        self.omni_client = OmniClient()
    
    async def start_session(self, request: SessionStartRequest) -> SessionResponse:
        """Start a new exam session"""
        # Load exam from YAML file
        exam = await self._load_exam_from_yaml(request.exam_file_path)
        
        # Create session
        session_id = str(uuid.uuid4())
        session = ExamSession(session_id, request.exam_file_path, exam)
        self.sessions[session_id] = session

        # Start audio files generation in background (don't wait for it)
        asyncio.create_task(self._prepare_audio_files(session))

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

        # Add instruction info if this is the first question in a section
        instruction = None
        instruct_audio_file_path = None

        if session.is_first_in_section():
            instruction = session.exam.section_instructions.get(question.type)
            instruct_audio_file_path = session.audio_files.get(f"section_{question.type}")

        return QuestionResponse(
            question=question,
            audio_file_path=audio_file_path,
            question_index=session.current_question_index,
            is_last=session.current_question_index == len(session.exam.questions) - 1,
            instruction=instruction,
            instruct_audio_file_path=instruct_audio_file_path,
        )
    
    async def submit_answer(self, session_id: str, answer_data: AnswerSubmission) -> AnswerResponse:
        """Submit answer and process asynchronously"""
        session = self._get_session(session_id)
        question = session.get_current_question()

        if question is None:
            raise ValueError("No current question to answer")

        # Check if this is the last question
        is_last_question = session.current_question_index == len(session.exam.questions) - 1

        # Start async processing (don't wait for it)
        asyncio.create_task(self._process_answer_async(session, question, answer_data))

        # Only advance to next question if it's not the last one
        if not is_last_question:
            session.advance_to_next_question()
        else:
            # If it's the last question, complete the session
            session.complete()

        return AnswerResponse(
            message="Answer submitted and processing",
            question_index=session.current_question_index,
            processing=True
        )
    
    async def get_audio_generation_status(self, session_id: str) -> AudioGenerationStatus:
        """Get the audio generation status for a session"""
        session = self._get_session(session_id)

        # Check audio generation status
        audio_generation = "completed" if session.audio_files else "generating"

        return AudioGenerationStatus(
            audio_generation=audio_generation,
            session_id=session_id
        )

    async def get_final_results(self, session_id: str) -> FinalResult:
        """Get final exam results with processed questions and completion status"""
        session = self._get_session(session_id)

        # Calculate results for processed questions only
        processed_results = [r for r in session.results if r.score is not None]
        total_score = sum(result.score for result in processed_results)
        max_score = len(processed_results)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        # Prepare question results for processed questions only
        question_results = []
        processed_count = 0

        for i, (question, result) in enumerate(zip(session.exam.questions, session.results)):
            if result.score is not None:  # Question has been processed
                processed_count += 1
                question_result = {
                    "question_index": i,
                    "question_id": question.id,
                    "question_type": question.type,
                    "question_text": question.text,
                    "score": result.score,
                    "feedback": result.feedback,
                    "explanation": result.explanation,
                    "suggested_answer": result.suggested_answer
                }

                # Add student answer info for multiple choice
                if question.type == "multiple_choice" and hasattr(result, 'student_answer'):
                    question_result["student_answer"] = result.student_answer
                    question_result["reference_answer"] = question.reference_answer

                # Add audio file path for audio questions
                if question.type in ["read_aloud", "quick_response", "translation"]:
                    question_result["student_audio_path"] = getattr(result, 'student_audio_path', None)

                question_results.append(question_result)

        # Check if all questions are processed
        all_processed = processed_count == len(session.exam.questions)

        # Use current time if exam not completed
        end_time = session.end_time if session.end_time else datetime.now()

        return FinalResult(
            session_id=session_id,
            exam_title=session.exam.title,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            question_results=question_results,
            start_time=session.start_time,
            end_time=end_time,
            duration_seconds=int((end_time - session.start_time).total_seconds()),
            all_processed=all_processed,
            processed_count=processed_count,
            total_questions=len(session.exam.questions)
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

        # Load section instructions
        section_instructions = {}
        for section_type, instruction_data in exam_data.get('section_instructions', {}).items():
            section_instructions[section_type] = SectionInstruction(
                text=instruction_data['text'],
                tts=instruction_data.get('tts')
            )

        # Load questions (without tts field - it's now in section_instructions)
        questions = []
        original_indices = {}  # Store original positions for stable sorting
        for i, q_data in enumerate(exam_data.get('questions', [])):
            question = Question(
                id=q_data['id'],
                type=q_data['type'],
                text=q_data['text'],
                options=q_data.get('options'),
                reference_answer=q_data.get('reference_answer'),
                time_limit=q_data.get('time_limit', 30)
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
            section_instructions=section_instructions,
            questions=questions
        )
    
    async def _prepare_audio_files(self, session: ExamSession):
        """Prepare TTS audio files for section instructions and questions with TTS"""

        audio_files = {}

        # Generate audio for section instructions
        for section_type, instruction in session.exam.section_instructions.items():
            if instruction.tts:
                try:
                    tts_request = TTSInput(text=instruction.tts, voice="Elias")
                    tts_result = await self.omni_client.text_to_speech(tts_request)
                    # Store with section_type prefix to avoid conflicts
                    audio_files[f"section_{section_type}"] = tts_result.audio_file_path
                    print(f"Generated audio for {section_type} instruction: {tts_result.audio_file_path}")
                except Exception as e:
                    print(f"Failed to generate audio for {section_type} instruction: {e}")

        # Generate audio for questions that need TTS (quick_response questions have text=TTS)
        for question in session.exam.questions:
            if question.type == 'quick_response':
                # For quick response, the text is the question audio
                try:
                    tts_request = TTSInput(text=question.text, voice="Cherry")
                    tts_result = await self.omni_client.text_to_speech(tts_request)
                    audio_files[question.id] = tts_result.audio_file_path
                    print(f"Generated audio for quick_response question {question.id}: {tts_result.audio_file_path}")
                except Exception as e:
                    print(f"Failed to generate audio for question {question.id}: {e}")

        session.audio_files = audio_files
    
    async def _process_answer_async(self, session: ExamSession, question: Question, answer_data: AnswerSubmission):
        """Process answer asynchronously"""
        task_id = f"{question.id}_{datetime.now().strftime('%H%M%S')}"
        session.add_processing_task(task_id)

        try:
            # Grade the answer using unified omni client
            grading_input = GradingInput(
                session_id=session.session_id,
                question_id=question.id,
                question_type=question.type,
                student_answer_text=answer_data.answer_text,
                student_answer_audio=answer_data.audio_data,
                reference_answer=question.reference_answer,
                question_text=question.text,
                options=question.options
            )

            grading_result = await self.omni_client.grade_answer(grading_input)
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
        finally:
            # Always remove the task when done
            session.remove_processing_task(task_id)
    
    def _get_session(self, session_id: str) -> ExamSession:
        """Get session by ID"""
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")
        return self.sessions[session_id]
