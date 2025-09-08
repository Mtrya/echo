from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import yaml
import json
import tempfile
import os
from pathlib import Path

# Import our models and clients
try:
    from .models import (
        Question, Exam, GradeRequest, GradeResponse, SessionStartRequest, 
        SessionResponse, SpeechToTextResponse, TextToSpeechRequest, TextToSpeechResponse,
        AnswerSubmission, SessionResults
    )
    from .exam_logic import ExamManager
    from .llm_client import LLMClient
    from .speech_client import SpeechClient
    from .file_conversion import FileProcessor
except ImportError:
    from models import (
        Question, Exam, GradeRequest, GradeResponse, SessionStartRequest, 
        SessionResponse, SpeechToTextResponse, TextToSpeechRequest, TextToSpeechResponse,
        AnswerSubmission, SessionResults
    )
    from exam_logic import ExamManager
    from llm_client import LLMClient
    from speech_client import SpeechClient
    from file_conversion import FileProcessor


app = FastAPI(title="Echo - LLM-Powered Exam Platform API", version="1.0.0")

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize exam manager
exam_manager = ExamManager()

# Initialize clients for direct use
llm_client = LLMClient()
speech_client = SpeechClient()
file_processor = FileProcessor()

@app.get("/")
async def root():
    return {"message": "Echo - LLM-Powered Exam Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/exams/list")
async def list_exams():
    """List all available exam files"""
    try:
        exam_files = await exam_manager.list_available_exams()
        return {"exams": exam_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing exams: {str(e)}")

@app.get("/exams/{filename}")
async def get_exam(filename: str):
    """Load exam questions from YAML file"""
    try:
        exam = await exam_manager.load_exam_from_yaml(filename)
        return exam
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading exam: {str(e)}")

@app.post("/sessions/start")
async def start_session(request: SessionStartRequest):
    """Start a new exam session"""
    try:
        session_response = await exam_manager.start_exam_session(request)
        return session_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")

@app.post("/process/grade-answer")
async def grade_answer(request: GradeRequest):
    """Grade student answer using LLM based on question type"""
    try:
        # Use the LLM client to grade the answer
        result = await llm_client.grade_answer(request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error grading answer: {str(e)}")

@app.post("/process/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert speech to text using Modelscope SenseVoiceSmall"""
    try:
        # Read the audio file
        audio_data = await audio.read()
        
        # Use the speech client to convert speech to text
        result = await speech_client.speech_to_text(audio_data)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing speech: {str(e)}")

@app.post("/process/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """Convert text to speech using Modelscope SenseVoiceSmall"""
    try:
        # Use the speech client to convert text to speech
        result = await speech_client.text_to_speech(request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@app.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get session status"""
    try:
        status = await exam_manager.get_session_status(session_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/sessions/{session_id}/submit")
async def submit_answer(session_id: str, answer: Dict[str, Any]):
    """Submit answer for a question"""
    try:
        # Extract answer data
        question_id = answer.get("question_id")
        student_answer = answer.get("student_answer")
        audio_data = answer.get("audio_data")
        transcribed_text = answer.get("transcribed_text")
        
        if not question_id or student_answer is None:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Submit answer using exam manager
        answer_submission = await exam_manager.submit_answer(
            session_id=session_id,
            question_id=question_id,
            student_answer=student_answer,
            audio_data=audio_data,
            transcribed_text=transcribed_text
        )
        
        return {"message": "Answer submitted successfully", "answer": answer_submission}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {str(e)}")

@app.get("/sessions/{session_id}/results")
async def get_session_results(session_id: str):
    """Get final results for a session"""
    try:
        results = await exam_manager.get_session_results(session_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/sessions/{session_id}/current-question")
async def get_current_question(session_id: str):
    """Get current question for a session"""
    try:
        question = await exam_manager.get_current_question(session_id)
        if not question:
            raise HTTPException(status_code=404, detail="No current question available")
        return question
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)