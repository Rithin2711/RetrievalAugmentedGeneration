#!/bin/bash
cd /home/kavia/workspace/code-generation/RetrievalAugmentedGeneration/Gemini_RAGMonolithicApplication

# Check if virtual environment exists, if not use system flake8
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Use flake8 from PATH (either from venv or system)
flake8 . --exclude=venv,__pycache__,.git --max-line-length=88 --ignore=E203,W503
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

