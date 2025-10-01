"""
A unified client for automatic answer grading & instruction tts
- Read Aloud: text+audio input; text output (json)
- Multiple Choice: text input; text output (json)
- Quick Response: text+audio input; text output (json)
- Translation: text+audio input; text output (json)
- Instruction: text input; text+audio output (though we only need audio data)

Audio comes in as base64encoded audio data; comes out as path of .mp3 file.
"""

import os
import aiohttp
import base64
import json
import time
import hashlib
import numpy as np
import ssl
from pathlib import Path
from typing import Optional, Dict, Any, List
import soundfile as sf
from json_repair import repair_json
try:
    from .models import TTSResult, TTSInput, GradingInput, GradingResult, ConversionInput, ConversionResult, Question
    from .config import config
    from .paths import get_paths
except ImportError:
    from models import TTSResult, TTSInput, GradingInput, GradingResult, ConversionInput, ConversionResult, Question
    from config import config
    from paths import get_paths

class OmniClient:
    """Unified client for qwen3-omni-flash and qwen3-vl-plus models handling TTS, ASR, LLM, and vision functions"""

    def __init__(self, model="qwen3-omni-flash"):
        self.api_key = config.get("api.dashscope_key")
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = model

        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in configuration. Please set it in Settings.")

        # Get paths from centralized path management
        paths = get_paths()
        self.cache_dir = paths.audio_cache
        self.tts_cache_dir = paths.tts_cache
        self.student_audio_dir = paths.student_answers

        # Load prompt templates
        self.prompts_dir = paths.prompts_dir
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, str]:
        """Load all prompt templates from files."""
        prompts = {}
        if self.prompts_dir.exists():
            for prompt_file in self.prompts_dir.glob("*.txt"):
                prompt_name = prompt_file.stem
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompts[prompt_name] = f.read().strip()
        return prompts

    def _get_prompt(self, prompt_name: str, **kwargs) -> str:
        """Get a prompt template with variables substituted."""
        if prompt_name not in self.prompts:
            raise ValueError(f"Prompt '{prompt_name}' not found")

        prompt = self.prompts[prompt_name]
        return prompt.format(**kwargs)

    def _get_tts_cache_path(self, text: str, voice: str) -> Path:
        """Generate cache file path for TTS audio"""
        content = f"{self.model}|{text}|{voice}"
        hash_key = hashlib.md5(content.encode()).hexdigest()
        return self.tts_cache_dir / f"{hash_key}.mp3"

    async def _process_omni_request(
        self,
        text_prompt: str,
        base64_audio: Optional[str] = None,
        base64_images: Optional[List[str]] = None,
        voice: str = "Cherry",
        output_modalities: Optional[list] = ["text", "audio"],
        enable_thinking: bool = False
    ) -> Dict[str, Any]:
        """
        Process unified request with qwen3-omni-flash or qwen3-vl-plus
        Returns dict with text_response and optional base64encoded audio data
        """
        print(f"Processing omni request: {text_prompt[:50]}...")

        # Prepare the content array
        content = []

        # Add images if provided (for vision models)
        if base64_images:
            for base64_image in base64_images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })

        # Add audio if provided
        if base64_audio:
            content.append({
                "type": "input_audio",
                "input_audio": {
                    "data": f"data:;base64,{base64_audio}",
                    "format": "mp3"
                }
            })

        # Add text prompt
        content.append({
            "type": "text",
            "text": text_prompt
        })

        # Prepare the request payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "stream": True,
            "stream_options": {"include_usage": True}
        }

        # Only add audio and modalities for audio-capable models
        if self.model in ["qwen3-omni-flash"]:
            payload["modalities"] = output_modalities
            payload["audio"] = {
                "voice": voice,
                "format": "wav"
            }

        if enable_thinking is not None:
            payload["extra_body"] = {"enable_thinking": enable_thinking}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        text_response = ""
        audio_response = ""
        usage_info = None

        # Create SSL context for PyInstaller compatibility
        try:
            # Try to use system certificates first
            ssl_context = ssl.create_default_context()
        except:
            # Fallback to SSL verification disabled for PyInstaller environments
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300.0)
            ) as response:

                if response.status != 200:
                    error_text = await response.text()
                    print(f"API Error ({response.status}): {error_text}")
                    raise Exception(f"API returned status {response.status}: {error_text}")

                # Process streaming response
                async for line in response.content:
                    line = line.decode('utf-8').strip()

                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            data = json.loads(line[6:])  # Remove "data: " prefix

                            if data.get("choices"):
                                delta = data["choices"][0].get("delta", {})

                                # Handle audio data
                                if "audio" in delta:
                                    audio_data = delta["audio"]
                                    if "data" in audio_data:
                                        audio_response += audio_data["data"]
                                    elif "transcript" in audio_data:
                                        print(f"Audio transcript: {audio_data['transcript']}")

                                # Handle text data
                                if "content" in delta and delta["content"]:
                                    text_response += delta["content"]

                            # Handle usage stats
                            if data.get("usage"):
                                usage_info = data["usage"]

                        except json.JSONDecodeError as e:
                            print(f"Failed to parse JSON: {line}")
                            continue

            return {
                "text_response": text_response,
                "audio_response": audio_response, # base64encoded audio data
                "usage": usage_info
            }

    async def text_to_speech(self, request: TTSInput) -> TTSResult:
        """Convert text to speech using qwen3-omni-flash"""

        # Check cache first
        cache_path = self._get_tts_cache_path(request.text, request.voice)
        if cache_path.exists():
            # Return web-accessible path relative to /audio_cache mount point
            web_path = f"/audio_cache/tts/{cache_path.name}"
            return TTSResult(
                text=request.text,
                audio_file_path=web_path
            )

        # Prepare TTS prompt
        tts_prompt = self._get_prompt("text_to_speech", text=request.text)

        # Process request
        result = await self._process_omni_request(
            text_prompt=tts_prompt,
            voice=request.voice,
            output_modalities=["text","audio"],
            enable_thinking=False
        )

        if result["audio_response"]:
            # Cache the audio file
            mp3_bytes = base64.b64decode(result["audio_response"])
            audio_np = np.frombuffer(mp3_bytes, dtype=np.int16)
            sf.write(cache_path, audio_np, samplerate=24000)

            # Return web-accessible path relative to /audio_cache mount point
            web_path = f"/audio_cache/tts/{cache_path.name}"
            return TTSResult(
                text=request.text,
                audio_file_path=web_path
            )
        else:
            raise Exception("No audio response received from TTS request")

    def _cache_student_audio(self, base64_audio: str, session_id: str, question_id: str) -> Path:
        """Cache student audio - save as MP3 for playback"""
        audio_bytes = base64.b64decode(base64_audio)
        session_dir = self.student_audio_dir / session_id
        session_dir.mkdir(exist_ok=True)
        timestamp = int(time.time())

        # Save MP3 file directly (browser now sends MP3 format)
        mp3_path = session_dir / f"{question_id}_{timestamp}.mp3"
        with open(mp3_path, 'wb') as f:
            f.write(audio_bytes)

        print(f"✅ Cached student MP3 audio: {mp3_path}")
        return mp3_path

    async def _grade_read_aloud(self, request: GradingInput) -> GradingResult:
        """Grade student answer for read-aloud questions"""
        # Cache student audio for debugging/review
        audio_path = self._cache_student_audio(request.student_answer_audio, request.session_id, request.question_id)

        # Prepare grading prompt for read-aloud
        grading_prompt = self._get_prompt("read_aloud_grading", question_text=request.question_text)

        # Process request
        try:
            result = await self._process_omni_request(
                text_prompt=grading_prompt,
                base64_audio=request.student_answer_audio,
                output_modalities=["text"],
                enable_thinking=True
            )

            # Parse and repair JSON response
            response_text = result["text_response"].strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]

            repaired_json = repair_json(response_text)
            grading_data = json.loads(repaired_json)

            return GradingResult(
                score=float(grading_data["score"]),
                feedback=grading_data["feedback"],
                explanation=grading_data["explanation"],
                student_audio_path=str(audio_path)
            )
        except:
            return GradingResult(
                score=0.0,
                feedback="Grading failed",
                explanation="Technical issue with AI processing"
            )

    async def _grade_multiple_choice(self, request: GradingInput) -> GradingResult:
        """Grade student answer for multiple-choice questions"""
        student_answer = request.student_answer_text

        # Prepare grading prompt for multiple choice
        options_text = chr(10).join(request.options) if request.options else 'No options provided'
        grading_prompt = self._get_prompt("multiple_choice_grading",
                                         question_text=request.question_text,
                                         options=options_text,
                                         reference_answer=request.reference_answer,
                                         student_answer=student_answer)

        # Process request
        try:
            result = await self._process_omni_request(
                text_prompt=grading_prompt,
                base64_audio=request.student_answer_audio,
                output_modalities=["text"],
                enable_thinking=True
            )

            # Parse and repair JSON response
            response_text = result["text_response"].strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]

            repaired_json = repair_json(response_text)
            grading_data = json.loads(repaired_json)

            return GradingResult(
                score=float(grading_data["score"]),
                feedback=grading_data["feedback"],
                explanation=grading_data["explanation"],
                student_answer=student_answer
            )
        except:
            return GradingResult(
                score=0.0,
                feedback="Grading failed",
                explanation="Technical issue with AI processing"
            )

    async def _grade_quick_response(self, request: GradingInput) -> GradingResult:
        """Grade student answer for quick-response questions"""
        # Cache student audio for debugging/review
        audio_path = self._cache_student_audio(request.student_answer_audio, request.session_id, request.question_id)

        # Prepare grading prompt for quick response
        grading_prompt = self._get_prompt("quick_response_grading", question_text=request.question_text)

        # Process request
        try:
            result = await self._process_omni_request(
                text_prompt=grading_prompt,
                base64_audio=request.student_answer_audio,
                output_modalities=["text"],
                enable_thinking=True
            )

            # Parse the JSON response
            import json
            response_text = result["text_response"].strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]

            grading_data = json.loads(response_text)

            return GradingResult(
                score=float(grading_data["score"]),
                feedback=grading_data["feedback"],
                explanation=grading_data["explanation"],
                suggested_answer=grading_data.get("suggested_answer"),
                student_audio_path=str(audio_path)
            )
        except:
            return GradingResult(
                score=0.0,
                feedback="Grading failed",
                explanation="Technical issue with AI processing"
            )

    async def _grade_translation(self, request: GradingInput) -> GradingResult:
        """Grade student answer for translation questions"""
        # Cache student audio for debugging/review
        audio_path = self._cache_student_audio(request.student_answer_audio, request.session_id, request.question_id)

        # Prepare grading prompt for translation
        grading_prompt = self._get_prompt("translation_grading", question_text=request.question_text)

        # Process request
        try:
            result = await self._process_omni_request(
                text_prompt=grading_prompt,
                base64_audio=request.student_answer_audio,
                output_modalities=["text"],
                enable_thinking=True
            )

            # Parse the JSON response
            import json
            response_text = result["text_response"].strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]

            grading_data = json.loads(response_text)

            return GradingResult(
                score=float(grading_data["score"]),
                feedback=grading_data["feedback"],
                explanation=grading_data["explanation"],
                suggested_answer=grading_data.get("suggested_answer"),
                student_audio_path=str(audio_path)
            )
        except:
            return GradingResult(
                score=0.0,
                feedback="Grading failed",
                explanation="Technical issue with AI processing"
            )

    async def convert_files_to_questions(self, request: ConversionInput) -> ConversionResult:
        """Convert files to exam questions using vision model"""
        # Get the conversion prompt
        conversion_prompt = self._get_prompt("file_conversion")

        # Handle text input - concatenate and insert into prompt
        if request.texts:
            combined_text = "\n\n".join(request.texts)
            full_prompt = f"""{conversion_prompt}

## Content to analyze:
{combined_text}"""
        else:
            # Handle image input
            full_prompt = conversion_prompt
            
        base64_images = request.images

        # Process the conversion request
        result = await self._process_omni_request(
            text_prompt=full_prompt,
            base64_images=base64_images,
            enable_thinking=True
        )

        # Parse the JSON response
        response_text = result["text_response"].strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]

        # Repair and parse JSON
        repaired_json = repair_json(response_text)
        conversion_data = json.loads(repaired_json)

        # Convert to Question objects
        questions = []
        for q_data in conversion_data.get("extracted_questions", []):
            question = Question(
                id=q_data["id"],
                type=q_data["type"],
                text=q_data["text"],
                options=q_data.get("options"),
                reference_answer=q_data.get("reference_answer")
            )
            questions.append(question)

        return ConversionResult(
            success=conversion_data["success"],
            message=conversion_data["message"],
            extracted_questions=questions
        )

    async def grade_answer(self, request: GradingInput) -> GradingResult:
        """Grade student answer based on question type"""
        if request.question_type == "read_aloud":
            return await self._grade_read_aloud(request)
        elif request.question_type == "multiple_choice":
            return await self._grade_multiple_choice(request)
        elif request.question_type == "quick_response":
            return await self._grade_quick_response(request)
        elif request.question_type == "translation":
            return await self._grade_translation(request)
        else:
            return GradingResult(
                score=0.0,
                feedback="Unknown question type",
                explanation="Unable to grade due to unknown question type",
            )

if __name__ == "__main__":
    pass