import os
import logging
from pathlib import Path
from typing import List, Optional, Dict
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables from .env file with robust path handling
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Set up logging
logger = logging.getLogger(__name__)

# Check for .env file and log warning if missing
if not env_path.exists():
    logger.warning(f".env file not found at {env_path}. Environment variables must be set externally.")
    print(f"WARNING: .env file not found at {env_path}. Environment variables must be set externally.")

from .models import ChatMessage, SearchResult

# PUBLIC_INTERFACE
class GeminiService:
    """
    Service for interacting with the Google Gemini API (Generative AI).
    The API key is securely loaded from environment variables.
    """
    def __init__(self):
        """Initialize Gemini API service by retrieving API key from environment variables."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            error_msg = (
                "GEMINI_API_KEY environment variable is required but not found. "
                "Please ensure:\n"
                "1. A .env file exists in the project root with GEMINI_API_KEY=your_api_key\n"
                "2. Or set the GEMINI_API_KEY environment variable in your system\n"
                f"3. Current .env file path: {Path(__file__).parent.parent / '.env'}"
            )
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        logger.info("GEMINI_API_KEY successfully loaded from environment variables")
        genai.configure(api_key=api_key)
        # Configure model
        self.model_name = "gemini-1.5-flash"
        self.model = genai.GenerativeModel(self.model_name)
        # Safety settings (allow most content for document analysis)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        # Generation config
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

    def _format_context(self, search_results: List[SearchResult]) -> str:
        """Format search results into context for the model."""
        if not search_results:
            return ""
        context_parts = []
        context_parts.append("=== RELEVANT DOCUMENT CONTEXT ===\n")
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"Context {i} (relevance: {result.score:.2f}):")
            context_parts.append(result.content)
            context_parts.append("")  # Empty line for separation
        context_parts.append("=== END CONTEXT ===\n")
        return "\n".join(context_parts)
    
    def _build_conversation_history(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """Build conversation history for Gemini API."""
        history = []
        for message in messages[-10:]:  # Use last 10 messages for context
            if message.role == "user":
                history.append({
                    "role": "user",
                    "parts": [message.content]
                })
            elif message.role == "assistant":
                history.append({
                    "role": "model",
                    "parts": [message.content]
                })
        return history

    # PUBLIC_INTERFACE
    def generate_response(
        self,
        user_message: str,
        context: Optional[List[SearchResult]] = None,
        conversation_history: Optional[List[ChatMessage]] = None
    ) -> str:
        """
        Generate a response using Gemini API with optional context.

        Args:
            user_message (str): The user's question or input.
            context (Optional[List[SearchResult]]): List of relevant search results to include as context.
            conversation_history (Optional[List[ChatMessage]]): Recent conversation history for context.

        Returns:
            str: The generated response from Gemini.

        Raises:
            Exception: If the Gemini API call fails or is misconfigured.
        """
        try:
            # Build the prompt
            prompt_parts = []
            # Add system instruction
            system_prompt = (
                "You are a helpful AI assistant that answers questions based on provided documents and context.\n\n"
                "Guidelines:\n"
                "- Use the provided context to answer questions accurately\n"
                "- If the context doesn't contain relevant information, say so clearly\n"
                "- Be concise but comprehensive in your responses\n"
                "- If asked about something not in the context, use your general knowledge but mention the limitation\n"
                "- Always be helpful and professional"
            )
            prompt_parts.append(system_prompt)

            # Add document context if available
            if context:
                formatted_context = self._format_context(context)
                prompt_parts.append(formatted_context)

            # Add conversation history
            if conversation_history:
                prompt_parts.append("\n=== CONVERSATION HISTORY ===")
                for msg in conversation_history[-5:]:  # Last 5 messages
                    prompt_parts.append(f"{msg.role.upper()}: {msg.content}")
                prompt_parts.append("=== END HISTORY ===\n")

            # Add current user message
            prompt_parts.append(f"USER QUESTION: {user_message}")

            # Generate response
            full_prompt = "\n".join(prompt_parts)

            response = self.model.generate_content(
                full_prompt,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config
            )

            if hasattr(response, "text") and response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

    # PUBLIC_INTERFACE
    def generate_session_title(self, first_message: str, response: str) -> str:
        """
        Generate a concise title for a chat session based on the initial user message and response.

        Args:
            first_message (str): The user's first message in the session.
            response (str): The assistant's first response.

        Returns:
            str: A concise session title.
        """
        try:
            prompt = (
                f"Generate a concise, descriptive title (4-8 words) for a chat session based on this exchange:\n\n"
                f"User: {first_message[:200]}...\n"
                f"Assistant: {response[:200]}...\n\n"
                "Title should capture the main topic or question. Return only the title, no quotes or additional text."
            )
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 50,
                }
            )
            if hasattr(response, "text") and response.text:
                title = response.text.strip().strip('"\'')

                return title[:100]  # Limit length
            else:
                return "Chat Session"
                
        except Exception as e:
            print(f"Error generating title: {e}")
            return "Chat Session"

    # PUBLIC_INTERFACE
    def summarize_document(self, text: str, max_length: int = 500) -> str:
        """
        Generate a summary of the provided document content.

        Args:
            text (str): The text content to summarize.
            max_length (int): Maximum length of the summary in characters.

        Returns:
            str: The document summary.
        """
        try:
            prompt = (
                f"Please provide a concise summary of the following document content in {max_length} characters or less:\n\n"
                f"{text[:2000]}...\n\n"
                "Focus on the key points, main topics, and important information."
            )
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": max_length // 4,  # Rough estimate
                }
            )
            if hasattr(response, "text") and response.text:
                return response.text.strip()[:max_length]
            else:
                return "Document summary not available."
                
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary generation failed."

# Global instance
gemini_service = GeminiService()
