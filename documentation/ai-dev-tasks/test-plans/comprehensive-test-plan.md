# Test Plan: Waygate MCP Framework

**Version:** 1.0.0
**Date:** 2025-01-14
**Author:** Jeremy Longshore
**Project:** Waygate MCP

## 1. Test Plan Overview

### 1.1 Objectives
- Verify all functional requirements from PRD
- Ensure system meets performance targets
- Validate security implementation
- Confirm plugin architecture works correctly
- Test diagnostic capabilities

### 1.2 Scope

#### In Scope
- Core MCP server functionality
- API endpoints
- Plugin system
- Diagnostic tools
- Security features
- Performance requirements

#### Out of Scope
- Third-party plugin testing
- Client application testing
- Infrastructure testing

### 1.3 Test Strategy
- **Unit Testing:** Individual component testing
- **Integration Testing:** Component interaction testing
- **System Testing:** End-to-end functionality
- **Performance Testing:** Load and stress testing
- **Security Testing:** Vulnerability assessment
- **Acceptance Testing:** User acceptance criteria

## 2. Test Environment

### 2.1 Hardware Requirements
- CPU: 4 cores minimum
- RAM: 8GB minimum
- Storage: 10GB available
- Network: 1Gbps connection

### 2.2 Software Requirements
- OS: Ubuntu 20.04+
- Python: 3.9+
- Database: SQLite (test), PostgreSQL (staging)
- Tools: pytest, locust, OWASP ZAP

### 2.3 Test Data
- Mock MCP commands
- Sample plugin configurations
- Test API keys
- Performance test datasets

## 3. Test Cases

### 3.1 Unit Tests

#### TEST-U001: Configuration Loading
**Component:** WaygateSettings
**Priority:** P0

**Test Steps:**
1. Create .env file with test values
2. Initialize WaygateSettings
3. Verify all settings loaded correctly

**Expected Result:** Settings match .env values

**Test Code:**
```python
def test_configuration_loading():
    settings = WaygateSettings()
    assert settings.port == 8000
    assert settings.mode == "local_vm"
    assert settings.env == "development"
```

---

#### TEST-U002: FastAPI Application Creation
**Component:** WaygateServer
**Priority:** P0

**Test Steps:**
1. Initialize WaygateServer
2. Check app instance created
3. Verify middleware configured

**Expected Result:** App instance with correct configuration

---

#### TEST-U003: MCP Command Validation
**Component:** MCPCommand
**Priority:** P0

**Test Steps:**
1. Create valid MCPCommand
2. Create invalid MCPCommand
3. Verify validation works

**Expected Result:** Valid commands accepted, invalid rejected

### 3.2 Integration Tests

#### TEST-I001: Health Check Integration
**Components:** Server + Health Endpoint
**Priority:** P0

**Test Steps:**
1. Start server
2. Call /health endpoint
3. Verify all checks return "ok"

**Expected Result:** Health status "healthy"

**Test Code:**
```python
def test_health_check_integration():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

#### TEST-I002: MCP Command Execution
**Components:** API + MCP Engine
**Priority:** P0

**Test Steps:**
1. Send POST to /mcp/execute
2. Verify command processed
3. Check response format

**Expected Result:** Command executed successfully

---

#### TEST-I003: Plugin Loading
**Components:** Plugin System + Registry
**Priority:** P1

**Test Steps:**
1. Place test plugin in plugins directory
2. Start server
3. Verify plugin loaded
4. Call plugin functionality

**Expected Result:** Plugin loads and executes

### 3.3 System Tests

#### TEST-S001: End-to-End Command Flow
**Priority:** P0

**Test Steps:**
1. Start server
2. Authenticate with API key
3. Execute MCP command
4. Verify result
5. Check metrics updated

**Expected Result:** Complete flow works

---

#### TEST-S002: Plugin Reload Functionality
**Priority:** P1

**Test Steps:**
1. Load initial plugins
2. Modify plugin
3. Call /plugins/reload
4. Verify new plugin loaded

**Expected Result:** Plugins reloaded successfully

### 3.4 Performance Tests

#### TEST-P001: Response Time
**Requirement:** < 100ms for 95th percentile
**Priority:** P0

**Test Steps:**
1. Send 1000 requests to /health
2. Measure response times
3. Calculate percentiles

**Test Script:**
```python
import locust

class PerformanceTest(locust.HttpUser):
    @locust.task
    def test_health(self):
        self.client.get("/health")
```

**Expected Result:**
- p50 < 50ms
- p95 < 100ms
- p99 < 200ms

---

#### TEST-P002: Throughput
**Requirement:** > 1000 req/s
**Priority:** P0

**Test Steps:**
1. Run load test with 100 concurrent users
2. Measure requests per second
3. Monitor error rate

**Expected Result:** > 1000 req/s with < 1% errors

---

#### TEST-P003: Memory Usage
**Requirement:** < 500MB baseline
**Priority:** P1

**Test Steps:**
1. Start server
2. Monitor memory usage for 1 hour
3. Execute various commands
4. Check for memory leaks

**Expected Result:** Memory stays under 500MB

### 3.5 Security Tests

#### TEST-SEC001: API Key Authentication
**Priority:** P0

**Test Steps:**
1. Send request without API key
2. Send request with invalid key
3. Send request with valid key

**Expected Result:**
- No key: 401 Unauthorized
- Invalid key: 401 Unauthorized
- Valid key: 200 OK

---

#### TEST-SEC002: Rate Limiting
**Priority:** P0

**Test Steps:**
1. Send 100 requests in 1 second
2. Send 101st request
3. Wait 1 minute
4. Send request again

**Expected Result:**
- 101st request: 429 Too Many Requests
- After wait: 200 OK

---

#### TEST-SEC003: Input Validation
**Priority:** P0

**Test Steps:**
1. Send malformed JSON
2. Send SQL injection attempt
3. Send XSS payload
4. Send oversized request

**Expected Result:** All attacks rejected

### 3.6 Diagnostic Tests

#### TEST-D001: Connection Diagnostics
**Priority:** P1

**Test Steps:**
1. Call /diagnostics/connection
2. Verify server status
3. Check connection count

**Expected Result:** Accurate diagnostic data

---

#### TEST-D002: Performance Diagnostics
**Priority:** P1

**Test Steps:**
1. Call /diagnostics/performance
2. Verify CPU usage
3. Check memory metrics

**Expected Result:** Realistic performance data

## 4. Test Execution Schedule

### Phase 1: Unit Testing (Week 1)
- [ ] Configuration tests
- [ ] Model validation tests
- [ ] Utility function tests

### Phase 2: Integration Testing (Week 1-2)
- [ ] API endpoint tests
- [ ] Database integration tests
- [ ] Plugin system tests

### Phase 3: System Testing (Week 2)
- [ ] End-to-end scenarios
- [ ] User workflows
- [ ] Error handling

### Phase 4: Performance Testing (Week 3)
- [ ] Load testing
- [ ] Stress testing
- [ ] Memory leak testing

### Phase 5: Security Testing (Week 3)
- [ ] Authentication tests
- [ ] Authorization tests
- [ ] Vulnerability scanning

### Phase 6: Acceptance Testing (Week 4)
- [ ] User acceptance criteria
- [ ] Documentation review
- [ ] Final validation

## 5. Test Automation

### 5.1 CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit -v --cov
      - name: Run integration tests
        run: pytest tests/integration -v
      - name: Run security tests
        run: pytest tests/security -v
```

### 5.2 Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test category
pytest tests/unit -v
pytest tests/integration -v
pytest tests/performance -v

# Run single test
pytest tests/test_api.py::test_health_check -v

# Run with markers
pytest -m "not slow"
pytest -m "security"
```

## 6. Test Metrics

### 6.1 Coverage Targets
- **Unit Test Coverage:** > 80%
- **Integration Coverage:** > 70%
- **API Coverage:** 100%
- **Critical Path Coverage:** 100%

### 6.2 Quality Metrics
- **Defect Density:** < 1 per KLOC
- **Test Pass Rate:** > 95%
- **Automation Rate:** > 80%
- **Test Execution Time:** < 10 minutes

## 7. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Flaky tests | High | Implement retry logic |
| Test environment issues | Medium | Docker containerization |
| Test data corruption | Low | Reset before each test |
| Performance test accuracy | Medium | Dedicated test environment |

## 8. Test Report Template

```markdown
# Test Report - [Date]

## Summary
- Total Tests: X
- Passed: X
- Failed: X
- Skipped: X
- Coverage: X%

## Failed Tests
| Test ID | Description | Error | Priority |
|---------|-------------|-------|----------|

## Performance Results
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|

## Security Findings
| Issue | Severity | Status |
|-------|----------|--------|

## Recommendations
- ...
```

## 9. Exit Criteria

### 9.1 Release Criteria
- [ ] All P0 tests passing
- [ ] 95% of P1 tests passing
- [ ] No critical security issues
- [ ] Performance targets met
- [ ] Code coverage > 80%

### 9.2 Rollback Criteria
- Critical bug in production
- Performance degradation > 20%
- Security vulnerability discovered
- Data corruption detected

## 10. Appendices

### A. Test Data Files
- `test_data/commands.json` - Sample MCP commands
- `test_data/plugins/` - Test plugins
- `test_data/api_keys.txt` - Test API keys

### B. Test Tools
- **pytest:** Unit and integration testing
- **locust:** Performance testing
- **OWASP ZAP:** Security testing
- **coverage.py:** Code coverage
- **hypothesis:** Property-based testing

### C. Test Categories

```python
# pytest markers
import pytest

# Mark slow tests
@pytest.mark.slow
def test_long_running():
    pass

# Mark security tests
@pytest.mark.security
def test_authentication():
    pass

# Mark performance tests
@pytest.mark.performance
def test_response_time():
    pass
```

---

**Document Status:** Complete
**Review Status:** Pending
**Test Coverage:** 0% (Not started)