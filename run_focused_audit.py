#!/usr/bin/env python3
"""
Simple runner for the focused dashboard callback audit
This avoids the 41k file issue by targeting only your dashboard directories
"""

if __name__ == "__main__":
    from focused_dashboard_auditor import FocusedDashboardAuditor
    
    print("🎯 RUNNING FOCUSED DASHBOARD CALLBACK AUDIT")
    print("Targeting: core/, pages/, components/, services/, analytics/, plugins/")
    print("=" * 60)
    
    # Run focused audit
    auditor = FocusedDashboardAuditor()
    results = auditor.scan_focused_codebase()
    
    # Generate and display the dashboard-specific report
    report = auditor.generate_dashboard_report(results)
    print(report)
    
    print("\n" + "=" * 60)
    print("✅ FOCUSED AUDIT COMPLETE!")
    print("📁 Check 'focused_callback_audit/' for detailed files")