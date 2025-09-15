# Runbook: Waygate MCP Operations

**Version:** 1.0.0
**Last Updated:** 2025-01-14
**Service:** Waygate MCP Server
**Owner:** Jeremy Longshore

## 1. Service Overview

### 1.1 Service Description
Waygate MCP is an enterprise-grade Model Context Protocol server providing MCP operations with comprehensive diagnostics and plugin support.

### 1.2 Critical Information
- **Service Name:** waygate-mcp
- **Default Port:** 8000
- **Process Name:** waygate_mcp.py
- **Config Location:** `/home/jeremy/projects/waygate-mcp/.env`
- **Log Location:** `/home/jeremy/.waygate/logs/`
- **Data Location:** `/home/jeremy/.waygate/data/`

### 1.3 Dependencies
- Python 3.9+
- SQLite database
- Optional: Redis for caching
- Optional: PostgreSQL for production

## 2. Common Operations

### 2.1 Starting the Service

#### Development Mode
```bash
cd /home/jeremy/projects/waygate-mcp
source venv/bin/activate
python src/waygate_mcp.py --env development
```

#### Production Mode
```bash
cd /home/jeremy/projects/waygate-mcp
source venv/bin/activate
python src/waygate_mcp.py --env production --workers 4
```

#### Using systemd
```bash
sudo systemctl start waygate-mcp
sudo systemctl status waygate-mcp
```

### 2.2 Stopping the Service

#### Graceful Shutdown
```bash
# Find process
ps aux | grep waygate_mcp

# Send SIGTERM for graceful shutdown
kill -TERM <PID>
```

#### Using systemd
```bash
sudo systemctl stop waygate-mcp
```

#### Emergency Stop
```bash
# Force kill (use only if graceful shutdown fails)
kill -9 <PID>
```

### 2.3 Restarting the Service

```bash
# Using systemd
sudo systemctl restart waygate-mcp

# Manual restart
./scripts/waygate-ctl restart
```

### 2.4 Health Checks

#### Quick Health Check
```bash
curl http://localhost:8000/health
```

Expected Response:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "filesystem": "ok"
  }
}
```

#### Detailed Diagnostics
```bash
# Connection diagnostics
curl http://localhost:8000/diagnostics/connection

# Performance diagnostics
curl http://localhost:8000/diagnostics/performance
```

## 3. Troubleshooting

### 3.1 Service Won't Start

#### Check 1: Port Already in Use
```bash
# Check if port 8000 is in use
netstat -tuln | grep :8000
lsof -i :8000

# Solution: Kill the process using the port or use a different port
python src/waygate_mcp.py --port 8001
```

#### Check 2: Python Environment Issues
```bash
# Verify Python version
python3 --version  # Should be 3.9+

# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Check 3: Configuration Issues
```bash
# Check .env file exists
ls -la .env

# Verify configuration
cat .env | grep -E "WAYGATE_"

# Use default configuration
cp .env.example .env
```

#### Check 4: Permission Issues
```bash
# Check file permissions
ls -la src/waygate_mcp.py

# Fix permissions
chmod +x src/waygate_mcp.py
chmod -R 755 /home/jeremy/.waygate/
```

### 3.2 High CPU Usage

#### Diagnosis
```bash
# Check CPU usage
top -p $(pgrep -f waygate_mcp)

# Check number of requests
curl http://localhost:8000/metrics | grep requests_total
```

#### Solutions
1. Increase workers: `--workers 8`
2. Enable rate limiting in configuration
3. Check for infinite loops in plugins
4. Review logs for excessive errors

### 3.3 High Memory Usage

#### Diagnosis
```bash
# Check memory usage
ps aux | grep waygate_mcp | awk '{print $6/1024 " MB"}'

# Check for memory leaks
curl http://localhost:8000/diagnostics/performance
```

#### Solutions
1. Restart service to clear memory
2. Reduce cache size in configuration
3. Check for memory leaks in plugins
4. Enable memory profiling

### 3.4 Database Issues

#### Check Database
```bash
# Verify database file exists
ls -la waygate.db

# Check database integrity
sqlite3 waygate.db "PRAGMA integrity_check;"

# Backup database
cp waygate.db waygate.db.backup
```

#### Reset Database
```bash
# WARNING: This will delete all data
rm waygate.db
python src/waygate_mcp.py  # Will recreate database
```

### 3.5 Connection Timeouts

#### Diagnosis
```bash
# Test endpoint response time
time curl http://localhost:8000/health

# Check network connectivity
ping localhost
telnet localhost 8000
```

#### Solutions
1. Increase timeout settings
2. Check firewall rules
3. Verify network configuration
4. Review proxy settings

## 4. Monitoring

### 4.1 Key Metrics to Monitor

| Metric | Alert Threshold | Check Command |
|--------|----------------|---------------|
| CPU Usage | > 80% | `top -p $(pgrep -f waygate)` |
| Memory Usage | > 500MB | `ps aux | grep waygate` |
| Response Time | > 1s | `time curl /health` |
| Error Rate | > 1% | Check logs for ERROR |
| Disk Space | < 100MB | `df -h /home/jeremy` |

### 4.2 Log Monitoring

#### View Logs
```bash
# Tail logs
tail -f /home/jeremy/.waygate/logs/waygate.log

# Search for errors
grep ERROR /home/jeremy/.waygate/logs/waygate.log

# Count errors in last hour
grep ERROR waygate.log | grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" | wc -l
```

#### Log Rotation
```bash
# Rotate logs manually
mv waygate.log waygate.log.$(date +%Y%m%d)
touch waygate.log

# Set up logrotate (add to /etc/logrotate.d/waygate)
/home/jeremy/.waygate/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### 4.3 Prometheus Metrics

```bash
# Scrape metrics endpoint
curl http://localhost:8000/metrics

# Key metrics to watch:
# - waygate_requests_total
# - waygate_errors_total
# - waygate_response_time_seconds
```

## 5. Maintenance Tasks

### 5.1 Daily Tasks
- [ ] Check health endpoint
- [ ] Review error logs
- [ ] Monitor disk space
- [ ] Verify backup completion

### 5.2 Weekly Tasks
- [ ] Review performance metrics
- [ ] Clean old log files
- [ ] Update dependencies
- [ ] Test backup restoration

### 5.3 Monthly Tasks
- [ ] Security updates
- [ ] Performance tuning
- [ ] Capacity planning review
- [ ] Documentation updates

## 6. Backup and Recovery

### 6.1 Backup Procedures

#### Database Backup
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/home/jeremy/backups/waygate"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp waygate.db $BACKUP_DIR/waygate_${DATE}.db
tar -czf $BACKUP_DIR/waygate_config_${DATE}.tar.gz .env configs/

# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 6.2 Recovery Procedures

#### Restore from Backup
```bash
# Stop service
systemctl stop waygate-mcp

# Restore database
cp /home/jeremy/backups/waygate/waygate_20250114.db waygate.db

# Restore configuration
tar -xzf /home/jeremy/backups/waygate/waygate_config_20250114.tar.gz

# Start service
systemctl start waygate-mcp

# Verify
curl http://localhost:8000/health
```

## 7. Security Procedures

### 7.1 API Key Rotation
```bash
# Generate new API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
sed -i 's/WAYGATE_API_KEY=.*/WAYGATE_API_KEY=new_key_here/' .env

# Restart service
systemctl restart waygate-mcp
```

### 7.2 Security Checklist
- [ ] API keys rotated monthly
- [ ] Logs reviewed for suspicious activity
- [ ] Dependencies updated
- [ ] Firewall rules verified
- [ ] SSL certificates valid

## 8. Incident Response

### 8.1 Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|--------------|----------|
| P1 | Service Down | Immediate | Complete outage |
| P2 | Degraded Performance | 30 min | Slow responses |
| P3 | Minor Issue | 2 hours | Non-critical errors |
| P4 | Improvement | Next day | Feature requests |

### 8.2 Incident Response Steps

1. **Identify** - Determine scope and impact
2. **Contain** - Prevent further damage
3. **Diagnose** - Find root cause
4. **Resolve** - Apply fix
5. **Verify** - Confirm resolution
6. **Document** - Create post-mortem

### 8.3 Emergency Contacts

| Role | Contact | When to Contact |
|------|---------|----------------|
| Service Owner | Jeremy Longshore | All incidents |
| On-Call | Rotation schedule | P1/P2 incidents |
| Management | Escalation path | P1 after 1 hour |

## 9. Performance Tuning

### 9.1 Configuration Optimization

```bash
# Increase workers for high load
WAYGATE_WORKERS=8

# Enable connection pooling
WAYGATE_DB_POOL_SIZE=20

# Adjust timeout
WAYGATE_TIMEOUT=60

# Enable caching
WAYGATE_CACHE_TYPE=redis
WAYGATE_CACHE_TTL=600
```

### 9.2 Database Optimization

```sql
-- Add indexes for frequent queries
CREATE INDEX idx_command_history_created ON command_history(created_at);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

-- Vacuum database
VACUUM;
ANALYZE;
```

## 10. Appendices

### A. Useful Commands Reference

```bash
# Service management
systemctl {start|stop|restart|status} waygate-mcp

# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/metrics

# Diagnostics
curl http://localhost:8000/diagnostics/connection
curl http://localhost:8000/diagnostics/performance

# Plugin management
curl http://localhost:8000/plugins
curl -X POST http://localhost:8000/plugins/reload

# Testing
pytest tests/ -v
python src/waygate_mcp.py --env test
```

### B. Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| WAYGATE_MODE | local_vm | Operating mode |
| WAYGATE_ENV | development | Environment |
| WAYGATE_PORT | 8000 | Service port |
| WAYGATE_WORKERS | 4 | Worker processes |
| WAYGATE_LOG_LEVEL | INFO | Log verbosity |

### C. Error Codes

| Code | Description | Action |
|------|-------------|--------|
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Verify API key |
| 404 | Not Found | Check endpoint URL |
| 429 | Rate Limited | Reduce request rate |
| 500 | Internal Error | Check logs |
| 503 | Service Unavailable | Service starting/stopping |

---

**Document Status:** Complete
**Review Schedule:** Monthly
**Last Review:** 2025-01-14
**Next Review:** 2025-02-14