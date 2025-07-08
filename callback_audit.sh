#!/bin/bash

# =============================================================================
# Dashboard Callback Audit Script
# Comprehensive callback pattern analysis for your dashboard
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIT_DIR="callback_audit_results"
PYTHON_CMD="python3"

# Functions
print_header() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "🎯 DASHBOARD CALLBACK AUDIT SCRIPT"
    echo "=================================================================="
    echo -e "${NC}"
}

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

# Check if Python 3 is available
check_python() {
    print_info "Checking Python 3 availability..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_status "Found: $PYTHON_VERSION"
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version)
        if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
            print_status "Found: $PYTHON_VERSION"
            PYTHON_CMD="python"
        else
            print_error "Python 3 required, found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.7+ and try again."
        exit 1
    fi
}

# Create the auditor Python script inline
create_auditor_script() {
    print_info "Creating callback auditor script..."
    
    cat > "${SCRIPT_DIR}/dashboard_callback_auditor.py" << 'EOF'
#!/usr/bin/env python3
"""
Dashboard Callback Auditor - Inline version for bash script
Focuses on your dashboard directories only
"""
import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
import json

@dataclass
class CallbackPattern:
    file_path: str
    line_number: int
    pattern_type: str
    decorator_name: str
    callback_id: Optional[str]
    component_name: Optional[str]
    raw_code: str
    output_targets: List[str]
    input_sources: List[str]
    function_name: str
    complexity_score: int

class DashboardCallbackAuditor:
    """Focused auditor for dashboard callback patterns"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.patterns: List[CallbackPattern] = []
        self.pattern_counts = Counter()
        self.namespace_usage = defaultdict(list)
        self.output_conflicts = defaultdict(list)
        
        # Your specific callback patterns
        self.callback_signatures = {
            'truly_unified_callback': [
                r'@callbacks\.callback\(',
                r'@callbacks\.unified_callback\(',
                r'@callbacks\.register_callback\(',
            ],
            'master_callback_system': [
                r'@system\.register_dash_callback\(',
                r'@master_system\.register_dash_callback\(',
            ],
            'callback_registry': [
                r'registry\.handle_register\(',
                r'\.handle_register\(',
            ],
            'callback_controller': [
                r'controller\.handle_register\(',
                r'CallbackController\(\)\.handle_register\(',
                r'\.handle_register\(CallbackEvent\.',
            ],
            'legacy_dash': [
                r'@app\.callback\(',
                r'app\.callback\(',
            ],
            'clientside_callback': [
                r'\.clientside_callback\(',
                r'app\.clientside_callback\(',
                r'\.handle_register_clientside\(',
            ]
        }
        
        # Target directories for your dashboard
        self.target_directories = [
            "core", "pages", "components", "services", 
            "analytics", "plugins", "app.py", "wsgi.py"
        ]
        
        # Skip patterns
        self.skip_patterns = [
            'venv', '__pycache__', '.git', 'node_modules', 'build', 'dist',
            'tests', '.pytest_cache', 'docs', '.vscode', '.idea', 'data',
            'logs', 'temp', 'cache', 'migrations', 'legacy'
        ]
    
    def scan_dashboard(self) -> dict:
        """Scan dashboard directories for callback patterns"""
        print("🔍 Scanning dashboard directories...")
        
        # Find existing target directories
        existing_dirs = []
        for target in self.target_directories:
            target_path = self.root_path / target
            if target_path.exists():
                existing_dirs.append(target)
        
        print(f"📁 Found directories: {', '.join(existing_dirs)}")
        
        total_files = 0
        for target_dir in existing_dirs:
            target_path = self.root_path / target_dir
            
            if target_path.is_file() and target_path.suffix == '.py':
                # Single Python file
                total_files += 1
                self._analyze_file(target_path)
            elif target_path.is_dir():
                # Directory of Python files
                py_files = [f for f in target_path.rglob("*.py") if not self._should_skip(f)]
                total_files += len(py_files)
                print(f"  📂 {target_dir}: {len(py_files)} Python files")
                
                for py_file in py_files:
                    self._analyze_file(py_file)
        
        print(f"✅ Analyzed {total_files} files, found {len(self.patterns)} callbacks")
        
        # Generate results
        results = self._generate_results()
        results['scanned_directories'] = existing_dirs
        results['total_files'] = total_files
        
        return results
    
    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        file_str = str(file_path)
        return any(pattern in file_str for pattern in self.skip_patterns)
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file for callback patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # AST analysis
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        for decorator in node.decorator_list:
                            pattern = self._analyze_decorator(decorator, node, file_path, lines)
                            if pattern:
                                self.patterns.append(pattern)
                                self.pattern_counts[pattern.pattern_type] += 1
                                self._track_pattern(pattern)
            except SyntaxError:
                pass  # Skip files with syntax errors
            
            # Regex analysis for patterns AST might miss
            self._regex_analysis(content, file_path, lines)
            
        except (UnicodeDecodeError, FileNotFoundError):
            pass  # Skip problematic files
    
    def _analyze_decorator(self, decorator, func_node, file_path, lines) -> Optional[CallbackPattern]:
        """Analyze a decorator for callback patterns"""
        decorator_code = self._get_source_code(decorator, lines)
        pattern_type = self._classify_pattern(decorator_code)
        
        if not pattern_type:
            return None
        
        return CallbackPattern(
            file_path=str(file_path),
            line_number=getattr(decorator, 'lineno', 0),
            pattern_type=pattern_type,
            decorator_name=self._get_decorator_name(decorator),
            callback_id=self._extract_callback_id(decorator),
            component_name=self._extract_component_name(decorator),
            raw_code=decorator_code.strip(),
            output_targets=self._extract_outputs(decorator),
            input_sources=self._extract_inputs(decorator),
            function_name=func_node.name,
            complexity_score=self._calculate_complexity(func_node)
        )
    
    def _get_source_code(self, decorator, lines) -> str:
        """Get source code for decorator"""
        if hasattr(decorator, 'lineno') and decorator.lineno <= len(lines):
            return lines[decorator.lineno - 1]
        return str(decorator)
    
    def _classify_pattern(self, decorator_code: str) -> Optional[str]:
        """Classify decorator as callback pattern type"""
        for pattern_type, signatures in self.callback_signatures.items():
            if any(re.search(sig, decorator_code) for sig in signatures):
                return pattern_type
        return None
    
    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{getattr(decorator.value, 'id', 'unknown')}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return "unknown"
    
    def _extract_callback_id(self, decorator) -> Optional[str]:
        """Extract callback_id from decorator"""
        if isinstance(decorator, ast.Call):
            for keyword in getattr(decorator, 'keywords', []):
                if keyword.arg == 'callback_id':
                    if isinstance(keyword.value, ast.Constant):
                        value = keyword.value.value
                        if isinstance(value, str):
                            return value
                        if value is not None:
                            return str(value)
                        return None
        return None
    
    def _extract_component_name(self, decorator) -> Optional[str]:
        """Extract component_name from decorator"""
        if isinstance(decorator, ast.Call):
            for keyword in getattr(decorator, 'keywords', []):
                if keyword.arg == 'component_name':
                    if isinstance(keyword.value, ast.Constant):
                        value = keyword.value.value
                        if isinstance(value, str):
                            return value
                        if value is not None:
                            return str(value)
                        return None
        return None
    
    def _extract_outputs(self, decorator) -> List[str]:
        """Extract Output targets"""
        # Simplified extraction - would need more complex logic for full parsing
        return []
    
    def _extract_inputs(self, decorator) -> List[str]:
        """Extract Input sources"""
        # Simplified extraction
        return []
    
    def _calculate_complexity(self, func_node) -> int:
        """Calculate function complexity score"""
        complexity = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While)):
                complexity += 2
            elif isinstance(node, ast.Try):
                complexity += 3
        return complexity
    
    def _regex_analysis(self, content: str, file_path: Path, lines: List[str]) -> None:
        """Regex analysis for patterns AST might miss"""
        event_patterns = [
            r'\.handle_register\(CallbackEvent\.(\w+)',
            r'\.register\(CallbackEvent\.(\w+)',
            r'controller\.fire_event\(CallbackEvent\.(\w+)'
        ]
        
        for i, line in enumerate(lines):
            for pattern in event_patterns:
                if re.search(pattern, line):
                    event_pattern = CallbackPattern(
                        file_path=str(file_path),
                        line_number=i + 1,
                        pattern_type='callback_controller_event',
                        decorator_name='event_handler',
                        callback_id=None,
                        component_name=None,
                        raw_code=line.strip(),
                        output_targets=[],
                        input_sources=[],
                        function_name='event_handler',
                        complexity_score=1
                    )
                    self.patterns.append(event_pattern)
                    self.pattern_counts['callback_controller_event'] += 1
                    self._track_pattern(event_pattern)
    
    def _track_pattern(self, pattern: CallbackPattern) -> None:
        """Track pattern for analysis"""
        if pattern.component_name:
            self.namespace_usage[pattern.component_name].append(pattern.callback_id)
        
        for output in pattern.output_targets:
            self.output_conflicts[output].append({
                'file': pattern.file_path,
                'callback_id': pattern.callback_id,
                'line': pattern.line_number
            })
    
    def _generate_results(self) -> dict:
        """Generate analysis results"""
        total_callbacks = len(self.patterns)
        
        # Analyze conflicts
        conflicts = []
        for output_id, usages in self.output_conflicts.items():
            if len(usages) > 1:
                conflicts.append({
                    'output_id': output_id,
                    'conflicting_files': [u['file'] for u in usages],
                    'conflicting_callbacks': [u['callback_id'] for u in usages if u['callback_id']],
                    'severity': 'HIGH' if len(usages) > 2 else 'MEDIUM'
                })
        
        # Generate recommendations
        recommendations = []
        
        legacy_count = self.pattern_counts.get('legacy_dash', 0)
        if legacy_count > 0:
            recommendations.append(f"🔥 HIGH PRIORITY: Migrate {legacy_count} legacy @app.callback patterns")
        
        truly_unified_count = self.pattern_counts.get('truly_unified_callback', 0)
        if truly_unified_count / max(total_callbacks, 1) > 0.8:
            recommendations.append("✅ EXCELLENT: Most callbacks use TrulyUnifiedCallbacks")
        
        high_conflicts = len([c for c in conflicts if c['severity'] == 'HIGH'])
        if high_conflicts > 0:
            recommendations.append(f"⚠️ URGENT: Resolve {high_conflicts} high-severity conflicts")
        
        if total_callbacks == 0:
            recommendations.append("🔍 Consider expanding search or checking different directories")
        
        return {
            'summary': {
                'total_callbacks': total_callbacks,
                'pattern_distribution': dict(self.pattern_counts),
                'files_with_callbacks': len(set(p.file_path for p in self.patterns)),
                'unique_namespaces': len(self.namespace_usage),
                'total_conflicts': len(conflicts),
                'high_severity_conflicts': high_conflicts,
                'average_complexity': sum(p.complexity_score for p in self.patterns) / max(total_callbacks, 1)
            },
            'conflicts': conflicts,
            'recommendations': recommendations,
            'patterns': [
                {
                    'file_path': p.file_path,
                    'pattern_type': p.pattern_type,
                    'function_name': p.function_name,
                    'callback_id': p.callback_id,
                    'component_name': p.component_name,
                    'complexity_score': p.complexity_score
                }
                for p in self.patterns
            ]
        }
    
    def generate_report(self, results: dict) -> str:
        """Generate human-readable report"""
        summary = results['summary']
        
        report = "🎯 DASHBOARD CALLBACK AUDIT REPORT\n"
        report += "=" * 50 + "\n\n"
        
        report += "📊 SUMMARY:\n"
        report += f"  Total Callbacks: {summary['total_callbacks']:,}\n"
        report += f"  Files with Callbacks: {summary['files_with_callbacks']:,}\n"
        report += f"  Pattern Types: {len(summary['pattern_distribution'])}\n"
        report += f"  Conflicts: {summary['total_conflicts']} ({summary['high_severity_conflicts']} critical)\n\n"
        
        if summary['pattern_distribution']:
            report += "📈 PATTERN DISTRIBUTION:\n"
            for pattern_type, count in summary['pattern_distribution'].items():
                percentage = (count / summary['total_callbacks']) * 100 if summary['total_callbacks'] > 0 else 0
                emoji = self._get_emoji(pattern_type)
                report += f"  {emoji} {pattern_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)\n"
            report += "\n"
        
        if results['conflicts']:
            report += "⚠️ CONFLICTS:\n"
            for conflict in results['conflicts']:
                report += f"  • {conflict['output_id']} ({conflict['severity']})\n"
            report += "\n"
        
        if results['recommendations']:
            report += "🚀 RECOMMENDATIONS:\n"
            for i, rec in enumerate(results['recommendations'], 1):
                report += f"  {i}. {rec}\n"
            report += "\n"
        
        report += "📋 NEXT STEPS:\n"
        if summary['total_callbacks'] > 0:
            report += "  1. Review pattern distribution above\n"
            report += "  2. Address any high-priority recommendations\n"
            report += "  3. Resolve conflicts if present\n"
            report += "  4. Consider implementing Unicode safety wrappers\n"
        else:
            report += "  1. Check if callbacks are in other directories\n"
            report += "  2. Verify callback registration patterns\n"
            report += "  3. Consider running audit on broader scope\n"
        
        return report
    
    def _get_emoji(self, pattern_type: str) -> str:
        """Get emoji for pattern type"""
        emojis = {
            'truly_unified_callback': '✅',
            'master_callback_system': '⚡',
            'legacy_dash': '🔥',
            'callback_registry': '📋',
            'callback_controller': '🎛️',
            'clientside_callback': '🌐',
            'callback_controller_event': '📡'
        }
        return emojis.get(pattern_type, '❓')
    
    def save_results(self, results: dict, output_dir: str) -> None:
        """Save results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save JSON data
        with open(output_path / "audit_data.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save text report
        report = self.generate_report(results)
        with open(output_path / "audit_report.txt", 'w') as f:
            f.write(report)
        
        print(f"📁 Results saved to {output_path}/")

if __name__ == "__main__":
    auditor = DashboardCallbackAuditor()
    results = auditor.scan_dashboard()
    
    # Display results
    print("\n" + auditor.generate_report(results))
    
    # Save results
    auditor.save_results(results, "callback_audit_results")
EOF

    print_status "Auditor script created: dashboard_callback_auditor.py"
}

# Run the callback audit
run_audit() {
    print_info "Starting dashboard callback audit..."
    
    if ! $PYTHON_CMD "${SCRIPT_DIR}/dashboard_callback_auditor.py"; then
        print_error "Audit failed. Check Python script for errors."
        exit 1
    fi
    
    print_status "Audit completed successfully!"
}

# Display results summary
show_results() {
    local audit_file="${AUDIT_DIR}/audit_report.txt"
    
    if [[ -f "$audit_file" ]]; then
        print_info "Displaying audit results..."
        echo ""
        cat "$audit_file"
        echo ""
        print_status "Full results saved in: ${AUDIT_DIR}/"
        print_info "Check ${AUDIT_DIR}/audit_data.json for detailed data"
    else
        print_warning "Report file not found. Check audit execution."
    fi
}

# Clean up function
cleanup() {
    if [[ -f "${SCRIPT_DIR}/dashboard_callback_auditor.py" ]]; then
        print_info "Cleaning up temporary files..."
        rm -f "${SCRIPT_DIR}/dashboard_callback_auditor.py"
        print_status "Cleanup completed"
    fi
}

# Main execution
main() {
    print_header
    
    # Check prerequisites
    check_python
    
    # Create auditor script
    create_auditor_script
    
    # Run audit
    run_audit
    
    # Show results
    show_results
    
    # Cleanup
    if [[ "${1:-}" != "--keep-files" ]]; then
        cleanup
    fi
    
    echo -e "${GREEN}"
    echo "=================================================================="
    echo "✅ DASHBOARD CALLBACK AUDIT COMPLETE!"
    echo "=================================================================="
    echo -e "${NC}"
    
    if [[ -d "$AUDIT_DIR" ]]; then
        echo "📁 Results location: ./${AUDIT_DIR}/"
        echo "📊 Data file: ./${AUDIT_DIR}/audit_data.json"
        echo "📄 Report file: ./${AUDIT_DIR}/audit_report.txt"
    fi
}

# Help function
show_help() {
    echo "Dashboard Callback Audit Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --keep-files    Keep temporary Python files after audit"
    echo "  --help, -h      Show this help message"
    echo ""
    echo "This script analyzes callback patterns in your dashboard codebase."
    echo "It focuses on: core/, pages/, components/, services/, analytics/, plugins/"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac