#!/bin/bash
# Bug Fixing Workflow Example
# Systematic debugging approach with ollama-sgpt

set -e

echo "=== Bug Fixing Workflow ==="
echo

# Configuration
BUG_ID="${1:-unknown}"
SESSION="bug-$BUG_ID"
LOG_FILE="${2:-error.log}"

echo "Bug ID: $BUG_ID"
echo "Session: $SESSION"
echo "Log File: $LOG_FILE"
echo

# Step 1: Understand the bug
echo "Step 1: Describing the bug"
echo "Enter bug description (or press Enter to skip):"
read -r bug_description

if [ -n "$bug_description" ]; then
  ollama-sgpt --session "$SESSION" \
    "I'm investigating a bug: $bug_description. What information do I need to collect?"
fi

echo
read -p "Press Enter to continue..."
echo

# Step 2: Analyze error logs
echo "Step 2: Analyzing error logs"

if [ -f "$LOG_FILE" ]; then
  echo "Reading $LOG_FILE..."
  ollama-sgpt --session "$SESSION" \
    --context "$LOG_FILE" \
    "Analyze this error log. What's the root cause?"
else
  echo "Note: $LOG_FILE not found"
  echo "Please provide error message:"
  read -r error_msg
  if [ -n "$error_msg" ]; then
    ollama-sgpt --session "$SESSION" \
      "Error message: $error_msg. What could cause this?"
  fi
fi

echo
read -p "Press Enter to continue..."
echo

# Step 3: Review relevant code
echo "Step 3: Code investigation"
echo "Enter path to problematic file (or press Enter to skip):"
read -r code_file

if [ -f "$code_file" ]; then
  ollama-sgpt --session "$SESSION" \
    --context "$code_file" \
    "Based on the error we discussed, where is the bug in this code?"
fi

echo
read -p "Press Enter to continue..."
echo

# Step 4: Reproduce the bug
echo "Step 4: Reproduction steps"

ollama-sgpt --session "$SESSION" \
  "How can I reliably reproduce this bug? What test case should I write?"

echo
read -p "Press Enter to continue..."
echo

# Step 5: Solution proposal
echo "Step 5: Finding solution"

ollama-sgpt --session "$SESSION" \
  --code \
  "Suggest a fix for this bug with code examples"

echo
read -p "Press Enter to continue..."
echo

# Step 6: Testing strategy
echo "Step 6: Verification plan"

ollama-sgpt --session "$SESSION" \
  "How should I test the fix to ensure:"$'\n'"1. The bug is resolved"$'\n'"2. No new issues introduced"$'\n'"3. Edge cases are covered"

echo
read -p "Press Enter to continue..."
echo

# Step 7: Implementation
echo "Step 7: Applying the fix"
echo "Review the suggested solution above, then:"
echo "  1. Implement the fix"
echo "  2. Run tests"
echo "  3. Return here"
echo
read -p "Press Enter when ready to verify..."
echo

ollama-sgpt --session "$SESSION" \
  "I've implemented the fix. What should I check to confirm it's working?"

echo
echo "=== Bug Fixing Complete ==="
echo
echo "Session: $SESSION"
echo
echo "Documentation:"
echo "  # Generate bug report"
echo "  ollama-sgpt -s $SESSION \"summarize root cause and fix\" > bug-$BUG_ID-report.md"
echo
echo "  # Update tests"
echo "  ollama-sgpt -s $SESSION --code \"write test for this bug\" > test_bug_$BUG_ID.py"
