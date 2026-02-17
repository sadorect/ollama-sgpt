#!/bin/bash
# Development Workflow Example
# Demonstrates using ollama-sgpt for daily development tasks

set -e

echo "=== Development Workflow with ollama-sgpt ==="
echo

# Configuration
SESSION="dev-$(date +%Y%m%d)"
MODEL="codellama"

echo "Starting development session: $SESSION"
echo "Using model: $MODEL"
echo

# Step 1: Project Setup
echo "Step 1: Getting project setup guidance"
ollama-sgpt --session "$SESSION" \
  --model "$MODEL" \
  "I'm starting a new Python web API project. What's the recommended project structure?"

echo
read -p "Press Enter to continue..."
echo

# Step 2: Code Generation
echo "Step 2: Generating boilerplate code"
ollama-sgpt --session "$SESSION" \
  --model "$MODEL" \
  --code \
  "Generate a basic FastAPI app with health check endpoint"

echo
read -p "Press Enter to continue..."
echo

# Step 3: Code Review (assumes main.py exists)
if [ -f "main.py" ]; then
  echo "Step 3: Reviewing main.py"
  ollama-sgpt --session "$SESSION" \
    --context main.py \
    "Review this code for best practices and potential issues"
else
  echo "Step 3: Skipped (main.py not found)"
fi

echo
read -p "Press Enter to continue..."
echo

# Step 4: Testing Guidance
echo "Step 4: Getting testing advice"
ollama-sgpt --session "$SESSION" \
  "What unit tests should I write for a REST API? Show me an example with pytest."

echo
read -p "Press Enter to continue..."
echo

# Step 5: Shell Commands (with execution)
echo "Step 5: Setting up virtual environment"
ollama-sgpt --session "$SESSION" \
  --shell --execute \
  "create Python virtual environment and activate it"

echo
echo "=== Workflow Complete ==="
echo
echo "Session saved as: $SESSION"
echo "View conversation history:"
echo "  ollama-sgpt --session $SESSION '/history'"
echo
echo "Continue working:"
echo "  ollama-sgpt --session $SESSION \"your next question\""
