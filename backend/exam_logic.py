import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
try:
    from .models import (
        Question, Exam, GradeRequest, GradeResponse, SessionResults,
        AnswerSubmission, SessionStartRequest, SessionResponse
    )
    from .llm_client import LLMClient
    from .speech_client import SpeechClient
except ImportError:
    from models import (
        Question, Exam, GradeRequest, GradeResponse, SessionResults,
        AnswerSubmission, SessionStartRequest, SessionResponse
    )
    from llm_client import LLMClient
    from speech_client import SpeechClient

class ExamManager:
    """Manages exam sessions, questions, and state"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.speech_client = SpeechClient()
        
        # Session storage - in memory for demo
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    async def load_exam_from_yaml(self, filename: str) -> Exam:
        """Load exam configuration from YAML file"""
        try:
            exam_path = Path("../exams") / filename
            if not exam_path.exists():
                raise FileNotFoundError(f"Exam file not found: {filename}")
            
            with open(exam_path, 'r', encoding='utf-8') as file:
                exam_data = yaml.safe_load(file)
            
            # Convert to our Exam model
            questions = []
            for i, q in enumerate(exam_data['exam']['questions']):
                question = Question(
                    id=str(i),
                    type=q['type'],
                    text=q['text'],
                    options=q.get('options'),
                    correct_answer=q.get('correct_answer'),
                    time_limit=q.get('time_limit', 30),
                    difficulty=q.get('difficulty', 'medium')
                )
                questions.append(question)
            
            exam = Exam(
                title=exam_data['exam']['title'],
                description=exam_data['exam']['description'],
                questions=questions,
                total_questions=len(questions)
            )
            
            return exam
            
        except Exception as e:
            raise ValueError(f"Error loading exam: {str(e)}")
    
    async def start_exam_session(self, request: SessionStartRequest) -> SessionResponse:
        """Start a new exam session"""
        try:
            # Load the exam
            exam = await self.load_exam_from_yaml(request.exam_filename)
            
            # Create session ID
            session_id = f"session_{len(self.sessions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Initialize session state
            self.sessions[session_id] = {
                "exam_filename": request.exam_filename,
                "student_name": request.student_name,
                "started_at": datetime.now().isoformat(),
                "current_question_index": 0,
                "questions": exam.questions,
                "answers": [],  # Will store AnswerSubmission objects
                "is_completed": False,
                "total_score": 0.0
            }
            
            return SessionResponse(
                session_id=session_id,
                exam_title=exam.title,
                total_questions=exam.total_questions,
                started_at=self.sessions[session_id]["started_at"]
            )
            
        except Exception as e:
            raise ValueError(f"Error starting session: {str(e)}")
    
    async def get_current_question(self, session_id: str) -> Optional[Question]:
        """Get the current question for a session"""
        if session_id not in self.sessions:
            return None
            
        session = self.sessions[session_id]
        if session["is_completed"]:
            return None
            
        current_index = session["current_question_index"]
        if current_index >= len(session["questions"]):
            return None
            
        return session["questions"][current_index]
    
    async def submit_answer(self, session_id: str, question_id: str, 
                          student_answer: str, audio_data: Optional[bytes] = None,
                          transcribed_text: Optional[str] = None) -> AnswerSubmission:
        """Submit an answer and store it with grading"""
        
        if session_id not in self.sessions:
            raise ValueError("Session not found")
            
        session = self.sessions[session_id]
        
        # Find the question
        question = None
        for q in session["questions"]:
            if q.id == question_id:
                question = q
                break
                
        if not question:
            raise ValueError("Question not found")
        
        # Grade the answer
        grade_request = GradeRequest(
            question_id=question_id,
            question_type=question.type,
            student_answer=student_answer,
            correct_answer=question.correct_answer,
            question_text=question.text
        )
        
        grade_response = self.llm_client.grade_answer(grade_request)
        
        # Create answer submission with all data
        answer_submission = AnswerSubmission(
            question_id=question_id,
            student_answer=student_answer,
            score=grade_response.score,
            feedback=grade_response.feedback,
            time_taken=None  # Could be calculated from timestamps
        )
        
        # Store additional data for non-multiple choice questions
        if question.type != "multiple_choice":
            answer_submission.audio_data = audio_data
            answer_submission.transcribed_text = transcribed_text
        
        # Add to session answers
        session["answers"].append(answer_submission)
        
        # Move to next question
        session["current_question_index"] += 1
        
        # Check if exam is completed
        if session["current_question_index"] >= len(session["questions"]):
            session["is_completed"] = True
            # Calculate final score
            total_score = sum(answer.score for answer in session["answers"])
            session["total_score"] = total_score
        
        return answer_submission
    
    async def get_session_results(self, session_id: str) -> SessionResults:
        """Get final results for a completed session"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
            
        session = self.sessions[session_id]
        
        if not session["is_completed"]:
            raise ValueError("Session not completed")
        
        total_score = sum(answer.score for answer in session["answers"])
        total_questions = len(session["answers"])
        percentage = (total_score / total_questions * 100) if total_questions > 0 else 0
        
        return SessionResults(
            session_id=session_id,
            student_name=session["student_name"],
            total_score=total_score,
            total_questions=total_questions,
            percentage=percentage,
            answers=session["answers"],
            completed_at=datetime.now().isoformat()
        )
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status"""
        if session_id not in self.sessions:
            raise ValueError("Session not found")
            
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "student_name": session["student_name"],
            "exam_filename": session["exam_filename"],
            "started_at": session["started_at"],
            "current_question_index": session["current_question_index"],
            "total_questions": len(session["questions"]),
            "answers_submitted": len(session["answers"]),
            "is_completed": session["is_completed"],
            "current_score": sum(answer.score for answer in session["answers"])
        }
    
    async def list_available_exams(self) -> List[str]:
        """List all available exam files"""
        try:
            exams_dir = Path("../exams")
            if not exams_dir.exists():
                return []
            
            exam_files = [f.name for f in exams_dir.glob("*.yaml") if f.is_file()]
            return exam_files
            
        except Exception as e:
            raise ValueError(f"Error listing exams: {str(e)}")
    
    async def process_speech_answer(self, session_id: str, question_id: str, 
                                 audio_data: bytes) -> AnswerSubmission:
        """Process speech answer: transcribe and grade"""
        
        # Transcribe speech to text
        stt_response = self.speech_client.speech_to_text(audio_data)
        transcribed_text = stt_response.transcription
        
        # Submit the transcribed answer
        return await self.submit_answer(
            session_id=session_id,
            question_id=question_id,
            student_answer=transcribed_text,
            audio_data=audio_data,
            transcribed_text=transcribed_text
        )
    
    async def generate_question_audio(self, question: Question) -> bytes:
        """Generate audio for question text using TTS"""
        try:
            from .models import TextToSpeechRequest
            
            tts_request = TextToSpeechRequest(
                text=question.text,
                voice="female",
                language="en"
            )
            
            tts_response = self.speech_client.text_to_speech(tts_request)
            
            # Convert base64 back to bytes
            import base64
            audio_bytes = base64.b64decode(tts_response.audio_data)
            
            return audio_bytes
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            return b""  # Return empty bytes on error

# Add audio_data and transcribed_text to AnswerSubmission model
# We need to extend the model for non-multiple choice questions
class ExtendedAnswerSubmission(AnswerSubmission):
    """Extended answer submission with audio and transcription data"""
    audio_data: Optional[bytes] = None
    transcribed_text: Optional[str] = None

# Update the AnswerSubmission model to include these fields
# This is a temporary workaround - in production, you'd modify the original model
AnswerSubmission.__annotations__['audio_data'] = Optional[bytes]
AnswerSubmission.__annotations__['transcribed_text'] = Optional[str]

if __name__ == "__main__":
    import asyncio
    
    async def test_exam_manager():
        print("Testing Exam Manager...")
        
        # Create exam manager
        exam_manager = ExamManager()
        
        # Test listing exams (create a sample exam first)
        print("Testing exam listing...")
        try:
            exams = await exam_manager.list_available_exams()
            print(f"Available exams: {exams}")
        except Exception as e:
            print(f"Error listing exams: {e}")
        
        # Test session management
        print("\nTesting session management...")
        try:
            # Create a sample exam file for testing
            sample_exam = {
                'exam': {
                    'title': 'Sample Test',
                    'description': 'A sample exam for testing',
                    'questions': [
                        {
                            'type': 'multiple_choice',
                            'text': 'What is 2+2?',
                            'options': ['A: 4', 'B: 5', 'C: 6', 'D: 7'],
                            'correct_answer': 'A',
                            'time_limit': 30
                        },
                        {
                            'type': 'quick_response',
                            'text': 'What is your favorite color?',
                            'time_limit': 15
                        }
                    ]
                }
            }
            
            # Create exams directory if it doesn't exist
            Path("../exams").mkdir(exist_ok=True)
            
            # Write sample exam
            with open("../exams/sample_test.yaml", 'w') as f:
                yaml.dump(sample_exam, f)
            
            # Start session
            session_request = SessionStartRequest(
                exam_filename="sample_test.yaml",
                student_name="Test Student"
            )
            
            session_response = await exam_manager.start_exam_session(session_request)
            print(f"Session started: {session_response.session_id}")
            
            # Get current question
            current_question = await exam_manager.get_current_question(session_response.session_id)
            print(f"Current question: {current_question.text if current_question else 'None'}")
            
            # Submit answer
            if current_question:
                answer = await exam_manager.submit_answer(
                    session_id=session_response.session_id,
                    question_id=current_question.id,
                    student_answer="A"
                )
                print(f"Answer submitted: Score {answer.score}")
            
            # Get session status
            status = await exam_manager.get_session_status(session_response.session_id)
            print(f"Session status: {status}")
            
        except Exception as e:
            print(f"Error in session test: {e}")
    
    # Run the test
    asyncio.run(test_exam_manager())