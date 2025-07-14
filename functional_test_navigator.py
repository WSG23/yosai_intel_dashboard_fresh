#!/usr/bin/env python3
"""
Navigation Flow Testing Module
Tests all navbar links and page routing functionality.
"""

import requests
import time
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class NavigationTest:
    """Single navigation test case."""
    name: str
    path: str
    expected_content: List[str]
    expected_status: int = 200
    timeout: float = 5.0


@dataclass
class TestResult:
    """Test execution result."""
    test_name: str
    success: bool
    status_code: Optional[int]
    response_time: float
    error_message: str = ""
    found_content: List[str] = None


class NavigationTester:
    """Comprehensive navigation flow tester."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8052"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 10
        
        # Define navigation test cases
        self.navigation_tests = [
            NavigationTest(
                name="Dashboard Page",
                path="/dashboard",
                expected_content=["Dashboard", "Yōsai Intel"]
            ),
            NavigationTest(
                name="Analytics Page", 
                path="/analytics",
                expected_content=["Analytics", "data-source"]
            ),
            NavigationTest(
                name="Graphs Page",
                path="/graphs", 
                expected_content=["Graphs", "visualization"]
            ),
            NavigationTest(
                name="Upload Page",
                path="/upload",
                expected_content=["Upload", "drag-drop-upload", "file"]
            ),
            NavigationTest(
                name="Export Page",
                path="/export",
                expected_content=["Export", "download"]
            ),
            NavigationTest(
                name="Settings Page",
                path="/settings",
                expected_content=["Settings", "configuration"]
            ),
            NavigationTest(
                name="Root Redirect",
                path="/",
                expected_content=["Dashboard", "Analytics"],
                expected_status=200
            )
        ]

    def test_server_availability(self) -> bool:
        """Test if server is running and responsive."""
        try:
            response = self.session.get(self.base_url, timeout=5)
            return response.status_code in [200, 302, 404]
        except Exception as e:
            print(f"❌ Server not available: {e}")
            return False

    def run_navigation_test(self, test: NavigationTest) -> TestResult:
        """Run a single navigation test."""
        start_time = time.time()
        
        try:
            url = urljoin(self.base_url + '/', test.path.lstrip('/'))
            response = self.session.get(url, timeout=test.timeout)
            response_time = time.time() - start_time
            
            # Check status code
            if response.status_code != test.expected_status:
                return TestResult(
                    test_name=test.name,
                    success=False,
                    status_code=response.status_code,
                    response_time=response_time,
                    error_message=f"Expected status {test.expected_status}, got {response.status_code}"
                )
            
            # Check content
            content = response.text.lower()
            found_content = []
            missing_content = []
            
            for expected in test.expected_content:
                if expected.lower() in content:
                    found_content.append(expected)
                else:
                    missing_content.append(expected)
            
            success = len(missing_content) == 0
            error_msg = f"Missing content: {missing_content}" if missing_content else ""
            
            return TestResult(
                test_name=test.name,
                success=success,
                status_code=response.status_code,
                response_time=response_time,
                error_message=error_msg,
                found_content=found_content
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                test_name=test.name,
                success=False,
                status_code=None,
                response_time=response_time,
                error_message=f"Request failed: {str(e)}"
            )

    def run_all_tests(self) -> Tuple[List[TestResult], Dict[str, int]]:
        """Run all navigation tests and return results summary."""
        print("🧭 NAVIGATION FLOW TESTING")
        print("=" * 50)
        
        if not self.test_server_availability():
            print("❌ Server is not available. Start the app first:")
            print("   python3 test_app_factory.py")
            return [], {"passed": 0, "failed": 1, "total": 1}
        
        results = []
        passed = 0
        
        for test in self.navigation_tests:
            print(f"\n🔍 Testing: {test.name}")
            result = self.run_navigation_test(test)
            results.append(result)
            
            if result.success:
                print(f"   ✅ PASS ({result.response_time:.2f}s)")
                if result.found_content:
                    print(f"      Found: {', '.join(result.found_content)}")
                passed += 1
            else:
                print(f"   ❌ FAIL ({result.response_time:.2f}s)")
                print(f"      Error: {result.error_message}")
                if result.status_code:
                    print(f"      Status: {result.status_code}")
        
        summary = {
            "passed": passed,
            "failed": len(results) - passed,
            "total": len(results)
        }
        
        print(f"\n📊 NAVIGATION RESULTS: {summary['passed']}/{summary['total']} passed")
        return results, summary

    def test_cross_page_navigation(self) -> bool:
        """Test navigation flow between pages."""
        print("\n🔄 Testing cross-page navigation...")
        
        try:
            # Test navigation sequence
            paths = ["/dashboard", "/analytics", "/upload", "/settings", "/dashboard"]
            
            for i, path in enumerate(paths):
                url = urljoin(self.base_url + '/', path.lstrip('/'))
                response = self.session.get(url, timeout=5)
                
                if response.status_code != 200:
                    print(f"   ❌ Failed at step {i+1}: {path} (status: {response.status_code})")
                    return False
                    
                print(f"   ✅ Step {i+1}: {path}")
                time.sleep(0.5)  # Small delay between requests
            
            print("   🎉 Cross-page navigation successful!")
            return True
            
        except Exception as e:
            print(f"   ❌ Cross-page navigation failed: {e}")
            return False


def main():
    """Main testing function."""
    tester = NavigationTester()
    
    # Run all navigation tests
    results, summary = tester.run_all_tests()
    
    # Test cross-page navigation
    cross_nav_success = tester.test_cross_page_navigation()
    
    # Final summary
    print("\n" + "=" * 50)
    print("🏁 FINAL NAVIGATION RESULTS")
    print("=" * 50)
    print(f"Individual tests: {summary['passed']}/{summary['total']} passed")
    print(f"Cross-page navigation: {'✅ PASS' if cross_nav_success else '❌ FAIL'}")
    
    overall_success = summary['failed'] == 0 and cross_nav_success
    
    if overall_success:
        print("\n🎉 ALL NAVIGATION TESTS PASSED!")
        print("\nNext: Run upload functionality testing")
        print("   python3 functional_test_upload.py")
    else:
        print("\n⚠️ Some navigation tests failed.")
        print("Check the app is running and all pages are loading correctly.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
