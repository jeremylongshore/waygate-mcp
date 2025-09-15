# Standard Operating Procedures (SOP): Waygate MCP

**Version:** 1.0.0
**Effective Date:** 2025-01-14
**Department:** Engineering
**Owner:** Jeremy Longshore

## 1. SOP Overview

### 1.1 Purpose
This document defines standard operating procedures for the Waygate MCP service to ensure consistent, reliable, and secure operations.

### 1.2 Scope
These procedures apply to all team members involved in:
- Development
- Deployment
- Operations
- Maintenance
- Support

### 1.3 Responsibilities
- **Developers:** Follow development and testing procedures
- **Operations:** Execute deployment and maintenance procedures
- **Support:** Follow incident response procedures
- **Management:** Ensure compliance and updates

## 2. Development Procedures

### SOP-DEV-001: Code Development Workflow

**Purpose:** Standardize code development process

**Procedure:**
1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/description
   ```

2. **Develop Feature**
   - Write code following style guide
   - Add unit tests (minimum 80% coverage)
   - Update documentation

3. **Run Quality Checks**
   ```bash
   make lint
   make test
   make security-check
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/description
   # Create PR on GitHub
   ```

**Frequency:** Per feature
**Owner:** Development Team

---

### SOP-DEV-002: Code Review Process

**Purpose:** Ensure code quality and knowledge sharing

**Procedure:**
1. **Reviewer Assignment**
   - Auto-assign based on CODEOWNERS
   - Minimum 1 reviewer required

2. **Review Checklist**
   - [ ] Code follows style guide
   - [ ] Tests included and passing
   - [ ] Documentation updated
   - [ ] Security considerations addressed
   - [ ] Performance impact assessed

3. **Feedback Process**
   - Use GitHub review comments
   - Mark as "Request Changes" or "Approve"
   - Respond within 24 hours

4. **Merge Requirements**
   - All CI checks passing
   - At least 1 approval
   - No unresolved comments

**Frequency:** Every PR
**Owner:** Lead Developer

## 3. Deployment Procedures

### SOP-OPS-001: Production Deployment

**Purpose:** Safely deploy code to production

**Pre-Deployment Checklist:**
- [ ] All tests passing
- [ ] Security scan complete
- [ ] Change ticket created
- [ ] Rollback plan documented
- [ ] Team notified

**Procedure:**
1. **Prepare Release**
   ```bash
   git checkout main
   git pull origin main
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Deploy to Staging**
   ```bash
   ./scripts/deploy-staging.sh
   # Run smoke tests
   ./scripts/test-staging.sh
   ```

3. **Deploy to Production**
   ```bash
   # During maintenance window
   ./scripts/deploy-production.sh
   ```

4. **Verify Deployment**
   ```bash
   curl https://production/health
   # Check metrics dashboard
   # Run production tests
   ```

5. **Post-Deployment**
   - Update deployment log
   - Notify stakeholders
   - Monitor for 24 hours

**Rollback Procedure:**
```bash
./scripts/rollback-production.sh
# Verify rollback
curl https://production/health
```

**Frequency:** Weekly/As needed
**Owner:** Operations Team

---

### SOP-OPS-002: Emergency Hotfix

**Purpose:** Rapidly fix critical production issues

**Procedure:**
1. **Create Hotfix Branch**
   ```bash
   git checkout -b hotfix/issue-description main
   ```

2. **Apply Fix**
   - Minimal code change
   - Add regression test
   - Update CHANGELOG

3. **Fast-Track Review**
   - Notify senior developer
   - Expedited review (< 1 hour)

4. **Deploy Immediately**
   ```bash
   ./scripts/emergency-deploy.sh
   ```

5. **Follow-Up**
   - Create post-mortem
   - Backport to develop
   - Schedule root cause analysis

**Frequency:** As needed
**Owner:** On-Call Engineer

## 4. Maintenance Procedures

### SOP-MAINT-001: Daily Health Check

**Purpose:** Ensure system health and performance

**Procedure:**
1. **Check Service Status** (9:00 AM)
   ```bash
   curl http://localhost:8000/health
   systemctl status waygate-mcp
   ```

2. **Review Metrics**
   - Response times
   - Error rates
   - Resource usage

3. **Check Logs**
   ```bash
   grep ERROR /var/log/waygate/waygate.log
   ```

4. **Verify Backups**
   ```bash
   ls -la /backup/waygate/
   ```

5. **Document Status**
   - Update daily checklist
   - Report issues

**Frequency:** Daily
**Owner:** Operations Team

---

### SOP-MAINT-002: Weekly Maintenance

**Purpose:** Perform routine maintenance tasks

**Procedure:**
1. **Update Dependencies** (Tuesday 2:00 PM)
   ```bash
   pip list --outdated
   pip install --upgrade [package]
   ```

2. **Database Maintenance**
   ```bash
   sqlite3 waygate.db "VACUUM;"
   sqlite3 waygate.db "ANALYZE;"
   ```

3. **Log Rotation**
   ```bash
   logrotate -f /etc/logrotate.d/waygate
   ```

4. **Security Updates**
   ```bash
   ./scripts/security-scan.sh
   ```

5. **Performance Review**
   - Analyze weekly metrics
   - Identify trends
   - Plan optimizations

**Frequency:** Weekly
**Owner:** Operations Team

## 5. Monitoring Procedures

### SOP-MON-001: Alert Response

**Purpose:** Standardize alert response process

**Alert Levels:**
- **P1 Critical:** Service down
- **P2 High:** Performance degraded
- **P3 Medium:** Non-critical issue
- **P4 Low:** Informational

**Procedure:**
1. **Acknowledge Alert** (within SLA)
   - P1: 5 minutes
   - P2: 15 minutes
   - P3: 1 hour
   - P4: Next business day

2. **Initial Assessment**
   - Check dashboard
   - Review recent changes
   - Identify scope

3. **Take Action**
   - P1/P2: Immediate investigation
   - P3/P4: Schedule investigation

4. **Resolution**
   - Apply fix
   - Verify resolution
   - Clear alert

5. **Documentation**
   - Update incident log
   - Create ticket if needed
   - Plan prevention

**Frequency:** As triggered
**Owner:** On-Call Team

## 6. Security Procedures

### SOP-SEC-001: Security Incident Response

**Purpose:** Handle security incidents effectively

**Procedure:**
1. **Detection**
   - Alert received
   - Anomaly detected
   - Report received

2. **Containment**
   - Isolate affected systems
   - Prevent spread
   - Preserve evidence

3. **Investigation**
   - Analyze logs
   - Identify attack vector
   - Assess damage

4. **Eradication**
   - Remove threat
   - Patch vulnerabilities
   - Update security controls

5. **Recovery**
   - Restore services
   - Verify integrity
   - Monitor closely

6. **Post-Incident**
   - Create report
   - Update procedures
   - Share learnings

**Frequency:** As needed
**Owner:** Security Team

---

### SOP-SEC-002: API Key Management

**Purpose:** Secure API key lifecycle management

**Procedure:**
1. **Key Generation**
   ```python
   import secrets
   key = secrets.token_urlsafe(32)
   ```

2. **Key Distribution**
   - Use secure channel
   - Never email plain text
   - Document recipient

3. **Key Storage**
   - Hash before storing
   - Use environment variables
   - Never commit to git

4. **Key Rotation** (Monthly)
   ```bash
   ./scripts/rotate-api-keys.sh
   ```

5. **Key Revocation**
   - Immediate when compromised
   - On employee departure
   - On service decommission

**Frequency:** Monthly rotation
**Owner:** Security Team

## 7. Backup Procedures

### SOP-BACK-001: Daily Backup

**Purpose:** Ensure data recoverability

**Procedure:**
1. **Database Backup** (2:00 AM)
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d)
   sqlite3 waygate.db ".backup /backup/waygate_${DATE}.db"
   ```

2. **Configuration Backup**
   ```bash
   tar -czf /backup/config_${DATE}.tar.gz /etc/waygate/
   ```

3. **Verify Backup**
   ```bash
   sqlite3 /backup/waygate_${DATE}.db "PRAGMA integrity_check;"
   ```

4. **Offsite Copy**
   ```bash
   rsync -av /backup/ remote:/backup/
   ```

5. **Cleanup Old Backups**
   ```bash
   find /backup/ -name "*.db" -mtime +30 -delete
   ```

**Frequency:** Daily
**Owner:** Operations Team

## 8. Documentation Procedures

### SOP-DOC-001: Documentation Updates

**Purpose:** Keep documentation current

**Procedure:**
1. **Identify Change**
   - Code change
   - Process change
   - Configuration change

2. **Update Documentation**
   - README.md
   - API documentation
   - Internal wiki

3. **Review Process**
   - Technical review
   - Editorial review
   - Approval

4. **Publication**
   - Commit to repository
   - Update version
   - Notify team

**Frequency:** With each change
**Owner:** Development Team

## 9. Training Procedures

### SOP-TRAIN-001: New Team Member Onboarding

**Purpose:** Ensure proper onboarding

**Week 1 Checklist:**
- [ ] System access setup
- [ ] Development environment
- [ ] Documentation review
- [ ] Shadow team member

**Week 2 Checklist:**
- [ ] First code review
- [ ] First deployment observation
- [ ] Emergency procedures training
- [ ] First on-call shadow

**Week 3-4 Checklist:**
- [ ] First feature development
- [ ] First production deployment
- [ ] First on-call shift (supervised)

**Frequency:** Per new hire
**Owner:** Team Lead

## 10. Compliance Procedures

### SOP-COMP-001: Audit Preparation

**Purpose:** Ensure audit readiness

**Monthly Tasks:**
- [ ] Review access logs
- [ ] Update documentation
- [ ] Verify compliance controls
- [ ] Archive audit trails

**Quarterly Tasks:**
- [ ] Full system audit
- [ ] Update risk register
- [ ] Review policies
- [ ] Training verification

**Annual Tasks:**
- [ ] Policy review and update
- [ ] Disaster recovery test
- [ ] Security assessment
- [ ] Compliance certification

**Frequency:** As specified
**Owner:** Compliance Officer

## 11. Appendices

### A. Contact Information

| Role | Primary | Backup |
|------|---------|---------|
| Service Owner | Jeremy L. | TBD |
| Tech Lead | TBD | TBD |
| On-Call | Rotation | Rotation |
| Security | Security Team | TBD |

### B. Tool Reference

| Tool | Purpose | Location |
|------|---------|----------|
| GitHub | Code repository | github.com/... |
| Grafana | Metrics dashboard | grafana.local |
| PagerDuty | Alerting | pagerduty.com |
| Slack | Communication | workspace.slack.com |

### C. Automation Scripts

| Script | Purpose | Schedule |
|--------|---------|----------|
| backup.sh | Database backup | Daily 2 AM |
| health-check.sh | Service health | Every 5 min |
| rotate-logs.sh | Log rotation | Weekly |
| security-scan.sh | Security check | Daily |

---

**Document Status:** Approved
**Review Frequency:** Quarterly
**Last Review:** 2025-01-14
**Next Review:** 2025-04-14