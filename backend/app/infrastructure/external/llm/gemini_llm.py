from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.domain.external.llm import LLM
from app.infrastructure.config import get_settings
import logging

logger = logging.getLogger(__name__)

class GeminiLLM(LLM):
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.api_key

        # Configure the generative AI client
        genai.configure(api_key=self.api_key)

        self._model_name = settings.model_name
        self._temperature = settings.temperature
        self._max_tokens = settings.max_tokens

        # Create the generative model instance
        self.model = genai.GenerativeModel(self._model_name)

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
            # Create the generation configuration
            generation_config = genai.types.GenerationConfig(
                temperature=self._temperature,
                max_output_tokens=self._max_tokens
            )

            # Send the request to the model
            response = self.model.generate_content(
                contents=messages,
                generation_config=generation_config,
                tools=tools
            )

            # Extract the response data
            response_data = {
                "role": response.candidates[0].content.role,
                "content": response.candidates[0].content.parts[0].text
            }

            return response_data
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            raise
