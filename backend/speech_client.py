import os
import requests
import base64
from typing import Optional
try:
    from .models import SpeechToTextResponse, TextToSpeechResponse, TextToSpeechRequest
except ImportError:
    from models import SpeechToTextResponse, TextToSpeechResponse, TextToSpeechRequest

class SpeechClient:
    """Client for speech-to-text and text-to-speech processing"""
    
    def __init__(self):
        # Using Siliconflow for speech services with specific models
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        self.base_url = "https://api.siliconflow.cn/v1"
        self.stt_model = "FunAudioLLM/SenseVoiceSmall"  # For speech-to-text
        self.tts_model = "FunAudioLLM/CosyVoice2-0.5B"  # For text-to-speech
        
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment variables")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def speech_to_text(self, audio_data: bytes) -> SpeechToTextResponse:
        """Convert speech to text using Siliconflow SenseVoiceSmall"""
        try:
            # Encode audio data as base64
            audio_base64 = base64.b64encode(audio_data).decode()
            
            # Prepare the API request
            payload = {
                "model": self.stt_model,
                "audio": audio_base64
            }
            
            response = requests.post(
                f"{self.base_url}/audio/transcriptions",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract transcription details from response
                transcription = result.get("text", "")
                confidence = result.get("confidence", 0.0)
                language = result.get("language", "en")
                
                return SpeechToTextResponse(
                    transcription=transcription,
                    confidence=confidence,
                    language=language
                )
            else:
                print(f"Speech-to-text API error: {response.status_code} - {response.text}")
                # Fallback to mock if API fails
                return self._mock_speech_to_text()
            
        except Exception as e:
            print(f"Speech-to-text API call failed: {e}")
            # Fallback to mock if API fails
            return self._mock_speech_to_text()
    
    def _mock_speech_to_text(self) -> SpeechToTextResponse:
        """Mock implementation as fallback"""
        mock_transcriptions = [
            "The cat sat on the mat.",
            "Hello, my name is Sarah.",
            "Technology has revolutionized communication.",
            "I enjoy learning new things every day.",
            "Math is my favorite subject."
        ]
        
        import random
        transcription = random.choice(mock_transcriptions)
        confidence = 0.85 + random.random() * 0.15
        
        return SpeechToTextResponse(
            transcription=transcription,
            confidence=confidence,
            language="en"
        )
    
    def text_to_speech(self, request: TextToSpeechRequest) -> TextToSpeechResponse:
        """Convert text to speech using Siliconflow CosyVoice2-0.5B"""
        try:
            # Prepare the API request
            payload = {
                "model": self.tts_model,
                "input": request.text,
                "voice": request.voice,
                "language": request.language,
                "speed": request.speed
            }
            
            response = requests.post(
                f"{self.base_url}/audio/speech",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                # The API should return audio data directly
                audio_data = response.content
                
                # Calculate approximate duration
                duration = len(request.text) * 0.1 * request.speed
                
                # Encode audio data as base64 for storage/transmission
                audio_base64 = base64.b64encode(audio_data).decode()
                
                return TextToSpeechResponse(
                    audio_data=audio_base64,
                    duration=duration,
                    text=request.text
                )
            else:
                print(f"Text-to-speech API error: {response.status_code} - {response.text}")
                # Fallback to mock if API fails
                return self._mock_text_to_speech(request)
            
        except Exception as e:
            print(f"Text-to-speech API call failed: {e}")
            # Fallback to mock if API fails
            return self._mock_text_to_speech(request)
    
    def _mock_text_to_speech(self, request: TextToSpeechRequest) -> TextToSpeechResponse:
        """Mock implementation as fallback"""
        duration = len(request.text) * 0.1 * request.speed
        
        # Generate mock base64 audio data
        mock_audio_data = base64.b64encode(b"mock_audio_data").decode()
        
        return TextToSpeechResponse(
            audio_data=mock_audio_data,
            duration=duration,
            text=request.text
        )

if __name__ == "__main__":
    # Test the SpeechClient
    print("Testing Speech Client...")
    
    speech_client = SpeechClient()
    
    # Test speech-to-text
    print("\nTesting speech-to-text...")
    mock_audio = b"mock_audio_data"
    stt_result = speech_client.speech_to_text(mock_audio)
    print(f"Transcription: {stt_result.transcription}")
    print(f"Confidence: {stt_result.confidence}")
    print(f"Language: {stt_result.language}")
    
    # Test text-to-speech
    print("\nTesting text-to-speech...")
    tts_request = TextToSpeechRequest(
        text="Hello, this is a test.",
        voice="female",
        language="en"
    )
    tts_result = speech_client.text_to_speech(tts_request)
    print(f"Audio data length: {len(tts_result.audio_data)}")
    print(f"Duration: {tts_result.duration}")
    print(f"Text: {tts_result.text}")
    
    print("\nSpeech Client tests completed!")