#!/bin/bash
# Post-create setup script for openstudio-deps devcontainer
# Runs after the container is created to set up the development environment

set -e

echo "🚀 Starting post-create setup..."

# Refresh certificate status and enable terminal banner (non-blocking)
if command -v certctl >/dev/null 2>&1; then
    echo "🔐 Checking certificate status..."
    certctl banner || true

    # Enable certificate status banner in new terminals
    echo "🔐 Enabling certificate status banner for new terminals..."
    sudo sed -i 's/^    # certctl_banner 2>\/dev\/null || true$/    certctl_banner 2>\/dev\/null || true/' /etc/profile.d/certctl-env.sh || true
fi

PROJECT_ROOT="$(pwd)"
PYTHON_VERSION="${DEVCONTAINER_PYTHON_VERSION:-3.12}"

echo "🐍 Setting up Python ${PYTHON_VERSION} environment with UV..."

# Ensure uv is on PATH
export PATH="$HOME/.local/bin:$PATH"

# Install the requested Python version via uv
uv python install "${PYTHON_VERSION}"

# Create virtual environment using uv
echo "🔧 Creating virtual environment at .venv..."
uv venv --python "${PYTHON_VERSION}" "${PROJECT_ROOT}/.venv"

# Install project in editable mode with dev dependencies
echo "📦 Installing openstudio-deps with dev dependencies..."
uv pip install --python "${PROJECT_ROOT}/.venv/bin/python" -e "${PROJECT_ROOT}[dev]"

echo ""
echo "✅ Post-create setup complete!"
echo "   Python:  $(${PROJECT_ROOT}/.venv/bin/python --version)"
echo "   Venv:    ${PROJECT_ROOT}/.venv"
echo "   Run 'osdep --help' to verify the CLI is installed."
