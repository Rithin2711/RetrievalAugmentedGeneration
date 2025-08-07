#!/usr/bin/env python3
"""
Startup script for the Gemini RAG FastAPI application.
This script ensures environment variables are loaded before importing any modules.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

def main():
    """Main function to start the server"""
    import uvicorn
    
    # Verify GEMINI_API_KEY is loaded
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set!")
        print("Please check your .env file.")
        sys.exit(1)
    
    print(f"✓ GEMINI_API_KEY loaded successfully (length: {len(api_key)})")
    
    # Start the FastAPI server
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"]
    )

if __name__ == "__main__":
    main()
