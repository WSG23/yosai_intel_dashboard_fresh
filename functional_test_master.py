#!/usr/bin/env python3
"""
Master Functional Test Runner
Orchestrates all functional testing modules and provides comprehensive reporting.
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import requests


@dataclass
class TestModuleResult:
    """Result from a test module execution."""
    module_name: str
    success: bool
    execution_time: float
    exit_code: int
    stdout: str
    stderr: str
    tests_passed: int = 0
    tests_total: int = 0


@dataclass
class FunctionalTestReport:
    """Comprehensive functional test report."""
    test_session_id: str
    start_time: str
    end_time: str
    total_duration: float
    app_url: str
    app_accessible: bool
    modules_executed: List[TestModuleResult]
    overall_success: bool
    summary: Dict[str, int]
    recommendations: List[str]


class MasterFunctionalTester:
    """Master orchestrator for all functional testing."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8052"):
        self.base_url = base_url.rstrip('/')
        self.test_modules = [
            {
                'name': 'Navigation Flow',
                'script': 'functional_test_navigator.py',
                'description': 'Tests all navbar links and page routing',
                'critical': True
            },
            {
                'name': 'Upload Functionality', 
                'script': 'functional_test_upload.py',
                'description': 'Tests file upload and validation',
                'critical': True
            },
            {
                'name': 'Interactive Features',
                'script': 'functional_test_interactive.py', 
                'description': 'Tests buttons, forms, and callbacks',
                'critical': False
            },
            {
                'name': 'Cross-Page Data Flow',
                'script': 'functional_test_dataflow.py',
                'description': 'Tests session persistence and data sharing',
                'critical': False
            }
        ]
        
        self.test_session_id = f"test_session_{int(time.time())}"
        self.start_time = datetime.now()
        
    def check_app_availability(self) -> Tuple[bool, str]:
        """Check if the application is running and accessible."""
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code in [200, 302]:
                return True, f"App accessible (status: {response.status_code})"
            else:
                return False, f"App returned status: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused - app may not be running"
        except requests.exceptions.Timeout:
            return False, "Connection timeout - app may be overloaded"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def check_test_scripts_exist(self) -> Tuple[bool, List[str]]:
        """Check if all required test scripts exist."""
        missing_scripts = []
        
        for module in self.test_modules:
            script_path = Path(module['script'])
            if not script_path.exists():
                missing_scripts.append(module['script'])
        
        return len(missing_scripts) == 0, missing_scripts

    def run_test_module(self, module_info: Dict) -> TestModuleResult:
        """Run a single test module and capture results."""
        print(f"\n🔬 Running: {module_info['name']}")
        print(f"   Script: {module_info['script']}")
        print(f"   Description: {module_info['description']}")
        print(f"   Critical: {'Yes' if module_info['critical'] else 'No'}")
        
        start_time = time.time()
        
        try:
            # Run the test script
            result = subprocess.run(
                [sys.executable, module_info['script']],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per module
            )
            
            execution_time = time.time() - start_time
            success = result.returncode == 0
            
            # Parse test counts from output if available
            tests_passed, tests_total = self._parse_test_counts(result.stdout)
            
            print(f"   ⏱️ Duration: {execution_time:.2f}s")
            print(f"   📊 Result: {'✅ PASS' if success else '❌ FAIL'}")
            if tests_total > 0:
                print(f"   📈 Tests: {tests_passed}/{tests_total}")
            
            return TestModuleResult(
                module_name=module_info['name'],
                success=success,
                execution_time=execution_time,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                tests_passed=tests_passed,
                tests_total=tests_total
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            print(f"   ⏱️ Duration: {execution_time:.2f}s")
            print(f"   ⏰ TIMEOUT after 5 minutes")
            
            return TestModuleResult(
                module_name=module_info['name'],
                success=False,
                execution_time=execution_time,
                exit_code=-1,
                stdout="",
                stderr="Test module timed out after 5 minutes",
                tests_passed=0,
                tests_total=1
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"   ⏱️ Duration: {execution_time:.2f}s")
            print(f"   💥 ERROR: {str(e)}")
            
            return TestModuleResult(
                module_name=module_info['name'],
                success=False,
                execution_time=execution_time,
                exit_code=-1,
                stdout="",
                stderr=f"Failed to execute test module: {str(e)}",
                tests_passed=0,
                tests_total=1
            )

    def _parse_test_counts(self, output: str) -> Tuple[int, int]:
        """Parse test pass/total counts from module output."""
        import re
        
        # Look for patterns like "5/7 passed" or "RESULTS: 3/5"
        patterns = [
            r'(\d+)/(\d+)\s+passed',
            r'RESULTS:\s*(\d+)/(\d+)',
            r'(\d+)/(\d+)\s+tests?\s+passed'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return int(match.group(1)), int(match.group(2))
        
        return 0, 0

    def generate_recommendations(self, results: List[TestModuleResult]) -> List[str]:
        """Generate actionable recommendations based on test results."""
        recommendations = []
        
        failed_modules = [r for r in results if not r.success]
        critical_failures = [r for r in failed_modules if any(
            m['critical'] for m in self.test_modules if m['name'] == r.module_name
        )]
        
        if critical_failures:
            recommendations.append(
                "🚨 CRITICAL: Fix critical functionality failures before deployment"
            )
            for failure in critical_failures:
                recommendations.append(f"   - Address {failure.module_name} issues")
        
        if len(failed_modules) > len(critical_failures):
            recommendations.append(
                "⚠️ NON-CRITICAL: Address remaining functionality issues for optimal UX"
            )
        
        # Specific recommendations based on failure patterns
        for result in failed_modules:
            if "navigation" in result.module_name.lower():
                recommendations.append("   - Check page routing and navbar configuration")
            elif "upload" in result.module_name.lower():
                recommendations.append("   - Verify file upload components and validation")
            elif "interactive" in result.module_name.lower():
                recommendations.append("   - Review callback registration and component interactions")
            elif "dataflow" in result.module_name.lower():
                recommendations.append("   - Check session management and data store implementations")
        
        # Performance recommendations
        slow_modules = [r for r in results if r.execution_time > 30]
        if slow_modules:
            recommendations.append("⚡ PERFORMANCE: Optimize slow-running components")
            for slow in slow_modules:
                recommendations.append(f"   - {slow.module_name} took {slow.execution_time:.1f}s")
        
        if not recommendations:
            recommendations.append("🎉 EXCELLENT: All tests passed! Your app is ready for use.")
        
        return recommendations

    def save_detailed_report(self, report: FunctionalTestReport) -> str:
        """Save detailed test report to file."""
        report_filename = f"functional_test_report_{self.test_session_id}.json"
        
        try:
            with open(report_filename, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
            
            return report_filename
            
        except Exception as e:
            print(f"⚠️ Failed to save detailed report: {e}")
            return ""

    def print_summary_report(self, report: FunctionalTestReport):
        """Print a formatted summary report."""
        print("\n" + "=" * 70)
        print("🏁 COMPREHENSIVE FUNCTIONAL TEST RESULTS")
        print("=" * 70)
        
        print(f"📅 Test Session: {report.test_session_id}")
        print(f"🕐 Started: {report.start_time}")
        print(f"🕑 Ended: {report.end_time}")
        print(f"⏱️ Total Duration: {report.total_duration:.2f} seconds")
        print(f"🌐 App URL: {report.app_url}")
        print(f"📡 App Status: {'✅ Accessible' if report.app_accessible else '❌ Not Accessible'}")
        
        print(f"\n📊 OVERALL SUMMARY")
        print(f"   Modules Executed: {len(report.modules_executed)}")
        print(f"   Modules Passed: {report.summary['modules_passed']}")
        print(f"   Modules Failed: {report.summary['modules_failed']}")
        print(f"   Total Tests: {report.summary['total_tests']}")
        print(f"   Tests Passed: {report.summary['tests_passed']}")
        print(f"   Success Rate: {report.summary['success_rate']:.1f}%")
        
        print(f"\n📋 MODULE RESULTS")
        for result in report.modules_executed:
            status = "✅ PASS" if result.success else "❌ FAIL"
            duration = f"{result.execution_time:.1f}s"
            tests = f"{result.tests_passed}/{result.tests_total}" if result.tests_total > 0 else "N/A"
            print(f"   {result.module_name:<25} {status:<8} {duration:<8} Tests: {tests}")
        
        print(f"\n💡 RECOMMENDATIONS")
        for rec in report.recommendations:
            print(f"   {rec}")
        
        overall_status = "🎉 SUCCESS" if report.overall_success else "⚠️ NEEDS ATTENTION"
        print(f"\n🏆 OVERALL STATUS: {overall_status}")
        
        if report.overall_success:
            print("\n🚀 Your Yōsai Intel Dashboard is fully functional!")
            print("   All critical features are working correctly.")
            print("   Ready for production use!")
        else:
            print("\n🔧 Some issues detected that need attention.")
            print("   Review the recommendations above.")
            print("   Fix critical issues before deployment.")

    def run_all_tests(self) -> FunctionalTestReport:
        """Run all functional tests and generate comprehensive report."""
        print("🚀 STARTING COMPREHENSIVE FUNCTIONAL TESTING")
        print("=" * 70)
        
        # Pre-flight checks
        print("\n🔍 PRE-FLIGHT CHECKS")
        print("-" * 30)
        
        # Check app availability
        app_accessible, app_status = self.check_app_availability()
        print(f"📡 App Status: {app_status}")
        
        if not app_accessible:
            print("\n❌ CRITICAL: Application is not accessible!")
            print("Start the application first:")
            print("   cd yosai_intel_dashboard_fresh")
            print("   source venv_dashboard/bin/activate")
            print("   export DB_PASSWORD='test_password'")
            print("   export SECRET_KEY='test_key'")
            print("   python3 test_app_factory.py")
            
            return self._create_failure_report("App not accessible")
        
        # Check test scripts
        scripts_exist, missing_scripts = self.check_test_scripts_exist()
        if not scripts_exist:
            print(f"❌ Missing test scripts: {missing_scripts}")
            return self._create_failure_report(f"Missing scripts: {missing_scripts}")
        
        print("✅ All pre-flight checks passed")
        
        # Run test modules
        print(f"\n🧪 EXECUTING TEST MODULES")
        print("-" * 30)
        
        module_results = []
        modules_passed = 0
        total_tests = 0
        tests_passed = 0
        
        for module_info in self.test_modules:
            result = self.run_test_module(module_info)
            module_results.append(result)
            
            if result.success:
                modules_passed += 1
            
            total_tests += result.tests_total
            tests_passed += result.tests_passed
        
        # Calculate summary
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        summary = {
            'modules_passed': modules_passed,
            'modules_failed': len(module_results) - modules_passed,
            'total_tests': total_tests,
            'tests_passed': tests_passed,
            'success_rate': (tests_passed / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Determine overall success
        critical_modules = [m for m in self.test_modules if m['critical']]
        critical_results = [r for r in module_results if any(
            cm['name'] == r.module_name for cm in critical_modules
        )]
        critical_passed = sum(1 for r in critical_results if r.success)
        overall_success = critical_passed == len(critical_results)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(module_results)
        
        # Create comprehensive report
        report = FunctionalTestReport(
            test_session_id=self.test_session_id,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_duration=total_duration,
            app_url=self.base_url,
            app_accessible=app_accessible,
            modules_executed=module_results,
            overall_success=overall_success,
            summary=summary,
            recommendations=recommendations
        )
        
        return report

    def _create_failure_report(self, reason: str) -> FunctionalTestReport:
        """Create a failure report when tests cannot run."""
        end_time = datetime.now()
        
        return FunctionalTestReport(
            test_session_id=self.test_session_id,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_duration=(end_time - self.start_time).total_seconds(),
            app_url=self.base_url,
            app_accessible=False,
            modules_executed=[],
            overall_success=False,
            summary={
                'modules_passed': 0,
                'modules_failed': 1,
                'total_tests': 1,
                'tests_passed': 0,
                'success_rate': 0
            },
            recommendations=[f"🚨 CRITICAL: {reason}"]
        )


def main():
    """Main function for master test runner."""
    # Check if custom URL provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8052"
    
    # Create master tester
    tester = MasterFunctionalTester(base_url)
    
    # Run all tests
    report = tester.run_all_tests()
    
    # Print summary
    tester.print_summary_report(report)
    
    # Save detailed report
    report_file = tester.save_detailed_report(report)
    if report_file:
        print(f"\n💾 Detailed report saved: {report_file}")
    
    # Exit with appropriate code
    sys.exit(0 if report.overall_success else 1)


if __name__ == "__main__":
    main()