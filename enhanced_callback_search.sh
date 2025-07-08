#!/bin/bash

# =============================================================================
# Enhanced Callback Pattern Search
# Search for actual callback patterns found in your codebase
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "🔍 ENHANCED CALLBACK PATTERN SEARCH"
    echo "=================================================================="
    echo -e "${NC}"
}

print_section() {
    echo -e "${BLUE}"
    echo "🔹 $1"
    echo "=================================================================="
    echo -e "${NC}"
}

# Function to search for patterns with context
search_pattern() {
    local pattern="$1"
    local description="$2"
    local files="$3"
    
    echo -e "${YELLOW}Searching for: $description${NC}"
    echo "Pattern: $pattern"
    echo ""
    
    # Search with line numbers and context
    if grep -rn --include="*.py" -B2 -A5 "$pattern" $files 2>/dev/null; then
        echo ""
        echo -e "${GREEN}✓ Found matches for: $description${NC}"
    else
        echo -e "${RED}✗ No matches found for: $description${NC}"
    fi
    echo ""
    echo "----------------------------------------"
    echo ""
}

# Enhanced search function with multiple patterns
search_multiple_patterns() {
    local description="$1"
    shift
    local patterns=("$@")
    
    echo -e "${YELLOW}🔍 $description${NC}"
    
    local found_any=false
    for pattern in "${patterns[@]}"; do
        if grep -rn --include="*.py" "$pattern" core/ pages/ components/ services/ analytics/ plugins/ app.py wsgi.py 2>/dev/null | head -10; then
            found_any=true
        fi
    done
    
    if [ "$found_any" = false ]; then
        echo -e "${RED}✗ No matches found${NC}"
    fi
    echo ""
    echo "----------------------------------------"
    echo ""
}

# Quick count function
count_patterns() {
    local pattern="$1"
    local description="$2"
    
    local count=$(grep -r --include="*.py" "$pattern" core/ pages/ components/ services/ analytics/ plugins/ app.py wsgi.py 2>/dev/null | wc -l)
    echo -e "${CYAN}$description: ${GREEN}$count matches${NC}"
}

main() {
    print_header
    
    echo "Targeting directories: core/, pages/, components/, services/, analytics/, plugins/, app.py, wsgi.py"
    echo ""
    
    # Quick counts first
    print_section "QUICK PATTERN COUNTS"
    count_patterns "@.*\.callback" "All @*.callback patterns"
    count_patterns "callback.*=" "Callback assignments"
    count_patterns "register.*callback" "Register callback patterns"
    count_patterns "unified_callback" "Unified callback patterns"
    count_patterns "app\.callback" "Direct app.callback patterns"
    count_patterns "CallbackEvent\." "Callback events"
    count_patterns "def.*callback" "Callback function definitions"
    echo ""
    
    # Detailed searches based on your actual patterns
    print_section "TRULYUNIFIEDCALLBACKS PATTERNS"
    search_multiple_patterns "TrulyUnifiedCallbacks decorator patterns" \
        "@callbacks\.callback" \
        "@callbacks\.unified_callback" \
        "@coord\.unified_callback" \
        "\.unified_callback(" \
        "\.callback("
    
    print_section "CALLBACK REGISTRY PATTERNS"
    search_multiple_patterns "CallbackRegistry patterns" \
        "\.handle_register" \
        "registry\.register" \
        "@self\.app\.callback" \
        "CallbackRegistry("
    
    print_section "EVENT CALLBACK PATTERNS"
    search_multiple_patterns "Event callback patterns" \
        "register_callback.*CallbackEvent" \
        "register_handler.*event" \
        "\.fire_event" \
        "events\.register_callback" \
        "controller\.register_handler"
    
    print_section "UNIFIED DECORATOR PATTERNS"
    search_multiple_patterns "Unified decorator patterns" \
        "@unified_callback" \
        "unified_callback(" \
        "safe_callback" \
        "@role_required"
    
    print_section "LEGACY DASH PATTERNS"
    search_multiple_patterns "Legacy Dash patterns" \
        "@app\.callback" \
        "app\.callback(" \
        "clientside_callback"
    
    print_section "FUNCTION DEFINITIONS"
    search_multiple_patterns "Callback function definitions" \
        "def.*callback.*:" \
        "def handle_" \
        "def on_" \
        "def update_" \
        "def refresh_"
    
    print_section "CALLBACK IMPORTS"
    search_multiple_patterns "Callback-related imports" \
        "from.*callback" \
        "import.*callback" \
        "from core\.truly_unified_callbacks" \
        "from core\.callback" \
        "TrulyUnifiedCallbacks"
    
    print_section "DETAILED FILE ANALYSIS"
    echo "Files most likely to contain callbacks:"
    echo ""
    
    # Find Python files with high callback density
    echo -e "${YELLOW}Files with multiple callback keywords:${NC}"
    for file in $(find core/ pages/ components/ services/ analytics/ plugins/ -name "*.py" 2>/dev/null); do
        if [ -f "$file" ]; then
            local callback_count=$(grep -c -i "callback\|@.*\.callback\|register.*callback\|unified_callback" "$file" 2>/dev/null || echo 0)
            if [ "$callback_count" -gt 2 ]; then
                echo -e "${GREEN}$file${NC}: $callback_count callback references"
            fi
        fi
    done
    
    echo ""
    echo -e "${YELLOW}Checking specific important files:${NC}"
    
    # Check key files
    important_files=(
        "core/app_factory.py"
        "core/truly_unified_callbacks.py"
        "core/callback_registry.py"
        "core/callback_controller.py"
        "pages/deep_analytics.py"
        "app.py"
    )
    
    for file in "${important_files[@]}"; do
        if [ -f "$file" ]; then
            local callback_count=$(grep -c -i "callback\|@.*\.callback\|register.*callback" "$file" 2>/dev/null || echo 0)
            echo -e "${CYAN}$file${NC}: $callback_count callback references"
            
            if [ "$callback_count" -gt 0 ]; then
                echo "  Sample matches:"
                grep -n -i "callback\|@.*\.callback\|register.*callback" "$file" 2>/dev/null | head -3 | sed 's/^/    /'
            fi
        else
            echo -e "${RED}$file${NC}: File not found"
        fi
        echo ""
    done
    
    print_section "SUMMARY"
    
    # Generate summary statistics
    echo "Summary of callback patterns found:"
    echo ""
    
    total_callback_files=$(find core/ pages/ components/ services/ analytics/ plugins/ -name "*.py" -exec grep -l -i "callback" {} \; 2>/dev/null | wc -l)
    total_py_files=$(find core/ pages/ components/ services/ analytics/ plugins/ -name "*.py" 2>/dev/null | wc -l)
    
    echo -e "📁 Python files with 'callback': ${GREEN}$total_callback_files${NC} out of $total_py_files files"
    
    # Count specific patterns
    truly_unified=$(grep -r --include="*.py" "@.*\.unified_callback\|@.*\.callback" core/ pages/ components/ services/ analytics/ plugins/ 2>/dev/null | wc -l)
    legacy_dash=$(grep -r --include="*.py" "@app\.callback" core/ pages/ components/ services/ analytics/ plugins/ 2>/dev/null | wc -l)
    event_callbacks=$(grep -r --include="*.py" "CallbackEvent\." core/ pages/ components/ services/ analytics/ plugins/ 2>/dev/null | wc -l)
    
    echo -e "✅ TrulyUnified patterns: ${GREEN}$truly_unified${NC}"
    echo -e "🔥 Legacy Dash patterns: ${GREEN}$legacy_dash${NC}"
    echo -e "📡 Event callbacks: ${GREEN}$event_callbacks${NC}"
    
    echo ""
    echo -e "${CYAN}=================================================================="
    echo "✅ ENHANCED CALLBACK SEARCH COMPLETE!"
    echo "=================================================================="
    echo -e "${NC}"
}

# Help function
show_help() {
    echo "Enhanced Callback Pattern Search Script"
    echo ""
    echo "Usage: $0"
    echo ""
    echo "This script searches for actual callback patterns used in your dashboard:"
    echo "  - TrulyUnifiedCallbacks patterns (@callbacks.callback, etc.)"
    echo "  - CallbackRegistry patterns (handle_register, etc.)"
    echo "  - Event callback patterns (CallbackEvent, etc.)"
    echo "  - Legacy Dash patterns (@app.callback)"
    echo "  - Function definitions and imports"
    echo ""
}

case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main
        ;;
esac