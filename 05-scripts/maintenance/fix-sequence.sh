#!/bin/bash
# WAYGATE-MCP OPTIMAL FIX SEQUENCE GENERATOR
# Creates executable fix sequence based on TaskWarrior dependencies

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                WAYGATE-MCP FIX SEQUENCE                  ║"
echo "║             Optimal Execution Order                     ║"
echo "╚══════════════════════════════════════════════════════════╝"

echo ""
echo "1️⃣ IMMEDIATE BLOCKERS (Must fix first)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
task project:waygate-mcp +CRITICAL status:pending -depends: rc.report.next.columns:id,urgency,description,fix_time rc.report.next.labels:"ID,Priority,Critical Issue,Time"

echo ""
echo "2️⃣ DEPENDENCY RESOLUTION CHAIN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Execute in this exact order:"

# Get tasks with dependencies in order
echo "Task 24: Fix libsql-client version (no dependencies)"
echo "↓"
echo "Task 26: Install FastAPI (depends on 24)"
echo "↓"
echo "Tasks 27,28: Fix server issues (depend on 26)"

echo ""
echo "3️⃣ QUICK WINS (Parallel execution possible)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
task project:waygate-mcp status:pending fix_time.under:6min rc.report.next.columns:id,description,fix_time rc.report.next.labels:"ID,Quick Fix,Time"

echo ""
echo "4️⃣ HIGH IMPACT IMPROVEMENTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
task project:waygate-mcp +HIGH status:pending rc.report.next.columns:id,priority,description,fix_time rc.report.next.labels:"ID,Priority,High Impact,Time"

echo ""
echo "📋 EXECUTION SCRIPT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "# Copy and paste these commands to execute the critical path:"
echo ""
echo "# Step 1: Start first critical task"
echo "task 24 start"
echo "# Fix libsql-client version in requirements.txt"
echo "sed -i 's/libsql-client>=0.4.0/libsql-client>=0.3.1/' requirements.txt"
echo "task 24 done"
echo ""
echo "# Step 2: Install dependencies"
echo "task 26 start"
echo "source venv/bin/activate && pip install -r requirements.txt"
echo "task 26 done"
echo ""
echo "# Step 3: Test server startup"
echo "task 27 start"
echo "# Fix duplicate endpoint in waygate_mcp.py"
echo "task 27 done"
echo ""
echo "# Continue with remaining tasks..."

echo ""
echo "⚡ ESTIMATED TOTAL TIME: $(task project:waygate-mcp status:pending export | jq -r '.[].fix_time' 2>/dev/null | sed 's/min//' | awk '{sum += $1} END {print sum " minutes"}' 2>/dev/null || echo 'Unable to calculate')"