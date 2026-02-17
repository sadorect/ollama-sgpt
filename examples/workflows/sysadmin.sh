#!/bin/bash
# System Administration Workflow Example
# Using ollama-sgpt for server management and troubleshooting

set -e

echo "=== Sysadmin Workflow with ollama-sgpt ==="
echo

# Configuration
SESSION="sysadmin-$(date +%Y%m%d)"
MODEL="llama3"

echo "Session: $SESSION"
echo "Model: $MODEL"
echo

# Step 1: System Health Check
echo "Step 1: System health check"
echo "Getting guidance on system diagnostics..."

ollama-sgpt --session "$SESSION" \
  --shell --execute --yes \
  "show system resources (CPU, memory, disk)"

echo
read -p "Press Enter to continue..."
echo

# Step 2: Log Analysis
echo "Step 2: Analyzing system logs"

if [ -f "/var/log/syslog" ]; then
  echo "Analyzing /var/log/syslog..."
  tail -n 100 /var/log/syslog | ollama-sgpt --session "$SESSION" \
    "Analyze these system logs. Are there any critical errors or warnings?"
else
  echo "Note: /var/log/syslog not accessible (may need sudo)"
fi

echo
read -p "Press Enter to continue..."
echo

# Step 3: Service Status
echo "Step 3: Checking service status"

ollama-sgpt --session "$SESSION" \
  --shell --execute --yes \
  "show status of all systemd services"

echo
read -p "Press Enter to continue..."
echo

# Step 4: Network Diagnostics
echo "Step 4: Network diagnostics"

ollama-sgpt --session "$SESSION" \
  --shell --execute \
  "check network connectivity and open ports"

echo
read -p "Press Enter to continue..."
echo

# Step 5: Security Audit
echo "Step 5: Basic security check"

ollama-sgpt --session "$SESSION" \
  --shell --execute --yes \
  "show failed login attempts and active SSH sessions"

echo
read -p "Press Enter to continue..."
echo

# Step 6: Disk Usage Review
echo "Step 6: Disk usage analysis"

ollama-sgpt --session "$SESSION" \
  --shell --execute --yes \
  "find directories using most disk space"

echo
echo "=== Sysadmin Workflow Complete ==="
echo
echo "Session: $SESSION"
echo
echo "Common sysadmin tasks:"
echo "  # Monitor logs"
echo "  tail -f /var/log/syslog | ollama-sgpt \"analyze for errors\""
echo
echo "  # Troubleshoot service"
echo "  ollama-sgpt -s $SESSION --shell \"restart nginx service\""
echo
echo "  # Update system"
echo "  ollama-sgpt -s $SESSION --shell --execute \"update package list\""
