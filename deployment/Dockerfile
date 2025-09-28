# Dockerfile
# Security-hardened multi-stage build for Waygate MCP
FROM python:3.12-slim-bookworm AS builder

# Security: Pin specific versions for reproducibility
ARG PYTHON_VERSION=3.12.1
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=2.0.0

# Metadata labels
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.authors="Jeremy Longshore" \
      org.opencontainers.image.url="https://github.com/jeremylongshore/waygate-mcp" \
      org.opencontainers.image.documentation="https://github.com/jeremylongshore/waygate-mcp/wiki" \
      org.opencontainers.image.source="https://github.com/jeremylongshore/waygate-mcp" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="Waygate" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.title="Waygate MCP" \
      org.opencontainers.image.description="Secure MCP Server Framework - Successor to NEXUS MCP"

# Security: Update base image and install only necessary build tools
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        make \
        && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Security: Create build user to avoid root operations
RUN groupadd -r builder && useradd -r -g builder -m builder
USER builder
WORKDIR /build

# Copy and install dependencies as non-root
COPY --chown=builder:builder ./source/requirements-docker.txt ./
RUN pip install --user --no-cache-dir --upgrade pip wheel setuptools && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements-docker.txt

#
# Production stage - Minimal attack surface
#
FROM python:3.12-slim-bookworm

# Security: Install security updates immediately
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        libcap2-bin \
        dumb-init \
        && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Security: Create non-root user with specific UID/GID
RUN groupadd -r waygate -g 1000 && \
    useradd -r -u 1000 -g waygate \
        -d /home/waygate \
        -s /sbin/nologin \
        -c "Waygate service user" waygate && \
    mkdir -p /home/waygate && \
    chown -R waygate:waygate /home/waygate

# Security: Set up app directory with proper permissions
WORKDIR /app
RUN mkdir -p /app/logs /app/data /app/.waygate /app/tmp && \
    chown -R waygate:waygate /app && \
    chmod 750 /app && \
    chmod 770 /app/logs /app/data /app/.waygate /app/tmp

# Copy wheels from builder (as root for installation)
COPY --from=builder /build/wheels /tmp/wheels

# Security: Install packages and remove wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links=/tmp/wheels /tmp/wheels/* && \
    rm -rf /tmp/wheels /root/.cache/pip

# Copy application code with proper ownership
COPY --chown=waygate:waygate ./source/waygate_mcp.py /app/waygate_mcp.py
COPY --chown=waygate:waygate ./source /app/src
COPY --chown=waygate:waygate ./source/configs /app/configs
COPY --chown=waygate:waygate ./deployment/scripts/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod 550 /app/docker-entrypoint.sh

# Security: Drop all capabilities and add only what's needed
RUN setcap -r /usr/local/bin/python3.12 || true

# Security: Set security options
USER waygate

# Security: Don't run as PID 1, use init system
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Health check with timeout
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with reduced privileges
EXPOSE 8000
CMD ["/app/docker-entrypoint.sh"]