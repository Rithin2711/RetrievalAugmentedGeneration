import os
from typing import List, Optional, Dict
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .models import ChatMessage, SearchResult

class GeminiService:
    def __init__(self):
        """Initialize Gemini API service"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
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
        """Format search results into context for the model"""
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
        """Build conversation history for Gemini API"""
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
        """Generate response using Gemini API with optional context"""
        
        try:
            # Build the prompt
            prompt_parts = []
            
            # Add system instruction
            system_prompt = """You are a helpful AI assistant that answers questions based on provided documents and context. 
            
            Guidelines:
            - Use the provided context to answer questions accurately
            - If the context doesn't contain relevant information, say so clearly
            - Be concise but comprehensive in your responses
            - If asked about something not in the context, use your general knowledge but mention the limitation
            - Always be helpful and professional"""
            
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
            
            if response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

    # PUBLIC_INTERFACE
    def generate_session_title(self, first_message: str, response: str) -> str:
        """Generate a concise title for a chat session"""
        try:
            prompt = f"""Generate a concise, descriptive title (4-8 words) for a chat session based on this exchange:

User: {first_message[:200]}...
Assistant: {response[:200]}...

Title should capture the main topic or question. Return only the title, no quotes or additional text."""
            
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 50,
                }
            )
            
            if response.text:
                title = response.text.strip().strip('"\'')
                return title[:100]  # Limit length
            else:
                return "Chat Session"
                
        except Exception as e:
            print(f"Error generating title: {e}")
            return "Chat Session"

    # PUBLIC_INTERFACE
    def summarize_document(self, text: str, max_length: int = 500) -> str:
        """Generate a summary of document content"""
        try:
            prompt = f"""Please provide a concise summary of the following document content in {max_length} characters or less:

{text[:2000]}...

Focus on the key points, main topics, and important information."""
            
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": max_length // 4,  # Rough estimate
                }
            )
            
            if response.text:
                return response.text.strip()[:max_length]
            else:
                return "Document summary not available."
                
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary generation failed."

# Global instance
gemini_service = GeminiService()
