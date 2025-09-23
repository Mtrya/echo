import os
import aiohttp
import hashlib
import time
from pathlib import Path
import asyncio
try:
    from .models import STTOutput, STTInput, TTSOutput, TTSInput
except ImportError:
    from models import STTOutput, STTInput, TTSOutput, TTSInput

class SpeechClient:
    """Client for speech-to-text and text-to-speech processing"""
    
    def __init__(self):
        # Using Siliconflow for speech services with specific models
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        self.base_url = "https://api.siliconflow.cn/v1"
        self.stt_model = "TeleAI/TeleSpeechASR"  # For speech-to-text
        self.tts_model = "FunAudioLLM/CosyVoice2-0.5B"  # For text-to-speech
        self.voice_mapping = {
            "female": "FunAudioLLM/CosyVoice2-0.5B:anna",
            "male": "FunAudioLLM/CosyVoice2-0.5B:charles"
        }
        
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment variables")
        
        # Create cache directories
        self.cache_dir = Path("../audio_cache")
        self.tts_cache_dir = self.cache_dir / "tts"
        self.student_audio_dir = self.cache_dir / "student_answers"
        self.tts_cache_dir.mkdir(parents=True, exist_ok=True)
        self.student_audio_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_tts_cache_path(self, text: str, voice: str) -> Path:
        """Generate cache file path for TTS audio"""
        content = f"{text}|{voice}"
        hash_key = hashlib.md5(content.encode()).hexdigest()
        return self.tts_cache_dir / f"{hash_key}.mp3"
    
    def _get_student_audio_path(self, session_id: str, question_id: str) -> Path:
        """Generate file path for student audio recording"""
        session_dir = self.student_audio_dir / session_id
        session_dir.mkdir(exist_ok=True)
        timestamp = int(time.time())
        return session_dir / f"{question_id}_{timestamp}.webm"

    async def text_to_speech(self, request: TTSInput) -> TTSOutput:
        """Convert text to speech using Siliconflow CosyVoice2-0.5B"""
        try:
            print("Generating text to speech...")
            
            # Determine voice based on request
            voice = self.voice_mapping.get(request.voice, "FunAudioLLM/CosyVoice2-0.5B:claire")
            
            # Check cache first
            cache_file = self._get_tts_cache_path(request.text, request.voice)
            if cache_file.exists():
                print(f"Using cached audio: {cache_file}")
                return TTSOutput(
                    text=request.text,
                    audio_file_path=str(cache_file)
                )
            
            print("Cache miss, generating new audio...")
            
            payload = {
                "model": self.tts_model,
                "input": request.text,
                "voice": voice
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/audio/speech",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60.0)
                ) as response:
                    
                    if response.status == 200:
                        # Get the audio data
                        audio_data = await response.read()
                        
                        # Cache the audio file
                        with open(cache_file, 'wb') as f:
                            f.write(audio_data)
                        
                        print(f"Cached new audio: {cache_file}")
                        
                        return TTSOutput(
                            text=request.text,
                            audio_file_path=str(cache_file)
                        )
                    else:
                        error_text = await response.text()
                        print(f"Error response: {error_text}")
                        raise Exception(f"API returned status {response.status}: {error_text}")
            
        except Exception as e:
            print(f"Text to speech failed: {e}")
            raise

    async def speech_to_text(self, request: STTInput) -> STTOutput:
        """Convert speech to text using Siliconflow SenseVoiceSmall"""
        try:
            print("Processing speech to text...")
            
            # Save audio data to temporary file
            audio_file_path = self._get_student_audio_path(request.session_id, request.question_id)
            with open(audio_file_path, 'wb') as f:
                f.write(request.audio_data)
            
            print(f"Saved student audio to: {audio_file_path}")
            
            # Prepare the multipart form data
            data = aiohttp.FormData()
            data.add_field('model', self.stt_model)
            data.add_field('file', open(audio_file_path, 'rb'))
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=60.0)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        text = result.get("text", "")
                        
                        return STTOutput(
                            text=text,
                            audio_file_path=str(audio_file_path)
                        )
                    else:
                        error_text = await response.text()
                        print(f"Error response: {error_text}")
                        raise Exception(f"API returned status {response.status}: {error_text}")
            
        except Exception as e:
            print(f"Speech to text failed: {e}")
            raise


if __name__ == "__main__":
    pass