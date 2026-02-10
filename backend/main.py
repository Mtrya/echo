from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import sys
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

# Import paths after module initialization
try:
    from .paths import get_paths
except ImportError:
    from paths import get_paths

# Mount static files for audio cache
paths = get_paths()
app.mount("/audio_cache", StaticFiles(directory=str(paths.audio_cache)), name="audio_cache")

# API info endpoint (moved from root to avoid conflict with frontend)
@app.get("/api/info")
async def api_info():
    """API information endpoint"""
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

# API key status endpoint
@app.get("/api-key-status")
async def api_key_status():
    """Check if API key is configured"""
    try:
        has_key = exam_manager.has_api_key()
        return {
            "has_api_key": has_key,
            "message": "API key configured" if has_key else "API key not configured"
        }
    except Exception as e:
        return {
            "has_api_key": False,
            "message": f"Error checking API key: {str(e)}"
        }

# List available exams
@app.get("/exams/list")
async def list_exams(include_completed: bool = True):
    """List available exam YAML files with optional filtering"""
    try:
        exams = await exam_manager.list_available_exams(include_completed)
        return {"exams": exams}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing exams: {str(e)}")

# Get completed exams
@app.get("/exams/completed")
async def get_completed_exams():
    """Get list of completed exam files"""
    try:
        completed_exams = exam_manager.get_completed_exams()
        return {"completed_exams": completed_exams}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting completed exams: {str(e)}")

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

# Delete exam file endpoint
@app.post("/delete-exam")
async def delete_exam(request: dict):
    """Delete an exam file from the exams directory"""
    try:
        exam_filename = request.get("exam_filename")

        if not exam_filename:
            raise HTTPException(status_code=400, detail="exam_filename is required")

        return await file_converter.delete_exam_file(exam_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting exam file: {str(e)}")

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

# Mount frontend static files (moved after API endpoints to avoid conflicts)
# In Tauri mode, Tauri serves the frontend — only mount API and audio_cache
if not os.environ.get('TAURI_MODE'):
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle - frontend files are in the bundled directory
        bundled_frontend_path = Path(sys._MEIPASS) / "frontend" / "dist"
        if bundled_frontend_path.exists():
            app.mount("/", StaticFiles(directory=str(bundled_frontend_path), html=True), name="frontend")
        else:
            print(f"Warning: Frontend directory not found at {bundled_frontend_path}")
    else:
        # Development environment
        frontend_path = paths.base_path / "frontend" / "dist"
        if frontend_path.exists():
            app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
        else:
            # Fallback for development when running from source
            dev_frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
            if dev_frontend_path.exists():
                app.mount("/", StaticFiles(directory=str(dev_frontend_path), html=True), name="frontend")

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