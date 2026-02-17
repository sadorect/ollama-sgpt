#!/bin/bash
# Data Analysis Workflow Example
# Using ollama-sgpt for data exploration and analysis

set -e

echo "=== Data Analysis Workflow ==="
echo

# Configuration
SESSION="data-analysis-$(date +%Y%m%d)"
DATA_FILE="${1:-data.csv}"

echo "Session: $SESSION"
echo "Data File: $DATA_FILE"
echo

# Step 1: Initial exploration
echo "Step 1: Understanding the data"

if [ -f "$DATA_FILE" ]; then
  echo "Loading data file..."
  ollama-sgpt --session "$SESSION" \
    --context "$DATA_FILE" \
    "Describe this dataset. What columns does it have? What kind of data is this?"
else
  echo "Warning: $DATA_FILE not found. Using sample questions."
  ollama-sgpt --session "$SESSION" \
    "I have a CSV file with sales data (date, product, quantity, revenue). What should I analyze first?"
fi

echo
read -p "Press Enter to continue..."
echo

# Step 2: Analysis strategy
echo "Step 2: Planning the analysis"

ollama-sgpt --session "$SESSION" \
  "What are the key metrics and visualizations I should create for this sales data?"

echo
read -p "Press Enter to continue..."
echo

# Step 3: Generate analysis code
echo "Step 3: Generating Python code for analysis"

ollama-sgpt --session "$SESSION" \
  --model codellama \
  --code \
  "Write Python code using pandas to:"$'\n'"1. Load the CSV"$'\n'"2. Show basic statistics"$'\n'"3. Group by product and sum revenue"$'\n'"4. Find top 5 products"

echo
read -p "Press Enter to continue..."
echo

# Step 4: Visualization
echo "Step 4: Creating visualizations"

ollama-sgpt --session "$SESSION" \
  --model codellama \
  --code \
  "Write Python code to create a bar chart of revenue by product using matplotlib"

echo
read -p "Press Enter to continue..."
echo

# Step 5: Statistical analysis
echo "Step 5: Statistical insights"

ollama-sgpt --session "$SESSION" \
  "What statistical tests should I run to find significant trends in sales over time?"

echo
read -p "Press Enter to continue..."
echo

# Step 6: Report generation
echo "Step 6: Generating report"

ollama-sgpt --session "$SESSION" \
  "Create an outline for a data analysis report with sections for methodology, findings, and recommendations"

echo
echo "=== Analysis Workflow Complete ==="
echo
echo "Session: $SESSION"
echo
echo "Next steps:"
echo "  # Generate analysis script"
echo "  ollama-sgpt -s $SESSION --code \"complete Python script\" > analysis.py"
echo
echo "  # Get visualization ideas"
echo "  ollama-sgpt -s $SESSION \"suggest additional visualizations\""
echo
echo "  # Export report"
echo "  ollama-sgpt -s $SESSION \"format findings as markdown report\" > report.md"
