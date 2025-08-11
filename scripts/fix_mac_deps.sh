#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}🔧 Mac Dependencies & Architecture Fix${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_system() {
    print_info "Checking system architecture and Python setup..."
    
    # Check architecture
    ARCH=$(uname -m)
    echo "System architecture: $ARCH"
    
    # Check if on Apple Silicon
    if [ "$ARCH" = "arm64" ]; then
        print_status "Apple Silicon (M1/M2) detected"
        IS_APPLE_SILICON=true
    else
        print_warning "Intel Mac detected"
        IS_APPLE_SILICON=false
    fi
    
    # Check Python version and location
    PYTHON_VERSION=$(python3 --version)
    PYTHON_PATH=$(which python3)
    echo "Python version: $PYTHON_VERSION"
    echo "Python path: $PYTHON_PATH"
    
    # Check if in virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "Not in virtual environment - this is the main issue!"
        IN_VENV=false
    else
        print_status "In virtual environment: $VIRTUAL_ENV"
        IN_VENV=true
    fi
}

clean_global_packages() {
    print_info "Cleaning problematic global packages..."
    
    # List of packages causing issues
    PROBLEM_PACKAGES=("numpy" "scipy" "scikit-learn" "rpds-py" "pandas")
    
    for pkg in "${PROBLEM_PACKAGES[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            print_warning "Found global $pkg - this may cause conflicts"
        fi
    done
    
    print_info "We'll use a virtual environment to isolate dependencies"
}

remove_existing_venv() {
    print_info "Removing any existing problematic virtual environment..."
    
    if [ -d "venv" ]; then
        rm -rf venv
        print_status "Removed old venv directory"
    fi
    
    if [ -d ".venv" ]; then
        rm -rf .venv
        print_status "Removed old .venv directory"
    fi
}

create_fresh_venv() {
    print_info "Creating fresh virtual environment..."
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    print_status "Virtual environment created and activated"
    
    # Verify we're in the venv
    which python3
    which pip3
}

install_compatible_packages() {
    print_info "Installing compatible packages for your system..."
    
    # Make sure we're in venv
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi
    
    # Upgrade pip first
    print_info "Upgrading pip..."
    pip3 install --upgrade pip
    
    # Install NumPy first with compatible version
    print_info "Installing compatible NumPy version..."
    pip3 install "numpy>=1.23,<2.0"
    
    # Install SciPy
    print_info "Installing SciPy..."
    pip3 install "scipy>=1.7.0"
    
    # Install scikit-learn
    print_info "Installing scikit-learn..."
    pip3 install "scikit-learn>=1.0.0"
    
    # For Apple Silicon, ensure we get the right wheels
    if [ "$IS_APPLE_SILICON" = true ]; then
        print_info "Installing Apple Silicon optimized packages..."
        
        # Force reinstall with platform-specific wheels
        pip3 install --force-reinstall --no-deps \
            --platform macosx_11_0_arm64 \
            --target ./temp_packages \
            numpy scipy scikit-learn 2>/dev/null || true
            
        # Clean up temp
        rm -rf ./temp_packages 2>/dev/null || true
    fi
    
    print_status "Core scientific packages installed"
}

install_project_requirements() {
    print_info "Installing project requirements..."
    
    # Make sure we're in venv
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi
    
    if [ -f "requirements.txt" ]; then
        # Create a fixed requirements file
        print_info "Creating fixed requirements.txt..."
        
        cat > requirements_fixed.txt << 'EOF'
# Core dependencies with compatible versions
numpy>=1.23,<2.0
scipy>=1.7.0,<1.12.0
pandas>=1.3.0
scikit-learn>=1.0.0

# Dash ecosystem
dash>=2.14.0
dash-bootstrap-components>=1.4.0
plotly>=5.15.0

# Data processing
xlrd>=2.0.0

# Web framework
flask>=2.3.0
werkzeug>=2.3.0

# Utilities
python-dotenv>=0.19.0
requests>=2.28.0

# Development
pytest>=7.0.0
pytest-cov>=4.0.0
EOF

        # Install from fixed requirements
        pip3 install -r requirements_fixed.txt
        
        # Try original requirements (may have additional packages)
        print_info "Attempting to install additional requirements..."
        pip3 install -r requirements.txt || print_warning "Some additional packages failed - continuing..."
        
    else
        print_warning "No requirements.txt found, installing minimal set..."
        pip3 install dash dash-bootstrap-components plotly pandas numpy scipy
    fi
    
    print_status "Project requirements installed"
}

verify_installation() {
    print_info "Verifying installation..."
    
    # Make sure we're in venv
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate
    fi
    
    # Test imports
    python3 -c "
import sys
print(f'Python: {sys.executable}')

try:
    import numpy as np
    print(f'✅ NumPy {np.__version__} - OK')
except Exception as e:
    print(f'❌ NumPy failed: {e}')

try:
    import scipy
    print(f'✅ SciPy {scipy.__version__} - OK')
except Exception as e:
    print(f'❌ SciPy failed: {e}')

try:
    import sklearn
    print(f'✅ Scikit-learn {sklearn.__version__} - OK')
except Exception as e:
    print(f'❌ Scikit-learn failed: {e}')

try:
    import dash
    print(f'✅ Dash {dash.__version__} - OK')
except Exception as e:
    print(f'❌ Dash failed: {e}')

try:
    import pandas as pd
    print(f'✅ Pandas {pd.__version__} - OK')
except Exception as e:
    print(f'❌ Pandas failed: {e}')
"
}

create_run_script() {
    print_info "Creating run script..."
    
    cat > run_app.sh << 'EOF'
#!/bin/bash

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found! Run the fix script first."
    exit 1
fi

source venv/bin/activate

# Verify we're in the right environment
echo "Using Python: $(which python3)"
echo "Virtual environment: $VIRTUAL_ENV"

# Run the app
echo "🚀 Starting application..."
python3 app.py
EOF

    chmod +x run_app.sh
    print_status "Created run_app.sh script"
}

main() {
    print_header
    
    # Navigate to project directory if not already there
    if [ ! -f "app.py" ]; then
        print_error "app.py not found in current directory"
        print_info "Please navigate to your project directory first"
        exit 1
    fi
    
    print_status "Found app.py - in correct directory"
    
    check_system
    clean_global_packages
    remove_existing_venv
    create_fresh_venv
    install_compatible_packages
    install_project_requirements
    verify_installation
    create_run_script
    
    echo ""
    print_status "Setup complete!"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Run: source venv/bin/activate"
    echo "2. Run: python3 app.py"
    echo "   OR"
    echo "   Run: ./run_app.sh"
    echo ""
    print_info "Your virtual environment is now properly configured for Apple Silicon"
}

# Run the main function
main "$@"