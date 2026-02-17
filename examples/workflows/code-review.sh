#!/bin/bash
# Code Review Workflow Example
# Systematic code review using ollama-sgpt with sessions and context

set -e

echo "=== Code Review Workflow ==="
echo

# Configuration
REVIEW_SESSION="code-review-$(date +%Y%m%d-%H%M)"
MODEL="codellama"
TARGET_DIR="${1:-.}"  # Default to current directory

echo "Review Session: $REVIEW_SESSION"
echo "Target Directory: $TARGET_DIR"
echo "Model: $MODEL"
echo

# Step 1: Overview
echo "Step 1: Getting overview of codebase"
ollama-sgpt --session "$REVIEW_SESSION" \
  --model "$MODEL" \
  "I'm about to review a codebase. What should I look for in a code review?"

echo
read -p "Press Enter to continue..."
echo

# Step 2: Review Python files
echo "Step 2: Reviewing Python files"
for pyfile in "$TARGET_DIR"/*.py; do
  if [ -f "$pyfile" ]; then
    echo "Reviewing: $pyfile"
    ollama-sgpt --session "$REVIEW_SESSION" \
      --context "$pyfile" \
      "Review this Python file for:"$'\n'"- Code quality"$'\n'"- Potential bugs"$'\n'"- Security issues"$'\n'"- Performance concerns"
    echo
    echo "---"
    echo
  fi
done

# Step 3: Review tests
echo "Step 3: Checking test coverage"
if [ -d "tests" ]; then
  ollama-sgpt --session "$REVIEW_SESSION" \
    --context tests/*.py \
    "Analyze these test files. Are there gaps in test coverage?"
else
  ollama-sgpt --session "$REVIEW_SESSION" \
    "I don't see a tests directory. What tests should be added?"
fi

echo
read -p "Press Enter to continue..."
echo

# Step 4: Security review
echo "Step 4: Security analysis"
ollama-sgpt --session "$REVIEW_SESSION" \
  "Based on the code we've reviewed, what are the top security concerns?"

echo
read -p "Press Enter to continue..."
echo

# Step 5: Summary report
echo "Step 5: Generating summary"
ollama-sgpt --session "$REVIEW_SESSION" \
  "Summarize all the issues found in this review with priority levels (Critical/High/Medium/Low)"

echo
echo "=== Review Complete ==="
echo
echo "Session: $REVIEW_SESSION"
echo
echo "Generate report:"
echo "  ollama-sgpt --session $REVIEW_SESSION '/history' > review-report.md"
echo
echo "Continue review:"
echo "  ollama-sgpt --session $REVIEW_SESSION --context file.py \"review this\""
