#!/bin/bash
# WAYGATE-MCP TASKWARRIOR DASHBOARD
# Comprehensive project status for user waygateai

clear
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    WAYGATE-MCP FORENSIC DASHBOARD        ║"
echo "║                        $(date +%Y-%m-%d)                           ║"
echo "║                                                          ║"
echo "║  User: waygateai | Project: waygate-mcp                 ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Health Score Calculation
TOTAL=$(task project:waygate-mcp status:pending count 2>/dev/null || echo "0")
CRITICAL=$(task project:waygate-mcp +CRITICAL status:pending count 2>/dev/null || echo "0")
HIGH=$(task project:waygate-mcp +HIGH status:pending count 2>/dev/null || echo "0")
SECURITY=$(task project:waygate-mcp +SECURITY status:pending count 2>/dev/null || echo "0")
COMPLETED=$(task project:waygate-mcp status:completed count 2>/dev/null || echo "0")

echo ""
echo "🏥 REPOSITORY HEALTH SCORE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$SECURITY" -gt 0 ]; then
  echo "Status: 🔴 SECURITY CRITICAL - IMMEDIATE ACTION REQUIRED"
elif [ "$CRITICAL" -gt 0 ]; then
  echo "Status: 🔴 CRITICAL - SERVER CANNOT START"
elif [ "$HIGH" -gt 3 ]; then
  echo "Status: 🟠 UNSTABLE - MAJOR FUNCTIONALITY MISSING"
elif [ "$HIGH" -gt 0 ]; then
  echo "Status: 🟡 DEGRADED - MINOR ISSUES PRESENT"
else
  echo "Status: 🟢 HEALTHY - ALL SYSTEMS OPERATIONAL"
fi

echo ""
echo "📊 TASK METRICS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total Pending Tasks: $TOTAL"
echo "🚨 Security Issues: $SECURITY"
echo "🔴 Critical Issues: $CRITICAL"
echo "🟠 High Priority: $HIGH"
echo "✅ Completed: $COMPLETED"

if [ "$TOTAL" -gt 0 ] && [ "$COMPLETED" -gt 0 ]; then
  COMPLETION_RATE=$((COMPLETED * 100 / (TOTAL + COMPLETED)))
  echo "📈 Completion Rate: ${COMPLETION_RATE}%"
else
  echo "📈 Completion Rate: 0%"
fi

echo ""
echo "🎯 IMMEDIATE ACTIONS (Critical Path)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
task project:waygate-mcp +CRITICAL status:pending rc.report.next.columns:id,description,fix_time rc.report.next.labels:"ID,Critical Issue,Est.Time" 2>/dev/null || echo "No critical tasks found"

echo ""
echo "🔐 SECURITY ALERTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
task project:waygate-mcp +SECURITY status:pending rc.report.next.columns:id,description,fix_time rc.report.next.labels:"ID,Security Issue,Est.Time" 2>/dev/null || echo "No security issues found"

echo ""
echo "🚧 BLOCKED TASKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
task project:waygate-mcp status:pending has:depends rc.report.next.columns:id,depends,description rc.report.next.labels:"ID,Depends,Task" 2>/dev/null || echo "No blocked tasks"

echo ""
echo "⏱️ TIME INVESTMENT ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -n "Total Estimated Fix Time: "
task project:waygate-mcp status:pending export | jq -r '.[].fix_time' 2>/dev/null | sed 's/min//' | awk '{sum += $1} END {print sum " minutes (" sum/60 " hours)"}' 2>/dev/null || echo "Unable to calculate"

echo ""
echo "📋 COMPONENT BREAKDOWN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for component in dependencies server security tools database testing documentation; do
  count=$(task project:waygate-mcp mcp_component:$component status:pending count 2>/dev/null || echo "0")
  if [ "$count" -gt 0 ]; then
    echo "$component: $count tasks"
  fi
done

echo ""
echo "🔄 NEXT ACTIONS (Ready to Execute)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
task project:waygate-mcp status:pending -depends: limit:5 rc.report.next.columns:id,urgency,description,fix_time rc.report.next.labels:"ID,Priority,Action,Time" 2>/dev/null || echo "No unblocked tasks ready"

echo ""
echo "📈 QUICK WINS (≤5min fixes)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
task project:waygate-mcp status:pending fix_time.under:6min rc.report.next.columns:id,description,fix_time rc.report.next.labels:"ID,Quick Fix,Time" 2>/dev/null || echo "No quick fixes available"

echo ""
echo "📅 TODAY'S FOCUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
task project:waygate-mcp due:today status:pending rc.report.next.columns:id,description,fix_time,pr_title rc.report.next.labels:"ID,Task,Time,PR Title" 2>/dev/null || echo "No tasks due today"

echo ""
echo "🔗 EXECUTION COMMANDS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Start first critical task: task \$(task project:waygate-mcp +CRITICAL limit:1 ids) start"
echo "View critical context:     task context mcp-critical"
echo "Mark task complete:        task [ID] done"
echo "View next ready task:      task project:waygate-mcp ready next"
echo "Generate report:           ./scripts/dashboard.sh > reports/\$(date +%Y%m%d)-waygate-mcp.txt"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  CRITICAL PATH: Fix dependencies → Install FastAPI →     ║"
echo "║  Resolve imports → Fix endpoints → Implement MCP tools   ║"
echo "║                                                          ║"
echo "║  USER: waygateai | PROJECT: waygate-mcp                 ║"
echo "╚══════════════════════════════════════════════════════════╝"