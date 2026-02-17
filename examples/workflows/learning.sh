#!/bin/bash
# Learning Workflow Example
# Structured learning session with ollama-sgpt

set -e

echo "=== Learning Workflow with ollama-sgpt ==="
echo

# Configuration
TOPIC="${1:-Docker}"
SESSION="learn-$(echo $TOPIC | tr '[:upper:]' '[:lower:]' | tr ' ' '-')"
MODEL="llama3"

echo "Learning Topic: $TOPIC"
echo "Session: $SESSION"
echo "Model: $MODEL"
echo

# Step 1: Introduction
echo "Step 1: Introduction to $TOPIC"

ollama-sgpt --session "$SESSION" \
  "I want to learn about $TOPIC. Give me a brief overview and explain why it's important."

echo
read -p "Press Enter to continue..."
echo

# Step 2: Key Concepts
echo "Step 2: Core concepts"

ollama-sgpt --session "$SESSION" \
  "What are the key concepts I need to understand about $TOPIC?"

echo
read -p "Press Enter to continue..."
echo

# Step 3: Hands-on Example
echo "Step 3: Practical example"

ollama-sgpt --session "$SESSION" \
  --code \
  "Show me a simple, practical example of using $TOPIC"

echo
read -p "Ready to try the example? (y/n): "
read -r try_example
echo

if [ "$try_example" = "y" ]; then
  echo "Asking for step-by-step guidance..."
  ollama-sgpt --session "$SESSION" \
    --shell \
    "Give me step-by-step commands to try this $TOPIC example"
fi

echo
read -p "Press Enter to continue..."
echo

# Step 4: Common Pitfalls
echo "Step 4: Common mistakes"

ollama-sgpt --session "$SESSION" \
  "What are common mistakes beginners make with $TOPIC and how to avoid them?"

echo
read -p "Press Enter to continue..."
echo

# Step 5: Best Practices
echo "Step 5: Best practices"

ollama-sgpt --session "$SESSION" \
  "What are the best practices for using $TOPIC in production?"

echo
read -p "Press Enter to continue..."
echo

# Step 6: Additional Resources
echo "Step 6: Further learning"

ollama-sgpt --session "$SESSION" \
  "What resources (documentation, tutorials, books) would you recommend for learning more about $TOPIC?"

echo
read -p "Press Enter to continue..."
echo

# Step 7: Practice Exercise
echo "Step 7: Practice challenge"

ollama-sgpt --session "$SESSION" \
  "Suggest a practice project or exercise to reinforce my understanding of $TOPIC"

echo
echo "=== Learning Session Complete ==="
echo
echo "Session: $SESSION"
echo
echo "Review your learning:"
echo "  ollama-sgpt -s $SESSION '/history'"
echo
echo "Continue learning:"
echo "  ollama-sgpt -s $SESSION \"explain [specific concept]\""
echo
echo "Get quiz questions:"
echo "  ollama-sgpt -s $SESSION \"quiz me on $TOPIC fundamentals\""
echo
echo "Generate study notes:"
echo "  ollama-sgpt -s $SESSION \"create study notes\" > $TOPIC-notes.md"
