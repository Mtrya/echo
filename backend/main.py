from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from pathlib import Path

# Import our modules
try:
    from .models import (
        SessionStartRequest, SessionResponse, QuestionResponse,
        AnswerSubmission, AnswerResponse, FinalResult,
        FileConversionRequest, FileConversionResponse
    )
    from .exam_logic import ExamManager
    from .file_conversion import FileConverter
    from .config import config
except ImportError:
    from models import (
        SessionStartRequest, SessionResponse, QuestionResponse,
        AnswerSubmission, AnswerResponse, FinalResult,
        FileConversionRequest, FileConversionResponse
    )
    from exam_logic import ExamManager
    from file_conversion import FileConverter
    from config import config

# Initialize FastAPI app
app = FastAPI(
    title="Echo - LLM-Powered Exam Platform API",
    description="API for managing and taking English+Math exams for Chinese students",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
exam_manager = ExamManager()
file_converter = FileConverter()

# Mount static files for audio cache
app.mount("/audio_cache", StaticFiles(directory="../audio_cache"), name="audio_cache")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Echo - LLM-Powered Exam Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "exams": "/exams/list",
            "session": "/session/start",
            "health": "/health"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# List available exams
@app.get("/exams/list")
async def list_exams():
    """List all available exam YAML files"""
    try:
        exams = await exam_manager.list_available_exams()
        return {"exams": exams}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing exams: {str(e)}")

# Start exam session
@app.post("/session/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest):
    """Start a new exam session"""
    try:
        return await exam_manager.start_session(request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")

# Get current question
@app.get("/session/{session_id}/question", response_model=QuestionResponse)
async def get_question(session_id: str):
    """Get the current question for a session"""
    try:
        return await exam_manager.get_current_question(session_id)
    except ValueError as e:
        if "No more questions available" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "Session not found" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting question: {str(e)}")

# Submit answer
@app.post("/session/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, answer_data: AnswerSubmission):
    """Submit an answer for the current question"""
    try:
        return await exam_manager.submit_answer(session_id, answer_data)
    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        elif "No current question" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {str(e)}")

# Get audio generation status
@app.get("/session/{session_id}/audio-status")
async def get_audio_generation_status(session_id: str):
    """Get the audio generation status for a session"""
    try:
        return await exam_manager.get_audio_generation_status(session_id)
    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting audio generation status: {str(e)}")

# Get final results
@app.get("/session/{session_id}/results", response_model=FinalResult)
async def get_results(session_id: str):
    """Get the final exam results"""
    try:
        return await exam_manager.get_final_results(session_id)
    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        elif "Exam not completed" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting results: {str(e)}")

# File conversion endpoint
@app.post("/convert/file", response_model=FileConversionResponse)
async def convert_file(request: FileConversionRequest):
    """Convert file to exam format using qwen3-vl-plus"""
    try:
        return await file_converter.convert_files(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting file: {str(e)}")

# Rename exam file endpoint
@app.post("/rename-exam")
async def rename_exam(request: dict):
    """Rename an exam file in the exams directory"""
    try:
        old_name = request.get("old_name")
        new_name = request.get("new_name")

        if not old_name or not new_name:
            raise HTTPException(status_code=400, detail="Both old_name and new_name are required")

        return await file_converter.rename_exam_file(old_name, new_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renaming exam file: {str(e)}")

# Configuration endpoints
@app.get("/settings")
async def get_settings():
    """Get current configuration"""
    try:
        return {
            "success": True,
            "config": config.get_all(),
            "options": {
                "omni_models": config.OMNI_MODELS,
                "vision_models": config.VISION_MODELS,
                "themes": config.THEMES,
                "voice_options": config.VOICE_OPTIONS
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}")

@app.post("/settings")
async def update_settings(request: dict):
    """Update configuration"""
    try:
        new_config = request.get("config", {})
        result = config.update(new_config)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["errors"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")

@app.post("/test-api")
async def test_api_connection(request: dict):
    """Test API connection"""
    try:
        api_key = request.get("api_key", "")
        result = config.test_api_connection(api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing API connection: {str(e)}")

@app.get("/voices/{omni_model}")
async def get_available_voices(omni_model: str):
    """Get available voices for a specific omni model"""
    try:
        voices = config.get_available_voices(omni_model)
        return {"success": True, "voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting voices: {str(e)}")

# Error handler
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(exc)
        }
    )

# Run the application
if __name__ == "__main__":    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )