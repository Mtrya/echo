import os
import aiohttp
import json
import asyncio
try:
    from .models import (
        GradingInput, GradingResult
    )
except ImportError:
    from models import (
        GradingInput, GradingResult
    )

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        self.base_url = "https://api.siliconflow.cn/v1"
        self.model = "Qwen/Qwen3-30B-A3B-Instruct-2507"
        
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment variables")
        
        # Using synchronous requests for better control
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def grade_answer(self, request: GradingInput) -> GradingResult:
        """Grade student answer based on question type"""
        if request.question_type == "multiple_choice":
            return await self._grade_multiple_choice(request)
        elif request.question_type == "read_aloud":
            return await self._grade_read_aloud(request)
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
    
    async def _grade_multiple_choice(self, request: GradingInput) -> GradingResult:
        """Multiple choice: automatic scoring, LLM provides explanation"""
        try:
            is_correct = request.student_answer.lower() == request.correct_answer.lower()
            score = 1.0 if is_correct else 0.0
            
            # Generate explanation for why each option is right or wrong
            options_text = request.options if request.options else "Options not provided"
            
            prompt = f"""
            You are an expert English and Math teacher for 10-year-old Chinese students.
            
            Question: {request.question_text}
            Correct Answer: {request.correct_answer}
            Student's Answer: {request.student_answer}
            Options: {options_text}
            
            Please provide a clear, age-appropriate explanation that:
            1. Explains why the correct answer is right
            2. Explains why other options might be wrong
            
            Keep the explanation simple and suitable for a 10-year-old. Use no more than 100 words.
            """
            
            explanation = await self._call_llm(prompt)
            
            feedback = "Correct! Well done!" if is_correct else f"Incorrect. The right answer is: {request.correct_answer}"
            
            return GradingResult(
                score=score,
                feedback=feedback,
                explanation=explanation,
            )
            
        except Exception as e:
            return GradingResult(
                score=score,
                feedback="Correct! Well done!" if is_correct else f"Incorrect. The right answer is: {request.correct_answer}",
                explanation=f"Technical issue with AI explanation. Exception: {e}"
            )
    
    async def _grade_read_aloud(self, request: GradingInput) -> GradingResult:
        """Read aloud: simple text matching, no LLM needed"""
        try:
            # Simple text matching for read aloud practice
            # Remove punctuation and convert to lowercase for comparison
            clean_student = request.student_answer.lower().replace('.', '').replace(',', '').replace('!', '').replace('?', '')
            clean_correct = request.correct_answer.lower().replace('.', '').replace(',', '').replace('!', '').replace('?', '')
            
            # Check if student answer contains key words from correct answer
            correct_words = set(clean_correct.split())
            student_words = set(clean_student.split())
            
            if correct_words.issubset(student_words):
                score = 1.0
                feedback = "Perfect! You read all the words correctly."
                explanation = "Excellent pronunciation and accuracy!"
            else:
                # Calculate partial score based on word matches
                matches = len(correct_words.intersection(student_words))
                score = matches / len(correct_words)
                feedback = f"Good attempt! You got {matches} out of {len(correct_words)} words correct."
                explanation = "Keep practicing to improve your reading accuracy."
            
            return GradingResult(
                score=score,
                feedback=feedback,
                explanation=explanation,
            )
            
        except Exception as e:
            return GradingResult(
                score=0.0,
                feedback="Unable to process read aloud response.",
                explanation="Technical issue with text comparison.",
            )
    
    async def _grade_quick_response(self, request: GradingInput) -> GradingResult:
        """Quick response: LLM grades answer relevance"""
        try:
            prompt = f"""
            You are an expert English and Math teacher for 10-year-old Chinese students.
            You are grading exam responses, so focus on grammar accuracy and meaning correspondence.
            
            Question: {request.question_text}
            Student's Answer: {request.student_answer}
            
            Please evaluate if the student's answer is a proper response to the question.
            Consider:
            1. Does the answer address the question?
            2. Is the response relevant and appropriate?
            3. Grammar accuracy and sentence structure
            
            Examples:
            - Question: "What do you like to do after school?" 
              Answer: "I like playing soccer with my friends" → Score: 1.0 (Perfect grammar, relevant)
            - Question: "What is your favorite color?"
              Answer: "Blue because it's the color of the sky" → Score: 1.0 (Good explanation)
            - Question: "What do you want to be when you grow up?"
              Answer: "Doctor" → Score: 0.7 (Too brief, but relevant)
            - Question: "What did you eat for breakfast?"
              Answer: "I like dogs" → Score: 0.2 (Irrelevant but grammatically correct)
            
            Scoring:
            - 1.0: Perfect answer with good grammar and relevance
            - 0.8-0.9: Good answer with minor issues
            - 0.6-0.7: Adequate but brief or has some grammar issues
            - 0.0-0.5: Poor answer, irrelevant, or major grammar problems
            
            Provide your evaluation in JSON format:
            {{
                "score": 0.0,
                "feedback": "Your feedback here",
                "explanation": "Your brief explanation here"
            }}
            
            If the score is below 0.7, also include a "suggested_answer" field with an appropriate response.
            """
            
            response_text = await self._call_llm(prompt)
            
            # Clean up response text - remove markdown code block formatting if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove ```
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            score = float(result.get("score")) # no fallback, if doesn't include keys, jump to exception directly
            feedback = result.get("feedback")
            explanation = result.get("explanation")
            suggested_answer = result.get("suggested_answer") if score < 0.7 else None
            
            return GradingResult(
                score=score,
                feedback=feedback,
                explanation=explanation,
                suggested_answer=suggested_answer
            )
            
        except Exception as e:
            return GradingResult(
                score=0.5,
                feedback=f"Technical issue with AI feedback. Exception: {e}",
                explanation=f"Technical issue with AI explanation. Exception: {e}",
            )
    
    async def _grade_translation(self, request: GradingInput) -> GradingResult:
        """Translation: LLM grades translation quality"""
        try:
            prompt = f"""
            You are an expert English and Chinese teacher for 10-year-old Chinese students.
            You are grading exam translations, so prioritize grammatical accuracy and meaning correspondence.
            
            Original Chinese Text: {request.question_text}
            Student's English Translation: {request.student_answer}
            
            Please evaluate the translation quality based on:
            1. Accuracy of meaning (must match Chinese text exactly)
            2. Grammar and sentence structure in English
            3. Appropriate vocabulary
            
            Examples:
            - Chinese: "我喜欢吃苹果" → Translation: "I like to eat apples" → Score: 1.0 (Perfect)
            - Chinese: "我喜欢吃苹果" → Translation: "I like apples" → Score: 0.9 (Minor simplification, acceptable)
            - Chinese: "我喜欢吃苹果" → Translation: "I like eating apples" → Score: 1.0 (Good alternative)
            - Chinese: "我喜欢吃苹果" → Translation: "I like eat apple" → Score: 0.7 (Grammar errors but meaning clear)
            - Chinese: "我喜欢吃苹果" → Translation: "I like bananas" → Score: 0.2 (Wrong meaning but correct grammar)
            
            Scoring:
            - 1.0: Perfect translation with accurate meaning and grammar
            - 0.8-0.9: Minor grammatical issues but meaning preserved
            - 0.6-0.7: Some errors but core meaning intact
            - 0.0-0.5: Significant errors or wrong meaning
            
            Note: This is an exam, so be strict about grammar accuracy while allowing reasonable variations.
            
            Provide your evaluation in JSON format:
            {{
                "score": 0.0,
                "feedback": "Your feedback here",
                "explanation": "Your explanation here"
            }}
            
            If the score is below 0.7, also include a "good_translation" field with a better translation.
            """
            
            response_text = await self._call_llm(prompt)
            
            # Clean up response text - remove markdown code block formatting if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove ```
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            score = float(result.get("score"))
            feedback = result.get("feedback")
            explanation = result.get("explanation")
            suggested_answer = result.get("good_translation") if score < 0.7 else None
            
            return GradingResult(
                score=score,
                feedback=feedback,
                explanation=explanation,
                suggested_answer=suggested_answer
            )
            
        except Exception as e:
            return GradingResult(
                score=0.5,
                feedback=f"Technical issue with AI feedback. Exception: {e}",
                explanation=f"Technical issue with AI explanation. Exception: {e}"
            )
    
    async def _call_llm(self, prompt: str) -> str:
        """Make a call to the LLM API using aiohttp with streaming"""
        try:
            print("Making API call...")
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert English and Math teacher for 10-year-old Chinese students. You use plain English that even non-native students can understand."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8,
                "stream": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60.0)
                ) as response:
                    
                    if response.status == 200:
                        content = ""
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line.startswith("data: ") and line != "data: [DONE]":
                                try:
                                    data = json.loads(line[6:])
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            content += delta["content"]
                                except json.JSONDecodeError:
                                    continue
                        return content
                    else:
                        error_text = await response.text()
                        print(f"Error response: {error_text}")
                        raise Exception(f"API returned status {response.status}: {error_text}")
            
        except Exception as e:
            print(f"API call failed: {e}")
            raise


if __name__ == "__main__":    
    pass
    
