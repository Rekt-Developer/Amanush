from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.domain.external.llm import LLM
from app.infrastructure.config import get_settings
import logging

logger = logging.getLogger(__name__)

class GeminiLLM(LLM):
    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        
        self._model_name = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens
        
        self.client = genai.GenerativeModel(
            model_name=self._model_name,
            generation_config={
                "temperature": self._temperature,
                "max_output_tokens": self._max_tokens,
            }
        )
        logger.info(f"Initialized Gemini LLM with model: {self._model_name}")

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    async def ask(self, messages: List[Dict[str, str]],
                tools: Optional[List[Dict[str, Any]]] = None,
                response_format: Optional[Dict[str, Any]] = None,
                tool_choice: Optional[str] = None) -> Dict[str, Any]:
        """Send chat request to Gemini API"""
        try:
            logger.debug(f"Sending request to Gemini, model: {self._model_name}")
            
            # Convert messages to the format expected by Gemini
            gemini_messages = self._convert_messages_to_gemini_format(messages)
            
            response = await self.client.generate_content_async(
                gemini_messages,
                tools=tools,
            )
            
            # Extract the response content
            response_text = response.candidates[0].content.parts[0].text
            
            # Format the response to match the expected output format
            return {
                "content": response_text,
                "role": "assistant"
            }
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise

    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        gemini_messages = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            
            if role == "user":
                gemini_messages.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [{"text": content}]})
        
        return gemini_messages
