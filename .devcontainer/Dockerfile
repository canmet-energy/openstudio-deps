# Development-only Dockerfile for openstudio-deps
# Single-stage container focused on Python package development workflow

FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu-24.04

# Install certificate management (single script)
COPY .devcontainer/certs* /tmp/certs/
COPY .devcontainer/scripts/certctl-safe.sh /tmp/
RUN chmod +x /tmp/certctl-safe.sh && \
    /tmp/certctl-safe.sh install && \
    /tmp/certctl-safe.sh certs-refresh && \
    rm -rf /tmp/certctl-safe.sh /tmp/certs/

# Unified dev environment init (venv + prompt)
COPY .devcontainer/scripts/dev-env-init.sh /etc/profile.d/dev-env-init.sh
RUN chmod 644 /etc/profile.d/dev-env-init.sh

# Environment Configuration
ENV DEBIAN_FRONTEND=noninteractive
# Note: Certificate environment variables now managed dynamically by certctl-safe

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # APT and repository tools
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    # Basic utilities
    curl \
    git \
    unzip \
    jq \
    # Development tools
    build-essential \
    # Runtime libraries needed by OpenStudio
    libgfortran5 \
    libgomp1 \
    libssl3 \
    # X11 libraries for OpenStudio GUI (optional but avoids missing-lib errors)
    libx11-6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy installation scripts
COPY .devcontainer/scripts/ /tmp/install-scripts/
RUN chmod +x /tmp/install-scripts/*.sh

# Set up for development workflow
USER vscode
WORKDIR /workspaces/openstudio-deps
ENV DOCKER_BUILD_CONTEXT=true

# Ensure user-local bin (uv, etc.) is visible during install scripts
ENV PATH="/home/vscode/.local/bin:$PATH"

# Install UV Python package manager (uses CURL_FLAGS set by certctl_load)
RUN bash -c '. /usr/local/bin/certctl 2>/dev/null || true && \
    certctl_load 2>/dev/null || true && \
    /tmp/install-scripts/install-user-uv.sh'

# Container metadata
LABEL maintainer="CANMET Energy <canmet-energy@nrcan-rncan.gc.ca>" \
    description="openstudio-deps development environment" \
    version="dev" \
    org.opencontainers.image.source="https://github.com/canmet-energy/openstudio-deps"
