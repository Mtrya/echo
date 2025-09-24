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
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import soundfile as sf
from json_repair import repair_json
try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None
try:
    from .models import TTSOutput, TTSInput, GradingInput, GradingResult
except ImportError:
    from models import TTSOutput, TTSInput, GradingInput, GradingResult

class OmniClient:
    """Unified client for qwen3-omni-flash model handling TTS, ASR, and LLM functions"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.model = "qwen3-omni-flash"

        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in environment variables")
        
        self.cache_dir = Path("../audio_cache")
        self.tts_cache_dir = self.cache_dir / "tts"
        self.student_audio_dir = self.cache_dir / "student_answers"
        self.tts_cache_dir.mkdir(parents=True, exist_ok=True)
        self.student_audio_dir.mkdir(parents=True, exist_ok=True)

    def _get_tts_cache_path(self, text: str, voice: str) -> Path:
        """Generate cache file path for TTS audio"""
        content = f"{self.model}|{text}|{voice}"
        hash_key = hashlib.md5(content.encode()).hexdigest()
        return self.tts_cache_dir / f"{hash_key}.mp3"

    async def _process_omni_request(
        self,
        text_prompt: str,
        base64_audio: Optional[str] = None,
        voice: str = "Cherry",
        modalities: list = ["text", "audio"],
        enable_thinking: bool = False
    ) -> Dict[str, Any]:
        """
        Process unified request with qwen3-omni-flash
        Returns dict with text_response and optional base64encoded audio data
        """
        print(f"Processing omni request: {text_prompt[:50]}...")

        # Prepare the content array
        content = []

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
            "modalities": modalities,
            "audio": {
                "voice": voice,
                "format": "wav"
            },
            "stream": True,
            "stream_options": {"include_usage": True}
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

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120.0)
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

    async def text_to_speech(self, request: TTSInput) -> TTSOutput:
        """Convert text to speech using qwen3-omni-flash"""

        # Check cache first
        cache_path = self._get_tts_cache_path(request.text, request.voice)
        if cache_path.exists():
            return TTSOutput(
                text=request.text,
                audio_file_path=str(cache_path)
            )

        # Prepare TTS prompt
        tts_prompt = f"""You are a text-to-speech assistant. Please read the following text:

`{request.text}`

Please read this text exactly as written, without any opening or greeting."""

        # Process request
        result = await self._process_omni_request(
            text_prompt=tts_prompt,
            voice=request.voice,
            modalities=["text","audio"],
            enable_thinking=False
        )

        if result["audio_response"]:
            # Cache the audio file
            mp3_bytes = base64.b64decode(result["audio_response"])
            audio_np = np.frombuffer(mp3_bytes, dtype=np.int16)
            sf.write(cache_path, audio_np, samplerate=24000)

            return TTSOutput(
                text=request.text,
                audio_file_path=str(cache_path)
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
        self._cache_student_audio(request.student_answer_audio, request.session_id, request.question_id)

        # Prepare grading prompt for read-aloud
        grading_prompt = f"""You are grading a student's read-aloud performance.

Text: {request.question_text}

Please evaluate the student's pronunciation, fluency, and accuracy based on their audio recording.

Provide a score from 0-10 where:
- 8-10: Excellent pronunciation and fluency, minimal errors
- 6-7: Good performance with some pronunciation issues
- 4-5: Fair performance, noticeable pronunciation problems
- 0-3: Poor performance, significant pronunciation issues

Respond in JSON format:
{{
    "score": <number between 0-10>,
    "feedback": "<specific feedback on pronunciation and fluency>",
    "explanation": "<detailed explanation of the evaluation>"
}}"""

        # Process request
        try:
            result = await self._process_omni_request(
                text_prompt=grading_prompt,
                base64_audio=request.student_answer_audio,
                modalities=["text"],
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
                explanation=grading_data["explanation"]
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
        grading_prompt = f"""You are grading a multiple-choice question.

Question: {request.question_text}

Options:
{chr(10).join(request.options) if request.options else 'No options provided'}

Reference Answer: {request.reference_answer}

Student Answer: {student_answer}

Please evaluate if the student selected the correct option. The student should identify the letter (A, B, C, or D) corresponding to the correct answer.

Score:
- 10 points: Correct answer identified
- 0 points: Incorrect answer or unclear response

Respond in JSON format:
{{
    "score": <10 or 0>,
    "feedback": "<specific feedback about their answer choice>",
    "explanation": "<explanation of the correct answer and why the student's choice was correct/incorrect>"
}}"""

        # Process request
        try:
            result = await self._process_omni_request(
                text_prompt=grading_prompt,
                base64_audio=request.student_answer_audio,
                modalities=["text"],
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
                explanation=grading_data["explanation"]
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
        self._cache_student_audio(request.student_answer_audio, request.session_id, request.question_id)

        # Prepare grading prompt for quick response
        grading_prompt = f"""You are grading a student's quick verbal response to an audio question.

Question Context: {request.question_text}

Reference Answer: {request.reference_answer}

Please evaluate the student's verbal response based on:
1. Relevance to the question
2. Accuracy of information
3. Clarity of expression
4. Appropriateness for a 10-year-old Chinese student learning English

The student heard the question in audio format and responded verbally. Their response should be evaluated for content comprehension and communication effectiveness.

Provide a score from 0-10 where:
- 8-10: Excellent, relevant, and accurate response
- 6-7: Good response with minor issues
- 4-5: Partially correct or somewhat relevant
- 0-3: Incorrect, irrelevant, or incomprehensible

Respond in JSON format:
{{
    "score": <number between 0-10>,
    "feedback": "<specific feedback about the content and delivery>",
    "explanation": "<detailed evaluation of the response>",
    "suggested_answer": "<an example of a good answer to this question if score < 3>"
}}"""

        # Process request
        try:
            result = await self._process_omni_request(
                text_prompt=grading_prompt,
                base64_audio=request.student_answer_audio,
                modalities=["text"],
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
                suggested_answer=grading_data.get("suggested_answer")
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
        self._cache_student_audio(request.student_answer_audio, request.session_id, request.question_id)

        # Prepare grading prompt for translation
        grading_prompt = f"""You are grading a student's translation performance.

Chinese Text: {request.question_text}

Reference English Translation: {request.reference_answer}

The student was asked to translate the Chinese text into English and provide their answer verbally. Please evaluate their translation based on:
1. Accuracy of translation
2. Grammar and vocabulary usage
3. Pronunciation and clarity of spoken English
4. Naturalness of the English expression

Provide a score from 0-10 where:
- 8-10: Excellent translation, accurate grammar, natural expression
- 6-7: Good translation with minor errors
- 4-5: Fair translation with noticeable issues
- 0-3: Poor translation, significant errors

Respond in JSON format:
{{
    "score": <number between 0-10>,
    "feedback": "<specific feedback on translation accuracy and spoken English>",
    "explanation": "<detailed evaluation of the translation performance>",
    "suggested_answer": "<an example of a good English translation if score < 3>"
}}"""

        # Process request
        try:
            result = await self._process_omni_request(
                text_prompt=grading_prompt,
                base64_audio=request.student_answer_audio,
                modalities=["text"],
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
                suggested_answer=grading_data.get("suggested_answer")
            )
        except:
            return GradingResult(
                score=0.0,
                feedback="Grading failed",
                explanation="Technical issue with AI processing"
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