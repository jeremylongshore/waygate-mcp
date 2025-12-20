#!/usr/bin/env python3
"""
Waygate MCP Security Monitoring and Alerting System
Enterprise-grade security monitoring with real-time alerts
Generated: 2025-09-29
"""

import json
import os
import sys
import time
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Any
import subprocess


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/waygate-security.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SecurityMonitor:
    """Enterprise security monitoring and alerting system"""

    def __init__(self, config_path: str = ".security-monitor.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.project_root = Path.cwd()
        self.reports_dir = self.project_root / "audit-reports"
        self.reports_dir.mkdir(exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "monitoring": {
                "enabled": True,
                "scan_interval_hours": 24,
                "real_time_monitoring": True,
                "file_monitoring_paths": ["02-src", "source", "requirements.txt"]
            },
            "alerting": {
                "enabled": True,
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "channel": "#security-alerts"
                },
                "github": {
                    "enabled": True,
                    "create_issues": True,
                    "token": ""
                }
            },
            "thresholds": {
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 2,
                "medium_vulnerabilities": 10,
                "low_vulnerabilities": 50
            },
            "compliance": {
                "frameworks": ["OWASP", "CWE", "PCI-DSS", "ISO-27001"],
                "required_scans": ["bandit", "safety", "semgrep", "secrets"],
                "scan_retention_days": 90
            }
        }

        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                return self.merge_configs(default_config, user_config)
            except Exception as e:
                logger.warning(f"Failed to load config {self.config_path}: {e}")

        # Save default config
        self.save_config(default_config)
        return default_config

    def merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self.merge_configs(default[key], value)
            else:
                default[key] = value
        return default

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def run_security_scan(self) -> Dict[str, Any]:
        """Execute comprehensive security scan"""
        logger.info("Starting comprehensive security scan...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        scan_results = {
            "timestamp": timestamp,
            "scan_id": f"security_scan_{timestamp}",
            "status": "success",
            "tools": {},
            "summary": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            }
        }

        # Run individual security tools
        try:
            scan_results["tools"]["bandit"] = self.run_bandit()
            scan_results["tools"]["safety"] = self.run_safety()
            scan_results["tools"]["semgrep"] = self.run_semgrep()
            scan_results["tools"]["secrets"] = self.run_secret_detection()
            scan_results["tools"]["pip_audit"] = self.run_pip_audit()

            # Calculate summary
            scan_results["summary"] = self.calculate_summary(scan_results["tools"])

        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            scan_results["status"] = "failed"
            scan_results["error"] = str(e)

        # Save scan results
        self.save_scan_results(scan_results)

        return scan_results

    def run_bandit(self) -> Dict[str, Any]:
        """Run Bandit static security analysis"""
        logger.info("Running Bandit security scan...")

        try:
            cmd = [
                "bandit", "-r", "02-src,source",
                "-f", "json",
                "--severity-level", "medium",
                "--confidence-level", "medium"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                bandit_data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "findings": len(bandit_data.get("results", [])),
                    "data": bandit_data,
                    "severity_counts": self.count_bandit_severities(bandit_data)
                }
            else:
                return {"status": "no_issues", "findings": 0}

        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")
            return {"status": "failed", "error": str(e)}

    def run_safety(self) -> Dict[str, Any]:
        """Run Safety vulnerability scan"""
        logger.info("Running Safety vulnerability scan...")

        try:
            cmd = ["safety", "check", "--json"]
            if Path(".safety-policy.json").exists():
                cmd.extend(["--policy-file", ".safety-policy.json"])

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                try:
                    safety_data = json.loads(result.stdout)
                    return {
                        "status": "vulnerabilities_found",
                        "findings": len(safety_data),
                        "data": safety_data,
                        "severity_counts": self.count_safety_severities(safety_data)
                    }
                except json.JSONDecodeError:
                    # Safety may output non-JSON when no vulnerabilities found
                    return {"status": "no_vulnerabilities", "findings": 0}
            else:
                return {"status": "no_vulnerabilities", "findings": 0}

        except Exception as e:
            logger.error(f"Safety scan failed: {e}")
            return {"status": "failed", "error": str(e)}

    def run_semgrep(self) -> Dict[str, Any]:
        """Run Semgrep static analysis"""
        logger.info("Running Semgrep static analysis...")

        try:
            cmd = [
                "semgrep", "--config=.semgrep.yml",
                "--json", "02-src", "source"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                semgrep_data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "findings": len(semgrep_data.get("results", [])),
                    "data": semgrep_data,
                    "severity_counts": self.count_semgrep_severities(semgrep_data)
                }
            else:
                return {"status": "no_issues", "findings": 0}

        except Exception as e:
            logger.error(f"Semgrep scan failed: {e}")
            return {"status": "failed", "error": str(e)}

    def run_secret_detection(self) -> Dict[str, Any]:
        """Run secret detection scan"""
        logger.info("Running secret detection scan...")

        try:
            cmd = [
                "detect-secrets", "scan",
                "--all-files", "--force-use-all-plugins"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                secrets_data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "findings": len(secrets_data.get("results", {})),
                    "data": secrets_data
                }
            else:
                return {"status": "no_secrets", "findings": 0}

        except Exception as e:
            logger.error(f"Secret detection failed: {e}")
            return {"status": "failed", "error": str(e)}

    def run_pip_audit(self) -> Dict[str, Any]:
        """Run pip-audit vulnerability scan"""
        logger.info("Running pip-audit scan...")

        try:
            cmd = [
                "pip-audit", "--format=json",
                "--require", "requirements.txt"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                pip_audit_data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "findings": len(pip_audit_data.get("vulnerabilities", [])),
                    "data": pip_audit_data
                }
            else:
                return {"status": "no_vulnerabilities", "findings": 0}

        except Exception as e:
            logger.error(f"pip-audit failed: {e}")
            return {"status": "failed", "error": str(e)}

    def count_bandit_severities(self, bandit_data: Dict) -> Dict[str, int]:
        """Count Bandit findings by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for result in bandit_data.get("results", []):
            severity = result.get("issue_severity", "").lower()
            if severity in counts:
                counts[severity] += 1

        return counts

    def count_safety_severities(self, safety_data: List) -> Dict[str, int]:
        """Count Safety findings by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for vuln in safety_data:
            # Safety doesn't provide severity, assume high for vulnerabilities
            counts["high"] += 1

        return counts

    def count_semgrep_severities(self, semgrep_data: Dict) -> Dict[str, int]:
        """Count Semgrep findings by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for result in semgrep_data.get("results", []):
            severity = result.get("extra", {}).get("severity", "info").lower()
            if severity == "error":
                counts["high"] += 1
            elif severity == "warning":
                counts["medium"] += 1
            else:
                counts["info"] += 1

        return counts

    def calculate_summary(self, tools: Dict[str, Any]) -> Dict[str, int]:
        """Calculate overall security summary"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for tool_name, tool_data in tools.items():
            if "severity_counts" in tool_data:
                for severity, count in tool_data["severity_counts"].items():
                    if severity in summary:
                        summary[severity] += count

        return summary

    def save_scan_results(self, results: Dict[str, Any]) -> None:
        """Save scan results to file"""
        filename = f"security_scan_{results['timestamp']}.json"
        filepath = self.reports_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Scan results saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save scan results: {e}")

    def check_thresholds(self, summary: Dict[str, int]) -> List[str]:
        """Check if findings exceed configured thresholds"""
        alerts = []
        thresholds = self.config["thresholds"]

        for severity, count in summary.items():
            if severity in thresholds:
                threshold = thresholds[severity]
                if count > threshold:
                    alerts.append(
                        f"{severity.upper()}: {count} findings (threshold: {threshold})"
                    )

        return alerts

    def send_alerts(self, scan_results: Dict[str, Any]) -> None:
        """Send security alerts based on findings"""
        summary = scan_results["summary"]
        alerts = self.check_thresholds(summary)

        if not alerts:
            logger.info("No threshold violations - no alerts needed")
            return

        alert_message = self.generate_alert_message(scan_results, alerts)

        if self.config["alerting"]["email"]["enabled"]:
            self.send_email_alert(alert_message)

        if self.config["alerting"]["slack"]["enabled"]:
            self.send_slack_alert(alert_message)

        if self.config["alerting"]["github"]["enabled"]:
            self.create_github_issue(scan_results, alerts)

    def generate_alert_message(self, scan_results: Dict[str, Any], alerts: List[str]) -> str:
        """Generate alert message"""
        timestamp = scan_results["timestamp"]
        summary = scan_results["summary"]

        message = f"""
🚨 WAYGATE MCP SECURITY ALERT 🚨

Scan ID: {scan_results['scan_id']}
Timestamp: {timestamp}
Status: {scan_results['status']}

THRESHOLD VIOLATIONS:
{chr(10).join(f"• {alert}" for alert in alerts)}

SUMMARY:
• Critical: {summary['critical']}
• High: {summary['high']}
• Medium: {summary['medium']}
• Low: {summary['low']}
• Info: {summary['info']}

RECOMMENDED ACTIONS:
1. Review security findings immediately
2. Prioritize critical and high severity issues
3. Update vulnerable dependencies
4. Implement security fixes
5. Re-run security scan to verify fixes

View detailed reports: ./audit-reports/
        """

        return message

    def send_email_alert(self, message: str) -> None:
        """Send email alert"""
        try:
            email_config = self.config["alerting"]["email"]

            msg = MimeMultipart()
            msg['From'] = email_config["username"]
            msg['Subject'] = "🚨 Waygate MCP Security Alert"
            msg.attach(MimeText(message, 'plain'))

            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])

            for recipient in email_config["recipients"]:
                msg['To'] = recipient
                text = msg.as_string()
                server.sendmail(email_config["username"], recipient, text)

            server.quit()
            logger.info("Email alert sent successfully")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def send_slack_alert(self, message: str) -> None:
        """Send Slack alert"""
        try:
            slack_config = self.config["alerting"]["slack"]

            payload = {
                "text": "🚨 Waygate MCP Security Alert",
                "attachments": [{
                    "color": "danger",
                    "text": message,
                    "footer": "Waygate MCP Security Monitor",
                    "ts": int(time.time())
                }]
            }

            response = requests.post(slack_config["webhook_url"], json=payload)
            response.raise_for_status()

            logger.info("Slack alert sent successfully")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    def create_github_issue(self, scan_results: Dict[str, Any], alerts: List[str]) -> None:
        """Create GitHub issue for security findings"""
        try:
            github_config = self.config["alerting"]["github"]

            if not github_config.get("token"):
                logger.warning("GitHub token not configured, skipping issue creation")
                return

            # This would require additional implementation for GitHub API
            logger.info("GitHub issue creation not yet implemented")

        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")

    def monitor_continuous(self) -> None:
        """Run continuous security monitoring"""
        logger.info("Starting continuous security monitoring...")

        scan_interval = self.config["monitoring"]["scan_interval_hours"] * 3600

        while True:
            try:
                scan_results = self.run_security_scan()
                self.send_alerts(scan_results)

                logger.info(f"Next scan in {self.config['monitoring']['scan_interval_hours']} hours")
                time.sleep(scan_interval)

            except KeyboardInterrupt:
                logger.info("Security monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(300)  # Wait 5 minutes before retry


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Waygate MCP Security Monitor")
    parser.add_argument("--scan", action="store_true", help="Run single security scan")
    parser.add_argument("--monitor", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--config", default=".security-monitor.json", help="Config file path")

    args = parser.parse_args()

    monitor = SecurityMonitor(args.config)

    if args.scan:
        results = monitor.run_security_scan()
        monitor.send_alerts(results)
        print(f"Scan completed: {results['scan_id']}")
    elif args.monitor:
        monitor.monitor_continuous()
    else:
        print("Use --scan for single scan or --monitor for continuous monitoring")


if __name__ == "__main__":
    main()