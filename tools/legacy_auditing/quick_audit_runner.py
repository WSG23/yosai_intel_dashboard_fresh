#!/usr/bin/env python3
"""
Quick Callback Audit Runner
Run this script immediately to get your callback landscape mapped out!

Usage:
    python3 quick_audit_runner.py
    python3 quick_audit_runner.py --path /path/to/your/project
    python3 quick_audit_runner.py --detailed  # More verbose output
"""
import argparse
import sys
from pathlib import Path

# Import the auditor (assumes it's saved as callback_auditor.py)
try:
    from tailored_callback_auditor import YourSystemCallbackAuditor
except ImportError:
    print("❌ Could not import YourSystemCallbackAuditor")
    print("💡 Make sure 'tailored_callback_auditor.py' is in the same directory")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Quick Callback System Audit")
    parser.add_argument("--path", "-p", default=".", help="Path to your project (default: current directory)")
    parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed output")
    parser.add_argument("--save", "-s", action="store_true", help="Save results to files")
    parser.add_argument("--conflicts-only", "-c", action="store_true", help="Show only conflicts")
    
    args = parser.parse_args()
    
    print("🎯 CALLBACK SYSTEM AUDIT STARTING...")
    print(f"📁 Scanning: {Path(args.path).absolute()}")
    print("-" * 50)
    
    # Run the audit
    auditor = YourSystemCallbackAuditor(args.path)
    results = auditor.scan_complete_codebase()
    
    if args.conflicts_only:
        show_conflicts_only(results)
    elif args.detailed:
        show_detailed_results(results, auditor)
    else:
        show_quick_summary(results)
    
    if args.save:
        auditor.save_results(results)
        print("\n📁 Detailed results saved to 'callback_audit_results/' directory")

def show_quick_summary(results):
    """Show quick summary for immediate insights"""
    summary = results['summary']
    
    print(f"""
🎯 QUICK CALLBACK AUDIT SUMMARY
{'='*50}

📊 OVERVIEW:
   Total Callbacks: {summary['total_callbacks']:,}
   Files with Callbacks: {summary['files_with_callbacks']:,}
   Pattern Types: {len(summary['pattern_distribution'])}
   Namespaces: {summary['unique_namespaces']:,}

📈 PATTERN BREAKDOWN:""")
    
    for pattern_type, count in summary['pattern_distribution'].items():
        percentage = (count / summary['total_callbacks']) * 100 if summary['total_callbacks'] > 0 else 0
        indicator = get_pattern_indicator(pattern_type)
        print(f"   {indicator} {pattern_type.replace('_', ' ').title()}: {count:,} ({percentage:.1f}%)")
    
    print(f"""
⚠️  CONFLICTS:
   Total Conflicts: {summary['total_conflicts']:,}
   High Priority: {summary['high_severity_conflicts']:,}
""")
    
    if results['conflicts']:
        print("   🔥 Critical Conflicts:")
        for conflict in results['conflicts'][:3]:
            if conflict.severity == 'HIGH':
                print(f"      • {conflict.output_id} - {len(conflict.conflicting_callbacks)} callbacks")
    
    print(f"""
🧩 COMPLEXITY:
   Average Score: {summary['average_complexity']:.1f}
   Most Complex: {summary['most_complex_callbacks'][0][0] if summary['most_complex_callbacks'] else 'None'} (Score: {summary['most_complex_callbacks'][0][1] if summary['most_complex_callbacks'] else 0})
""")
    
    print("🚀 TOP 3 RECOMMENDATIONS:")
    for i, recommendation in enumerate(results['recommendations'][:3], 1):
        print(f"   {i}. {recommendation}")
    
    print(f"""
📋 NEXT STEPS:
   1. Focus on {summary['high_severity_conflicts']} high-priority conflicts
   2. Migrate {summary['pattern_distribution'].get('legacy_dash', 0)} legacy @app.callback patterns
   3. Run detailed audit: python3 quick_audit_runner.py --detailed --save
""")

def show_detailed_results(results, auditor):

    """Show detailed results"""
    print(auditor.generate_detailed_report(results))

def show_conflicts_only(results):
    """Show only conflict analysis"""
    print("⚠️  CALLBACK CONFLICTS ANALYSIS")
    print("=" * 40)
    
    if not results['conflicts']:
        print("✅ No callback conflicts detected!")
        return
    
    # Group by severity
    high_conflicts = [c for c in results['conflicts'] if c.severity == 'HIGH']
    medium_conflicts = [c for c in results['conflicts'] if c.severity == 'MEDIUM']
    low_conflicts = [c for c in results['conflicts'] if c.severity == 'LOW']
    
    if high_conflicts:
        print(f"\n🔥 HIGH PRIORITY CONFLICTS ({len(high_conflicts)}):")
        for conflict in high_conflicts:
            print(f"\n   Output: {conflict.output_id}")
            print(f"   Files: {', '.join(set(conflict.conflicting_files))}")
            print(f"   Callbacks: {', '.join(filter(None, conflict.conflicting_callbacks))}")
            print(f"   Resolution: {conflict.resolution_suggestion}")
    
    if medium_conflicts:
        print(f"\n⚡ MEDIUM PRIORITY CONFLICTS ({len(medium_conflicts)}):")
        for conflict in medium_conflicts:
            print(f"   • {conflict.output_id} - {conflict.resolution_suggestion}")
    
    if low_conflicts:
        print(f"\n📝 LOW PRIORITY CONFLICTS ({len(low_conflicts)}):")
        for conflict in low_conflicts:
            print(f"   • {conflict.output_id}")

def get_pattern_indicator(pattern_type):
    """Get indicator emoji for pattern type"""
    indicators = {
        'truly_unified_callback': '✅',  # Good - this is your target
        'master_callback_system': '⚡',  # Medium - wrapper around TrulyUnified
        'callback_registry': '📋',      # Medium - separate system
        'callback_controller': '🎛️',    # Medium - event system
        'legacy_dash': '🔥',           # High priority - needs migration
        'clientside_callback': '🌐'    # Low priority - different purpose
    }
    return indicators.get(pattern_type, '❓')

if __name__ == "__main__":
    main()
