#!/bin/bash

# ==============================================
# InstaLens - Instagram Followers Scraper
# One-line installer for Linux/Mac
# ==============================================

set -e  # Exit on error

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Emojis
CHECK="✅"
CROSS="❌"
ROCKET="🚀"
PACKAGE="📦"
WRENCH="🔧"
WARNING="⚠️"
INFO="ℹ️"

# Configuration
REPO_URL="https://github.com/efdutra/InstaLens.git"
PYTHON_MIN_VERSION="3.9"
NODE_MIN_VERSION="18"

# ==============================================
# Helper Functions
# ==============================================

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════╗"
    echo "║                                        ║"
    echo "║   📸 InstaLens Installer V1            ║"
    echo "║   Instagram Followers Scraper          ║"
    echo "║                                        ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_header_running() {
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════╗"
    echo "║                                        ║"
    echo "║   📸 InstaLens Installer V1            ║"
    echo "║   Instagram Followers Scraper          ║"
    echo "║                                        ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    print_success "${ROCKET} InstaLens running!"
    echo ""
}

print_step() {
    echo -e "\n${BLUE}${BOLD}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

print_info() {
    echo -e "${CYAN}${INFO} $1${NC}"
}

ask_yes_no() {
    while true; do
        echo -e -n "${YELLOW}$1 (y/n): ${NC}"
        read -r response < /dev/tty
        case "$response" in
            [yY]|[yY][eE][sS]) return 0 ;;
            [nN]|[nN][oO]) return 1 ;;
            *) echo -e "${RED}Please answer 'y' or 'n'${NC}" ;;
        esac
    done
}

version_compare() {
    # Returns 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# ==============================================
# Dependency Checks
# ==============================================

check_python() {
    print_step "Checking Python..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        if version_compare "$PYTHON_VERSION" "$PYTHON_MIN_VERSION"; then
            print_success "Python $PYTHON_VERSION found"
            return 0
        else
            print_warning "Python $PYTHON_VERSION found, but $PYTHON_MIN_VERSION+ required"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

check_node() {
    print_step "Checking Node.js..."
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        if version_compare "$NODE_VERSION" "$NODE_MIN_VERSION"; then
            print_success "Node.js $NODE_VERSION found"
            return 0
        else
            print_warning "Node.js $NODE_VERSION found, but $NODE_MIN_VERSION+ required"
            return 1
        fi
    else
        print_error "Node.js not found"
        return 1
    fi
}

check_pnpm() {
    if ! command -v pnpm &> /dev/null; then
        print_warning "pnpm not found - installing globally..."
        npm install -g pnpm
        print_success "pnpm installed"
    else
        print_success "pnpm found"
    fi
}

ask_install_location() {
    local current_dir=$(pwd)
    local default_location="$current_dir/InstaLens"
    
    echo ""
    print_step "Choose installation directory"
    echo ""
    print_info "Current directory: ${BOLD}$current_dir${NC}"
    echo ""
    
    if ask_yes_no "Install InstaLens in current directory ($default_location)?"; then
        INSTALL_DIR="$default_location"
    else
        echo ""
        echo -e -n "${CYAN}Enter installation path (or press Enter for $HOME/InstaLens): ${NC}"
        read -r custom_path < /dev/tty
        
        if [ -z "$custom_path" ]; then
            INSTALL_DIR="$HOME/InstaLens"
        else
            # Expand ~ to home directory
            INSTALL_DIR="${custom_path/#\~/$HOME}"
        fi
    fi
    
    print_info "Will install to: ${BOLD}$INSTALL_DIR${NC}"
}

install_dependencies() {
    print_step "Installing dependencies..."
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="mac"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    else
        print_error "Unsupported OS: $OSTYPE"
        exit 1
    fi
    
    # Check Python
    if ! check_python; then
        echo ""
        print_info "Python 3.9+ is required to run InstaLens backend."
        
        if [[ "$OS" == "mac" ]]; then
            if ask_yes_no "Install Python 3 via Homebrew?"; then
                if ! command -v brew &> /dev/null; then
                    print_error "Homebrew not found. Please install from https://brew.sh"
                    exit 1
                fi
                brew install python@3
            else
                print_error "Python is required. Install manually: https://python.org"
                exit 1
            fi
        elif [[ "$OS" == "linux" ]]; then
            if ask_yes_no "Install Python 3 via apt?"; then
                sudo apt update
                sudo apt install -y python3 python3-pip python3-venv
            else
                print_error "Python is required. Install manually: sudo apt install python3"
                exit 1
            fi
        fi
    fi
    
    # Check Node.js
    if ! check_node; then
        echo ""
        print_info "Node.js 18+ is required to run InstaLens frontend."
        
        if [[ "$OS" == "mac" ]]; then
            if ask_yes_no "Install Node.js via Homebrew?"; then
                brew install node
            else
                print_error "Node.js is required. Install manually: https://nodejs.org"
                exit 1
            fi
        elif [[ "$OS" == "linux" ]]; then
            if ask_yes_no "Install Node.js 20 via NodeSource?"; then
                curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
                sudo apt install -y nodejs
            else
                print_error "Node.js is required. Install manually: https://nodejs.org"
                exit 1
            fi
        fi
    fi
    
    check_pnpm
}

# ==============================================
# Main Installation
# ==============================================

main() {
    print_header
    
    # Ask where to install
    ask_install_location
    
    # Check if already installed
    if [ -d "$INSTALL_DIR" ]; then
        print_info "InstaLens already installed at: $INSTALL_DIR"
        if ask_yes_no "Do you want to update and run?"; then
            cd "$INSTALL_DIR"
            print_step "Updating repository..."
            git pull
            print_success "Repository updated"
        else
            cd "$INSTALL_DIR"
        fi
    else
        # Install dependencies
        install_dependencies
        
        # Clone repository
        print_step "Cloning InstaLens repository..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
        print_success "Repository cloned to: $INSTALL_DIR"
        
        # Setup backend
        print_step "Setting up backend..."
        cd backend
        
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            print_success "Virtual environment created"
        fi
        
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        python -m playwright install chromium
        
        # Create .env file
        if [ ! -f ".env" ]; then
            cat > .env << EOF
# Browser settings
SESSION_FILE=session.json
HEADLESS=false
BROWSER_TYPE=chromium

# CORS Configuration (allow all for development)
CORS_ORIGINS=*
EOF
            print_success "Backend .env created"
        fi
        
        cd ..
        print_success "Backend setup complete"
        
        # Setup frontend
        print_step "Setting up frontend..."
        cd frontend
        
        if [ ! -d "node_modules" ]; then
            pnpm install
            print_success "Frontend dependencies installed"
        fi
        
        cd ..
        print_success "Frontend setup complete"
    fi
    
    # Run application
    echo ""
    print_header
    print_success "${ROCKET} Installation complete!"
    echo ""
    print_info "Starting InstaLens..."
    echo ""
    
    # Start backend in background (silently)
    cd "$INSTALL_DIR/backend"
    source venv/bin/activate
    python main.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    
    sleep 5
    
    # Start frontend and monitor for Vite ready message
    cd "$INSTALL_DIR/frontend"
    print_info "Starting frontend..."
    echo ""
    
    # Create temp log file
    VITE_LOG="/tmp/instalens-vite-$$.log"
    touch "$VITE_LOG"
    
    # Start pnpm dev redirecting to log
    pnpm dev > "$VITE_LOG" 2>&1 &
    FRONTEND_PID=$!
    
    # Show Vite output in real-time
    tail -f "$VITE_LOG" &
    TAIL_PID=$!
    
    # Monitor log for "ready in" message
    while ! grep -q "ready in" "$VITE_LOG" 2>/dev/null; do
        sleep 0.5
    done
    
    # Kill tail and clean screen
    kill $TAIL_PID 2>/dev/null
    wait $TAIL_PID 2>/dev/null
    
    # Show final status
    print_header_running
    print_success "Backend started (PID: $BACKEND_PID)"
    print_info "Backend running on: ${BOLD}http://localhost:8000${NC}"
    print_success "Frontend started (PID: $FRONTEND_PID)"
    print_info "Frontend running on: ${BOLD}http://localhost:5173${NC}"
    echo ""
    print_warning "Press Ctrl+C to stop both servers"
    echo ""
    
    # Wait for frontend (bring to foreground)
    wait $FRONTEND_PID
    
    # Cleanup on exit
    kill $BACKEND_PID 2>/dev/null
    rm -f "$VITE_LOG"
}

# ==============================================
# Run
# ==============================================

main
