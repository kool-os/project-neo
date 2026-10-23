#!/usr/bin/env bash
# ==============================================================================
# neo & neon Installer for Gentoo Linux
# Unified Package Manager & Qt6 GUI
# ==============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

echo -e "${CYAN}${BOLD}"
echo "=========================================================="
echo "           neo & neon Installation Script                 "
echo "        Unified Package Manager for Gentoo Linux          "
echo "=========================================================="
echo -e "${NC}"

# 1. Dependency Checks
echo -e "${BOLD}[1/6] Checking system dependencies...${NC}"

# Python check
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Error: python3 is not installed.${NC}"
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "  • Python version: ${GREEN}${PY_VER}${NC}"

# Rust / Cargo check
if ! command -v cargo &>/dev/null; then
    echo -e "${RED}Error: cargo (Rust) is not installed.${NC}"
    exit 1
fi
RUST_VER=$(cargo --version | head -n1)
echo -e "  • Cargo / Rust: ${GREEN}${RUST_VER}${NC}"

# pip check
if ! command -v pip &>/dev/null && ! python3 -m pip --version &>/dev/null; then
    echo -e "${YELLOW}  • pip not found in PATH, attempting emerge...${NC}"
    echo kdekde | sudo -S emerge --getbinpkg dev-python/pip
fi
PIP_VER=$(python3 -m pip --version | awk '{print $2}')
echo -e "  • pip: ${GREEN}${PIP_VER}${NC}"

# maturin check
if ! command -v maturin &>/dev/null; then
    echo -e "${YELLOW}  • maturin not found, attempting emerge...${NC}"
    echo kdekde | sudo -S emerge --getbinpkg dev-util/maturin || python3 -m pip install --break-system-packages maturin
fi
MATURIN_VER=$(maturin --version)
echo -e "  • Maturin: ${GREEN}${MATURIN_VER}${NC}"

# PyQt6 check
if ! python3 -c "import PyQt6" &>/dev/null; then
    echo -e "${YELLOW}  • PyQt6 not found, installing...${NC}"
    echo kdekde | sudo -S emerge --getbinpkg --binpkg-respect-use=n dev-python/pyqt6 || python3 -m pip install --break-system-packages PyQt6
fi
echo -e "  • PyQt6: ${GREEN}Installed${NC}"

# Required Python dependencies
python3 -m pip install --break-system-packages toml click rich pexpect 2>/dev/null || true

# 2. Build Rust Core (neo-core)
echo -e "\n${BOLD}[2/6] Building Rust acceleration core (neo-core)...${NC}"
cd "${SCRIPT_DIR}/neo-core"
maturin build --release --skip-auditwheel
WHEEL_PATH=$(ls -t "${SCRIPT_DIR}/neo-core/target/wheels/"neo_core-*.whl | head -n1)
echo -e "  • Built wheel: ${GREEN}${WHEEL_PATH}${NC}"

echo -e "  • Installing neo-core wheel..."
python3 -m pip uninstall -y --break-system-packages neo-core 2>/dev/null || true
python3 -m pip install --break-system-packages --force-reinstall "${WHEEL_PATH}"

# 3. Install Python CLI (neo-cli)
echo -e "\n${BOLD}[3/6] Installing neo CLI...${NC}"
cd "${SCRIPT_DIR}/neo-cli"
python3 -m pip install --break-system-packages -e .

# 4. Install Qt GUI (neon)
echo -e "\n${BOLD}[4/6] Installing neon GUI...${NC}"
cd "${SCRIPT_DIR}/neon"
python3 -m pip install --break-system-packages -e .

# 5. Verify and configure symlinks
echo -e "\n${BOLD}[5/6] Verifying user binaries and symlinks...${NC}"
mkdir -p "${HOME}/.local/bin"

if [ -f "${HOME}/.local/bin/neo" ]; then
    chmod +x "${HOME}/.local/bin/neo"
    echo -e "  • neo binary: ${GREEN}${HOME}/.local/bin/neo${NC}"
fi

if [ -f "${HOME}/.local/bin/neon" ]; then
    chmod +x "${HOME}/.local/bin/neon"
    echo -e "  • neon binary: ${GREEN}${HOME}/.local/bin/neon${NC}"
fi

# 6. Default configuration setup
echo -e "\n${BOLD}[6/6] Initializing default configuration...${NC}"
python3 -c "import neo.config; neo.config.load_config(); print('  • Configuration verified at:', neo.config.get_config_path())"

echo -e "\n${GREEN}${BOLD}=========================================================="
echo "          neo & neon Successfully Installed!              "
echo -e "==========================================================${NC}\n"

echo -e "Usage examples:"
echo -e "  ${CYAN}neo --version${NC}               # View backends and version"
echo -e "  ${CYAN}neo search firefox :flatp${NC}   # Search Flatpak packages"
echo -e "  ${CYAN}neo search vim :ebuild${NC}      # Search Portage packages"
echo -e "  ${CYAN}neo install <pkg> :<backend>${NC}# Install package via specific backend"
echo -e "  ${CYAN}neo update${NC}                  # Update packages"
echo -e "  ${CYAN}neo list${NC}                    # List installed packages"
echo -e "  ${CYAN}neon${NC}                        # Launch Qt GUI"
echo ""
