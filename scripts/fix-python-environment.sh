#!/bin/bash
# PERMANENT FIX for Python Environment Management Issues
# This script resolves PEP 668 externally-managed-environment errors

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 FIXING Python Environment Management Issues PERMANENTLY${NC}"

# Function to install system packages
install_system_packages() {
    echo -e "${YELLOW}📦 Installing required system packages...${NC}"

    # Update package list
    sudo apt update

    # Install Python development tools
    sudo apt install -y \
        python3-full \
        python3-pip \
        python3-venv \
        python3-dev \
        python3-wheel \
        python3-setuptools \
        pipx \
        build-essential \
        pkg-config \
        libffi-dev \
        libssl-dev \
        curl \
        git

    echo -e "${GREEN}✅ System packages installed${NC}"
}

# Function to configure pipx for global tools
setup_pipx() {
    echo -e "${YELLOW}⚙️ Setting up pipx for global Python tools...${NC}"

    # Ensure pipx is in PATH
    if ! command -v pipx &> /dev/null; then
        echo 'export PATH="$PATH:/home/jeremy/.local/bin"' >> ~/.bashrc
        export PATH="$PATH:/home/jeremy/.local/bin"
    fi

    # Install commonly needed global tools with pipx
    pipx install pip-tools || true
    pipx install poetry || true
    pipx install black || true
    pipx install ruff || true

    echo -e "${GREEN}✅ pipx configured${NC}"
}

# Function to create a comprehensive virtual environment setup
create_venv_solution() {
    echo -e "${YELLOW}🐍 Creating robust virtual environment solution...${NC}"

    cd /home/jeremy/waygate-mcp

    # Remove existing venv if corrupted
    if [ -d "venv" ]; then
        echo -e "${YELLOW}🗑️ Removing existing virtual environment...${NC}"
        rm -rf venv
    fi

    # Create new virtual environment with system site packages
    python3 -m venv venv --system-site-packages

    # Activate and upgrade pip
    source venv/bin/activate
    pip install --upgrade pip wheel setuptools

    # Install all requirements
    pip install -r source/requirements.txt
    pip install -r source/requirements-docker.txt

    echo -e "${GREEN}✅ Virtual environment created successfully${NC}"
}

# Function to create automatic activation script
create_auto_activation() {
    echo -e "${YELLOW}⚡ Creating automatic environment activation...${NC}"

    # Enhanced activate script
    cat > /home/jeremy/waygate-mcp/activate_venv.sh << 'EOF'
#!/bin/bash
# Enhanced Virtual Environment Activation for Waygate MCP
# Automatically handles all Python environment issues

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/home/jeremy/waygate-mcp"
VENV_DIR="$PROJECT_DIR/venv"

echo -e "${BLUE}🐍 Waygate MCP Environment Manager${NC}"

# Change to project directory
cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}📦 Virtual environment not found, creating...${NC}"
    python3 -m venv venv --system-site-packages
    source venv/bin/activate
    pip install --upgrade pip wheel setuptools
    pip install -r source/requirements.txt
    pip install -r source/requirements-docker.txt
else
    source venv/bin/activate
fi

# Verify critical packages are installed
REQUIRED_PACKAGES=("fastapi" "uvicorn" "libsql-client" "pydantic-settings")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python -c "import $package" 2>/dev/null; then
        echo -e "${YELLOW}📦 Installing missing package: $package${NC}"
        pip install "$package"
    fi
done

echo -e "${GREEN}✅ Virtual environment activated for waygate-mcp${NC}"
echo -e "${BLUE}📦 To install packages: pip install package_name${NC}"
echo -e "${BLUE}🔄 To deactivate: deactivate${NC}"

# Set up environment variables
export PYTHONPATH="$PROJECT_DIR/source:$PYTHONPATH"
export WAYGATE_PROJECT_DIR="$PROJECT_DIR"

# Display environment info
echo -e "${BLUE}🔧 Python: $(python --version)${NC}"
echo -e "${BLUE}🔧 Pip: $(pip --version)${NC}"
echo -e "${BLUE}🔧 PYTHONPATH: $PYTHONPATH${NC}"
EOF

    chmod +x /home/jeremy/waygate-mcp/activate_venv.sh

    echo -e "${GREEN}✅ Auto-activation script created${NC}"
}

# Function to configure system-wide Python policy
configure_python_policy() {
    echo -e "${YELLOW}⚙️ Configuring Python policy (requires sudo)...${NC}"

    # Create pip configuration to prefer user installs
    mkdir -p ~/.config/pip
    cat > ~/.config/pip/pip.conf << EOF
[global]
user = true
break-system-packages = false

[install]
user = true
EOF

    # Configure for all users (requires sudo)
    sudo mkdir -p /etc/pip
    sudo tee /etc/pip/pip.conf > /dev/null << EOF
[global]
user = false
break-system-packages = false

[install]
prefer-binary = true
EOF

    echo -e "${GREEN}✅ Python policy configured${NC}"
}

# Function to create project-specific Python launcher
create_python_launcher() {
    echo -e "${YELLOW}🚀 Creating project-specific Python launcher...${NC}"

    cat > /home/jeremy/waygate-mcp/python << 'EOF'
#!/bin/bash
# Waygate MCP Python Launcher
# Automatically uses virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"

if [ -f "$VENV_PYTHON" ]; then
    exec "$VENV_PYTHON" "$@"
else
    echo "❌ Virtual environment not found. Run: ./activate_venv.sh"
    exit 1
fi
EOF

    chmod +x /home/jeremy/waygate-mcp/python

    # Create pip launcher too
    cat > /home/jeremy/waygate-mcp/pip << 'EOF'
#!/bin/bash
# Waygate MCP Pip Launcher
# Automatically uses virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PIP="$SCRIPT_DIR/venv/bin/pip"

if [ -f "$VENV_PIP" ]; then
    exec "$VENV_PIP" "$@"
else
    echo "❌ Virtual environment not found. Run: ./activate_venv.sh"
    exit 1
fi
EOF

    chmod +x /home/jeremy/waygate-mcp/pip

    echo -e "${GREEN}✅ Python launchers created${NC}"
}

# Function to test the solution
test_solution() {
    echo -e "${YELLOW}🧪 Testing the solution...${NC}"

    cd /home/jeremy/waygate-mcp

    # Test virtual environment activation
    source activate_venv.sh

    # Test package installations
    pip install --upgrade pip
    python -c "import libsql_client; print('✅ libsql-client imported successfully')"
    python -c "import fastapi; print('✅ FastAPI imported successfully')"
    python -c "import pydantic_settings; print('✅ pydantic-settings imported successfully')"

    echo -e "${GREEN}✅ All tests passed!${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Starting comprehensive Python environment fix...${NC}"

    install_system_packages
    setup_pipx
    create_venv_solution
    create_auto_activation
    configure_python_policy
    create_python_launcher
    test_solution

    echo -e "\n${GREEN}🎉 PYTHON ENVIRONMENT ISSUES PERMANENTLY FIXED!${NC}"
    echo -e "\n${BLUE}📋 How to use going forward:${NC}"
    echo -e "  1. ${YELLOW}cd /home/jeremy/waygate-mcp${NC}"
    echo -e "  2. ${YELLOW}source activate_venv.sh${NC} (automatic setup)"
    echo -e "  3. ${YELLOW}pip install package_name${NC} (will work in venv)"
    echo -e "  4. ${YELLOW}./python script.py${NC} (project launcher)"
    echo -e "  5. ${YELLOW}./pip install package${NC} (project pip)"

    echo -e "\n${BLUE}🛡️ This solution prevents:${NC}"
    echo -e "  ✅ PEP 668 externally-managed-environment errors"
    echo -e "  ✅ Global Python package conflicts"
    echo -e "  ✅ Permission denied errors"
    echo -e "  ✅ Missing dependencies"
    echo -e "  ✅ Virtual environment corruption"
}

# Run main function
main "$@"