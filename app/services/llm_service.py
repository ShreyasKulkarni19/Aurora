"""Service for LLM-based answer generation."""

import json
from typing import List, Tuple
from openai import AsyncOpenAI
from app.models import Message
from app.config import settings
from app.utils.exceptions import LLMError
from app.utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


class LLMService:
    """Service for generating answers using LLM."""
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LLM client based on provider."""
        if self.provider == "openai":
            if not settings.openai_api_key:
                raise LLMError("OpenAI API key not configured")
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            # TODO: Implement Anthropic client
            raise LLMError("Anthropic provider not yet implemented")
        else:
            raise LLMError(f"Unsupported LLM provider: {self.provider}")
    
    def _build_prompt(
        self,
        question: str,
        relevant_messages: List[Tuple[Message, float]]
    ) -> str:
        """
        Build a prompt for the LLM.
        
        Args:
            question: User's question
            relevant_messages: List of (message, score) tuples
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are a helpful assistant that answers questions based on provided message data.",
            "Analyze the following messages and answer the question concisely.",
            "",
            "Question:",
            question,
            "",
            "Relevant Messages:",
        ]
        
        for idx, (message, score) in enumerate(relevant_messages, 1):
            message_text = self._format_message_for_prompt(message)
            prompt_parts.append(f"\n[{idx}] (relevance: {score:.3f})")
            prompt_parts.append(message_text)
        
        prompt_parts.extend([
            "",
            "Instructions:",
            "1. Extract the specific answer from the messages above.",
            "2. If the answer is not found, respond with 'I could not find an answer to this question in the available messages.'",
            "3. Be concise and direct. Only provide the answer, no additional explanation.",
            "4. Return your response as a JSON object with a single 'answer' field.",
            "",
            "Response (JSON only):"
        ])
        
        return "\n".join(prompt_parts)
    
    def _format_message_for_prompt(self, message: Message) -> str:
        """Format a message for inclusion in the prompt."""
        parts = []
        if message.user_name:
            parts.append(f"From: {message.user_name}")
        if message.user_id:
            parts.append(f"User ID: {message.user_id}")
        if message.message:
            parts.append(f"Message: {message.message}")
        if message.timestamp:
            parts.append(f"Time: {message.timestamp}")
        return "\n".join(parts)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_answer(
        self,
        question: str,
        relevant_messages: List[Tuple[Message, float]]
    ) -> str:
        """
        Generate an answer using the LLM.
        
        Args:
            question: User's question
            relevant_messages: List of (message, score) tuples
            
        Returns:
            Answer string
        """
        try:
            logger.info(
                "Generating answer with LLM",
                provider=self.provider,
                question=question,
                num_messages=len(relevant_messages)
            )
            
            prompt = self._build_prompt(question, relevant_messages)
            
            if self.provider == "openai":
                # Prepare request parameters
                request_params = {
                    "model": settings.openai_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions based on provided data. Always respond with valid JSON containing an 'answer' field."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": settings.openai_temperature,
                    "max_tokens": settings.openai_max_tokens,
                }
                
                # Add JSON mode for supported models
                # JSON mode is supported in gpt-4-turbo, gpt-4-1106-preview, gpt-3.5-turbo-1106 and later
                json_mode_models = ["gpt-4-turbo", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-3.5-turbo-1106"]
                if any(model in settings.openai_model for model in json_mode_models):
                    try:
                        request_params["response_format"] = {"type": "json_object"}
                    except Exception:
                        # If response_format is not supported, continue without it
                        pass
                
                response = await self.client.chat.completions.create(**request_params)
                
                answer_text = response.choices[0].message.content
                
                # Parse JSON response
                try:
                    answer_data = json.loads(answer_text)
                    answer = answer_data.get("answer", answer_text)
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract answer from text
                    # Sometimes LLM returns answer without JSON wrapper
                    cleaned_text = answer_text.strip()
                    # Remove markdown code blocks if present
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text[7:]
                    if cleaned_text.startswith("```"):
                        cleaned_text = cleaned_text[3:]
                    if cleaned_text.endswith("```"):
                        cleaned_text = cleaned_text[:-3]
                    cleaned_text = cleaned_text.strip()
                    
                    # Try parsing again
                    try:
                        answer_data = json.loads(cleaned_text)
                        answer = answer_data.get("answer", cleaned_text)
                    except json.JSONDecodeError:
                        # If still can't parse, use the raw response
                        logger.warning("Failed to parse LLM response as JSON, using raw text")
                        answer = cleaned_text
                
                logger.info("Successfully generated answer", answer_length=len(answer))
                return answer
            
            else:
                raise LLMError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(
                "Failed to generate answer",
                error=str(e),
                error_type=type(e).__name__
            )
            raise LLMError(f"Failed to generate answer: {str(e)}")

