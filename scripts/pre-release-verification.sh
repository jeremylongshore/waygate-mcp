#!/bin/bash
# PRE-RELEASE VERIFICATION CHECKLIST
# Run before executing release to ensure quality standards

set -e
cd "$(dirname "$0")/.."

echo "🔍 WAYGATE MCP v2.1.0 PRE-RELEASE VERIFICATION"
echo "=============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS_COUNT=0
TOTAL_CHECKS=12

check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $1"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}❌ FAIL${NC}: $1"
        echo -e "${YELLOW}⚠️  Fix required before release${NC}"
    fi
}

echo ""
echo "📦 1. VIRTUAL ENVIRONMENT AND DEPENDENCIES"
echo "-------------------------------------------"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ PASS${NC}: Virtual environment exists"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌ FAIL${NC}: Virtual environment missing"
fi

# Check if virtual environment is activated and dependencies work
source venv/bin/activate 2>/dev/null || {
    echo -e "${RED}❌ FAIL${NC}: Cannot activate virtual environment"
    exit 1
}

# Test dependency installation
pip check >/dev/null 2>&1
check_status "All dependencies properly installed"

echo ""
echo "🧪 2. SERVER STARTUP AND BASIC FUNCTIONALITY"
echo "--------------------------------------------"

# Test server can start without errors
timeout 10s python -m source.waygate_mcp --port 8001 --env development >/dev/null 2>&1 &
SERVER_PID=$!
sleep 3

# Check if server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${GREEN}✅ PASS${NC}: Server starts successfully"
    ((SUCCESS_COUNT++))
    kill $SERVER_PID 2>/dev/null
else
    echo -e "${RED}❌ FAIL${NC}: Server fails to start"
fi

echo ""
echo "🛠️ 3. MCP TOOLS FUNCTIONALITY"
echo "-----------------------------"

# Start server for testing
python -m source.waygate_mcp --port 8002 --env development >/dev/null 2>&1 &
SERVER_PID=$!
sleep 3

# Test health endpoint
curl -s http://localhost:8002/health | grep -q "healthy"
check_status "Health endpoint returns 'healthy' status"

# Test MCP tools endpoint
TOOLS_COUNT=$(curl -s http://localhost:8002/mcp/tools | jq -r '.total_tools' 2>/dev/null || echo "0")
if [ "$TOOLS_COUNT" -eq 5 ]; then
    echo -e "${GREEN}✅ PASS${NC}: All 5 MCP tools available"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌ FAIL${NC}: Expected 5 tools, found $TOOLS_COUNT"
fi

# Cleanup
kill $SERVER_PID 2>/dev/null

echo ""
echo "📄 4. VERSION CONSISTENCY"
echo "------------------------"

# Check mcp.json version
MCP_VERSION=$(jq -r '.server.version' mcp.json 2>/dev/null || echo "missing")
if [ "$MCP_VERSION" = "2.1.0" ]; then
    echo -e "${GREEN}✅ PASS${NC}: mcp.json version is 2.1.0"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌ FAIL${NC}: mcp.json version is $MCP_VERSION, expected 2.1.0"
fi

# Check README.md contains version badge
grep -q "version-2.1.0-blue" README.md
check_status "README.md contains correct version badge"

# Check CHANGELOG.md has current date
TODAY=$(date +%Y-%m-%d)
grep -q "\[2.1.0\] - $TODAY" CHANGELOG.md
check_status "CHANGELOG.md has today's date for v2.1.0"

echo ""
echo "🔒 5. SECURITY VALIDATION"
echo "------------------------"

# Check for hardcoded secrets (should find none)
HARDCODED_SECRETS=$(grep -r "change-this-in-production" source/ || echo "")
if [ -z "$HARDCODED_SECRETS" ]; then
    echo -e "${GREEN}✅ PASS${NC}: No hardcoded secrets in source code"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌ FAIL${NC}: Found hardcoded secrets in source code"
fi

# Check that .env contains secure keys
if [ -f ".env" ] && grep -q "WAYGATE_SECRET_KEY=" .env; then
    KEY_LENGTH=$(grep "WAYGATE_SECRET_KEY=" .env | cut -d'=' -f2 | wc -c)
    if [ "$KEY_LENGTH" -gt 50 ]; then
        echo -e "${GREEN}✅ PASS${NC}: .env contains secure secret key"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}❌ FAIL${NC}: .env secret key too short"
    fi
else
    echo -e "${YELLOW}⚠️  INFO${NC}: .env file missing (will auto-generate)"
    ((SUCCESS_COUNT++))
fi

echo ""
echo "📚 6. DOCUMENTATION COMPLETENESS"
echo "--------------------------------"

# Check required documentation files exist
for doc in "README.md" "CHANGELOG.md" "CLAUDE_DESKTOP_SETUP.md" "mcp.json"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $doc exists"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}❌ FAIL${NC}: $doc missing"
    fi
done

echo ""
echo "🎯 7. TASKWARRIOR INTEGRATION"
echo "-----------------------------"

# Check dashboard script exists and is executable
if [ -x "scripts/dashboard.sh" ]; then
    echo -e "${GREEN}✅ PASS${NC}: Dashboard script exists and executable"
    ((SUCCESS_COUNT++))
else
    echo -e "${RED}❌ FAIL${NC}: Dashboard script missing or not executable"
fi

# Test dashboard script runs without errors
./scripts/dashboard.sh >/dev/null 2>&1
check_status "Dashboard script executes without errors"

echo ""
echo "==============================================="
echo "🏁 VERIFICATION SUMMARY"
echo "==============================================="

PASS_RATE=$((SUCCESS_COUNT * 100 / TOTAL_CHECKS))

if [ $PASS_RATE -eq 100 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED!${NC}"
    echo -e "${GREEN}✅ Ready for release: $SUCCESS_COUNT/$TOTAL_CHECKS checks passed${NC}"
    echo ""
    echo "📋 NEXT STEPS:"
    echo "1. Execute the commit sequence"
    echo "2. Create git tag: git tag -a v2.1.0 -m '...'"
    echo "3. Push to repository: git push origin main --tags"
    echo "4. Create GitHub release"
    exit 0
elif [ $PASS_RATE -ge 80 ]; then
    echo -e "${YELLOW}⚠️  MOSTLY READY${NC}"
    echo -e "${YELLOW}✅ $SUCCESS_COUNT/$TOTAL_CHECKS checks passed ($PASS_RATE%)${NC}"
    echo -e "${YELLOW}🔧 Fix remaining issues before release${NC}"
    exit 1
else
    echo -e "${RED}❌ NOT READY FOR RELEASE${NC}"
    echo -e "${RED}✅ Only $SUCCESS_COUNT/$TOTAL_CHECKS checks passed ($PASS_RATE%)${NC}"
    echo -e "${RED}🚨 Critical issues must be resolved${NC}"
    exit 1
fi