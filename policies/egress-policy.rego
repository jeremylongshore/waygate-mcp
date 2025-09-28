# egress-policy.rego
# Open Policy Agent (OPA) policy for Waygate MCP Proxy egress control
# Implements fine-grained access control for outbound network requests

package waygate.proxy.egress

import rego.v1

# Default policy: deny all egress unless explicitly allowed
default allow := false

# Allow egress based on comprehensive rule evaluation
allow if {
    # Basic validation checks
    input.request
    input.request.destination
    input.request.method

    # Check if request meets all criteria
    destination_allowed
    method_allowed
    rate_limit_ok
    security_checks_passed
    time_window_allowed
}

# Destination validation
destination_allowed if {
    # Load allowed domains from configuration
    allowed_domains := data.egress_rules.rules[_].domains[_]

    # Check if destination matches allowed patterns
    destination_matches(input.request.destination.host, allowed_domains)
}

# Method validation
method_allowed if {
    allowed_methods := ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    input.request.method in allowed_methods
}

# Rate limiting check
rate_limit_ok if {
    # Check if client has exceeded rate limits
    client_id := input.client.id
    current_rate := data.rate_limits[client_id].current_requests_per_minute
    max_rate := data.rate_limits[client_id].max_requests_per_minute

    current_rate < max_rate
}

# Security validation checks
security_checks_passed if {
    # Content inspection
    content_inspection_ok

    # DLP checks
    dlp_checks_ok

    # Certificate validation
    certificate_validation_ok

    # Malware scan
    malware_scan_ok
}

# Content inspection validation
content_inspection_ok if {
    # Check request body size
    content_size_ok

    # Check for suspicious patterns
    not contains_suspicious_patterns

    # Validate content type
    content_type_allowed
}

# Content size validation
content_size_ok if {
    max_size := 52428800  # 50MB
    count(input.request.body) <= max_size
}

# Suspicious pattern detection
contains_suspicious_patterns if {
    suspicious_patterns := [
        "(?i)(password|passwd|pwd)\\s*[:=]\\s*[\"']?[\\w!@#$%^&*()-_+={}\\[\\]|\\\\:;\"'<>,.?/~`]{8,}",
        "(?i)(api[_-]?key|apikey)\\s*[:=]\\s*[\"']?[\\w-]{20,}",
        "(?i)(secret|token)\\s*[:=]\\s*[\"']?[\\w-]{20,}",
        "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
        "\\b\\d{3}-\\d{2}-\\d{4}\\b"
    ]

    some pattern in suspicious_patterns
    regex.match(pattern, input.request.body)
}

# Content type validation
content_type_allowed if {
    allowed_types := [
        "application/json",
        "application/xml",
        "text/plain",
        "text/html",
        "application/x-www-form-urlencoded",
        "multipart/form-data"
    ]

    input.request.headers["content-type"] in allowed_types
}

# DLP (Data Loss Prevention) checks
dlp_checks_ok if {
    not contains_pii
    not contains_financial_data
    not contains_health_data
}

# PII detection
contains_pii if {
    pii_patterns := [
        "\\b\\d{3}-\\d{2}-\\d{4}\\b",  # SSN
        "\\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b",  # Credit card
        "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"  # Email
    ]

    some pattern in pii_patterns
    regex.match(pattern, sprintf("%v", [input.request]))
}

# Financial data detection
contains_financial_data if {
    financial_patterns := [
        "(?i)(account[\\s_-]?number|acct[\\s_-]?num)",
        "(?i)(routing[\\s_-]?number|aba[\\s_-]?number)",
        "(?i)(bank[\\s_-]?account)"
    ]

    some pattern in financial_patterns
    regex.match(pattern, sprintf("%v", [input.request]))
}

# Health data detection
contains_health_data if {
    health_patterns := [
        "(?i)(medical[\\s_-]?record|health[\\s_-]?record)",
        "(?i)(patient[\\s_-]?id|medical[\\s_-]?id)",
        "(?i)(diagnosis|prescription|medication)"
    ]

    some pattern in health_patterns
    regex.match(pattern, sprintf("%v", [input.request]))
}

# Certificate validation
certificate_validation_ok if {
    # Check if destination uses HTTPS
    input.request.destination.scheme == "https"

    # Validate certificate chain
    certificate_chain_valid

    # Check certificate expiration
    certificate_not_expired
}

# Certificate chain validation
certificate_chain_valid if {
    # This would integrate with actual certificate validation
    # For now, assume valid if HTTPS is used
    input.request.destination.scheme == "https"
}

# Certificate expiration check
certificate_not_expired if {
    # This would check actual certificate expiry
    # For now, assume valid if HTTPS is used
    input.request.destination.scheme == "https"
}

# Malware scanning
malware_scan_ok if {
    # File upload malware scan
    file_upload_clean

    # URL reputation check
    url_reputation_ok
}

# File upload scanning
file_upload_clean if {
    # Check if request contains file uploads
    not has_file_uploads
}

has_file_uploads if {
    input.request.headers["content-type"] == "multipart/form-data"
}

# URL reputation check
url_reputation_ok if {
    # Check against known malicious domains
    not destination_in_blacklist
}

destination_in_blacklist if {
    blacklisted_domains := data.security.blacklisted_domains[_]
    destination_matches(input.request.destination.host, blacklisted_domains)
}

# Time window validation
time_window_allowed if {
    # Check if request is within allowed time windows
    current_time := time.now_ns() / 1000000000  # Convert to seconds
    current_hour := (current_time % 86400) / 3600  # Hour of day (0-23)

    # Get time restrictions for this destination
    time_restrictions := get_time_restrictions

    # If no restrictions, allow
    count(time_restrictions) == 0
} else := time_window_allowed if {
    current_time := time.now_ns() / 1000000000
    current_hour := (current_time % 86400) / 3600

    time_restrictions := get_time_restrictions
    count(time_restrictions) > 0

    # Check if current hour is in allowed hours
    some allowed_hour in time_restrictions.allowed_hours
    current_hour == allowed_hour
}

# Get time restrictions for current destination
get_time_restrictions := restrictions if {
    some rule in data.egress_rules.rules
    destination_matches(input.request.destination.host, rule.domains[_])
    restrictions := rule.schedule
}

# Helper function to match destinations against patterns
destination_matches(host, pattern) if {
    # Exact match
    host == pattern
} else := destination_matches(host, pattern) if {
    # Wildcard match
    startswith(pattern, "*.")
    domain_suffix := substring(pattern, 2, -1)
    endswith(host, domain_suffix)
} else := destination_matches(host, pattern) if {
    # Regex match (if pattern starts with regex:)
    startswith(pattern, "regex:")
    regex_pattern := substring(pattern, 6, -1)
    regex.match(regex_pattern, host)
}

# MCP server validation
mcp_server_allowed if {
    # Check if request is from an authorized MCP server
    mcp_server_id := input.client.mcp_server_id
    mcp_server_id in data.mcp_servers.authorized_servers

    # Validate MCP server credentials
    mcp_credentials_valid
}

# MCP credentials validation
mcp_credentials_valid if {
    # This would validate MCP server authentication tokens
    # For now, assume valid if server is in authorized list
    input.client.mcp_server_id in data.mcp_servers.authorized_servers
}

# Audit logging requirements
audit_required if {
    # Always require audit for external requests
    true
}

# Create audit log entry
audit_log := log_entry if {
    log_entry := {
        "timestamp": time.now_ns(),
        "client_id": input.client.id,
        "mcp_server": input.client.mcp_server_id,
        "destination": input.request.destination,
        "method": input.request.method,
        "decision": "allow",
        "reason": "Policy evaluation passed",
        "security_checks": {
            "content_inspection": content_inspection_ok,
            "dlp_check": dlp_checks_ok,
            "certificate_validation": certificate_validation_ok,
            "malware_scan": malware_scan_ok
        }
    }
} else := log_entry if {
    log_entry := {
        "timestamp": time.now_ns(),
        "client_id": input.client.id,
        "mcp_server": input.client.mcp_server_id,
        "destination": input.request.destination,
        "method": input.request.method,
        "decision": "deny",
        "reason": "Policy evaluation failed",
        "violations": violation_reasons
    }
}

# Collect violation reasons
violation_reasons := reasons if {
    reasons := array.concat(
        destination_violations,
        array.concat(
            security_violations,
            array.concat(rate_limit_violations, time_window_violations)
        )
    )
}

destination_violations := ["destination_not_allowed"] if {
    not destination_allowed
} else := []

security_violations := violations if {
    violations := array.concat(
        content_violations,
        array.concat(dlp_violations, certificate_violations)
    )
}

content_violations := ["content_inspection_failed"] if {
    not content_inspection_ok
} else := []

dlp_violations := ["dlp_violation"] if {
    not dlp_checks_ok
} else := []

certificate_violations := ["certificate_validation_failed"] if {
    not certificate_validation_ok
} else := []

rate_limit_violations := ["rate_limit_exceeded"] if {
    not rate_limit_ok
} else := []

time_window_violations := ["time_window_violation"] if {
    not time_window_allowed
} else := []