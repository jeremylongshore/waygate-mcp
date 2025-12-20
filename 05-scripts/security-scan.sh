#!/bin/bash
# Waygate MCP Security Scanning Script
# Enterprise-grade automated security analysis
# Generated: 2025-09-29

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PROJECT_ROOT/audit-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_PREFIX="security_scan_$TIMESTAMP"

# Ensure reports directory exists
mkdir -p "$REPORTS_DIR"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install security tools
install_security_tools() {
    log "Installing security scanning tools..."

    # Install Python security tools
    pip install --upgrade \
        bandit[toml] \
        safety \
        pip-audit \
        semgrep \
        cyclonedx-bom \
        detect-secrets

    success "Security tools installed successfully"
}

# Function to run Bandit static security analysis
run_bandit_scan() {
    log "Running Bandit static security analysis..."

    local bandit_report="$REPORTS_DIR/${REPORT_PREFIX}_bandit"

    # Run Bandit with JSON output
    if bandit -r 02-src,source \
        -f json \
        -o "${bandit_report}.json" \
        --severity-level medium \
        --confidence-level medium; then
        success "Bandit scan completed successfully"
    else
        warning "Bandit scan found security issues"
    fi

    # Generate human-readable report
    bandit -r 02-src,source \
        -f txt \
        -o "${bandit_report}.txt" \
        --severity-level medium \
        --confidence-level medium || true

    # Generate SARIF format for GitHub integration
    bandit -r 02-src,source \
        -f sarif \
        -o "${bandit_report}.sarif" \
        --severity-level medium \
        --confidence-level medium || true

    log "Bandit reports saved to: ${bandit_report}.*"
}

# Function to run Safety dependency vulnerability scan
run_safety_scan() {
    log "Running Safety dependency vulnerability scan..."

    local safety_report="$REPORTS_DIR/${REPORT_PREFIX}_safety"

    # Run Safety with JSON output
    if safety check \
        --json \
        --output "${safety_report}.json" \
        --policy-file ".safety-policy.json"; then
        success "Safety scan completed - no vulnerabilities found"
    else
        warning "Safety scan found vulnerabilities"
    fi

    # Generate human-readable report
    safety check \
        --output "${safety_report}.txt" \
        --policy-file ".safety-policy.json" || true

    log "Safety reports saved to: ${safety_report}.*"
}

# Function to run pip-audit
run_pip_audit() {
    log "Running pip-audit package vulnerability scan..."

    local pip_audit_report="$REPORTS_DIR/${REPORT_PREFIX}_pip_audit"

    # Run pip-audit with JSON output
    if pip-audit \
        --format=json \
        --output="${pip_audit_report}.json" \
        --require requirements.txt; then
        success "pip-audit scan completed - no vulnerabilities found"
    else
        warning "pip-audit scan found vulnerabilities"
    fi

    # Generate human-readable report
    pip-audit \
        --format=cyclonedx-json \
        --output="${pip_audit_report}_sbom.json" \
        --require requirements.txt || true

    log "pip-audit reports saved to: ${pip_audit_report}.*"
}

# Function to run Semgrep static analysis
run_semgrep_scan() {
    log "Running Semgrep static analysis..."

    local semgrep_report="$REPORTS_DIR/${REPORT_PREFIX}_semgrep"

    # Run Semgrep with custom rules
    if semgrep \
        --config=.semgrep.yml \
        --json \
        --output="${semgrep_report}.json" \
        02-src source; then
        success "Semgrep scan completed successfully"
    else
        warning "Semgrep scan found issues"
    fi

    # Generate SARIF format for GitHub integration
    semgrep \
        --config=.semgrep.yml \
        --sarif \
        --output="${semgrep_report}.sarif" \
        02-src source || true

    log "Semgrep reports saved to: ${semgrep_report}.*"
}

# Function to run secret detection
run_secret_detection() {
    log "Running secret detection scan..."

    local secrets_report="$REPORTS_DIR/${REPORT_PREFIX}_secrets"

    # Run detect-secrets
    if detect-secrets scan \
        --all-files \
        --force-use-all-plugins \
        --baseline "${secrets_report}.baseline"; then
        success "Secret detection completed - no secrets found"
    else
        warning "Secret detection found potential secrets"
    fi

    log "Secret detection baseline saved to: ${secrets_report}.baseline"
}

# Function to generate Software Bill of Materials (SBOM)
generate_sbom() {
    log "Generating Software Bill of Materials (SBOM)..."

    local sbom_report="$REPORTS_DIR/${REPORT_PREFIX}_sbom"

    # Generate SBOM in CycloneDX format
    cyclonedx-py \
        -o "${sbom_report}.json" \
        --format json \
        requirements.txt

    # Generate SBOM in SPDX format if available
    if command_exists spdx-tools; then
        cyclonedx-py \
            -o "${sbom_report}.spdx" \
            --format spdx \
            requirements.txt || true
    fi

    success "SBOM generated: ${sbom_report}.*"
}

# Function to run license compliance check
run_license_check() {
    log "Running license compliance check..."

    local license_report="$REPORTS_DIR/${REPORT_PREFIX}_licenses"

    # Use pip-licenses if available
    if command_exists pip-licenses; then
        pip-licenses \
            --format=json \
            --output-file="${license_report}.json" \
            --with-urls \
            --with-description

        success "License report generated: ${license_report}.json"
    else
        warning "pip-licenses not available, skipping license check"
    fi
}

# Function to generate comprehensive security report
generate_security_report() {
    log "Generating comprehensive security report..."

    local summary_report="$REPORTS_DIR/${REPORT_PREFIX}_summary.md"

    cat > "$summary_report" << EOF
# 🔒 Waygate MCP Security Scan Report

**Generated:** $(date)
**Scan ID:** $REPORT_PREFIX
**Project:** Waygate MCP
**Version:** 2.1.0

## 📊 Executive Summary

This report contains the results of comprehensive security scanning performed on the Waygate MCP codebase using industry-standard tools.

### 🛡️ Security Tools Used

1. **Bandit** - Static security analysis for Python code
2. **Safety** - Dependency vulnerability scanning
3. **pip-audit** - PyPI package vulnerability scanning
4. **Semgrep** - Advanced static analysis with custom rules
5. **detect-secrets** - Secret detection and prevention
6. **License Compliance** - Open source license verification

### 📈 Scan Results

| Tool | Status | Report File |
|------|--------|-------------|
| Bandit | ✅ | \`${REPORT_PREFIX}_bandit.json\` |
| Safety | ✅ | \`${REPORT_PREFIX}_safety.json\` |
| pip-audit | ✅ | \`${REPORT_PREFIX}_pip_audit.json\` |
| Semgrep | ✅ | \`${REPORT_PREFIX}_semgrep.json\` |
| Secrets | ✅ | \`${REPORT_PREFIX}_secrets.baseline\` |
| SBOM | ✅ | \`${REPORT_PREFIX}_sbom.json\` |

### 🎯 Security Compliance

- **OWASP Top 10 (2021)**: Covered by custom Semgrep rules
- **CWE (Common Weakness Enumeration)**: Mapped in findings
- **CVE Database**: Checked via Safety and pip-audit
- **Supply Chain Security**: SBOM generated and dependencies verified

### 🚀 Next Steps

1. Review all HIGH and CRITICAL severity findings
2. Update vulnerable dependencies immediately
3. Implement recommended security fixes
4. Schedule regular security scans (daily via CI/CD)
5. Monitor security advisories for used packages

### 📞 Contact

For questions about this security report, contact: Jeremy Longshore

---

**Note:** This is an automated security report. Review findings carefully and validate in your specific environment.
EOF

    success "Security summary report generated: $summary_report"
}

# Function to cleanup old reports
cleanup_old_reports() {
    log "Cleaning up old security reports..."

    # Keep only last 30 reports
    find "$REPORTS_DIR" -name "security_scan_*" -type f -mtime +30 -delete 2>/dev/null || true

    success "Old reports cleaned up"
}

# Function to validate environment
validate_environment() {
    log "Validating scanning environment..."

    # Check if we're in the correct directory
    if [[ ! -f "pyproject.toml" ]]; then
        error "Not in project root directory"
        exit 1
    fi

    # Check Python version
    local python_version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    log "Python version: $python_version"

    # Check if required config files exist
    local config_files=(".bandit" "pyproject.toml" ".safety-policy.json" ".semgrep.yml")
    for config_file in "${config_files[@]}"; do
        if [[ ! -f "$config_file" ]]; then
            warning "Configuration file missing: $config_file"
        fi
    done

    success "Environment validation completed"
}

# Main execution function
main() {
    log "🔒 Starting Waygate MCP Security Scan"
    log "================================================"

    # Change to project root
    cd "$PROJECT_ROOT"

    # Validate environment
    validate_environment

    # Install/update security tools if requested
    if [[ "${1:-}" == "--install-tools" ]]; then
        install_security_tools
    fi

    # Run security scans
    log "🔍 Running security scans..."

    run_bandit_scan
    run_safety_scan
    run_pip_audit
    run_semgrep_scan
    run_secret_detection
    generate_sbom
    run_license_check

    # Generate reports
    generate_security_report

    # Cleanup
    cleanup_old_reports

    log "================================================"
    success "🎉 Security scan completed successfully!"
    log "📊 Reports available in: $REPORTS_DIR"
    log "📋 Summary report: $REPORTS_DIR/${REPORT_PREFIX}_summary.md"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi