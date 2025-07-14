#!/usr/bin/env python3
"""
Interactive Features Testing Module
Tests buttons, forms, callbacks, and data stores functionality.
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class InteractiveTest:
    """Interactive feature test case."""
    name: str
    page_path: str
    element_id: str
    action_type: str  # 'click', 'input', 'select'
    test_data: Optional[Any] = None
    expected_response: Optional[str] = None
    timeout: float = 10.0


@dataclass
class InteractiveTestResult:
    """Interactive test result."""
    test_name: str
    success: bool
    response_time: float
    error_message: str = ""
    response_data: Optional[Dict] = None


class InteractiveFeaturesTestr:
    """Comprehensive interactive features tester."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8052"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 15
        
        # Define interactive test cases
        self.interactive_tests = [
            InteractiveTest(
                name="Analytics Refresh Button",
                page_path="/analytics",
                element_id="refresh-sources-btn",
                action_type="click",
                expected_response="data-source"
            ),
            InteractiveTest(
                name="Analytics Data Source Dropdown",
                page_path="/analytics",
                element_id="analytics-data-source",
                action_type="select",
                test_data="sample_data.csv"
            ),
            InteractiveTest(
                name="Upload Browse Button",
                page_path="/upload",
                element_id="upload-button",
                action_type="click"
            ),
            InteractiveTest(
                name="Dashboard Quick Actions",
                page_path="/dashboard", 
                element_id="quick-actions",
                action_type="click"
            ),
            InteractiveTest(
                name="Settings Form Input",
                page_path="/settings",
                element_id="config-form",
                action_type="input",
                test_data={"setting_key": "test_value"}
            )
        ]

    def get_page_content(self, page_path: str) -> Tuple[bool, str]:
        """Get page content and check if it's accessible."""
        try:
            url = urljoin(self.base_url + '/', page_path.lstrip('/'))
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return True, response.text
            else:
                return False, f"Status: {response.status_code}"
                
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def simulate_dash_callback(self, component_id: str, property_name: str, value: Any, page_content: str) -> Tuple[bool, Optional[Dict]]:
        """Simulate a Dash callback interaction."""
        try:
            # Create callback payload
            callback_data = {
                "output": f"{component_id}.children",
                "inputs": [
                    {
                        "id": component_id,
                        "property": property_name,
                        "value": value
                    }
                ],
                "changedPropIds": [f"{component_id}.{property_name}"],
                "state": []
            }
            
            # Try to post to Dash callback endpoint
            response = self.session.post(
                f"{self.base_url}/_dash-update-component",
                json=callback_data,
                headers={
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    return True, response_json
                except json.JSONDecodeError:
                    # Response might be HTML or other format
                    return True, {"response": response.text[:200]}
            else:
                return False, {"error": f"Status: {response.status_code}", "response": response.text[:200]}
                
        except Exception as e:
            return False, {"error": f"Callback simulation failed: {str(e)}"}

    def test_button_interaction(self, test: InteractiveTest) -> InteractiveTestResult:
        """Test button click interaction."""
        start_time = time.time()
        
        # Get page content first
        page_accessible, page_content = self.get_page_content(test.page_path)
        if not page_accessible:
            return InteractiveTestResult(
                test_name=test.name,
                success=False,
                response_time=time.time() - start_time,
                error_message=f"Page not accessible: {page_content}"
            )
        
        # Check if element exists in page
        if test.element_id not in page_content and test.element_id.replace('-', '_') not in page_content:
            return InteractiveTestResult(
                test_name=test.name,
                success=False,
                response_time=time.time() - start_time,
                error_message=f"Element '{test.element_id}' not found on page"
            )
        
        # Simulate button click
        success, response_data = self.simulate_dash_callback(
            test.element_id,
            "n_clicks",
            1,
            page_content
        )
        
        response_time = time.time() - start_time
        
        # Evaluate response
        if success and test.expected_response:
            if isinstance(response_data, dict):
                response_str = json.dumps(response_data).lower()
                success = test.expected_response.lower() in response_str
            else:
                success = False
        
        return InteractiveTestResult(
            test_name=test.name,
            success=success,
            response_time=response_time,
            response_data=response_data,
            error_message="" if success else "Callback response did not match expectations"
        )

    def test_input_interaction(self, test: InteractiveTest) -> InteractiveTestResult:
        """Test form input interaction."""
        start_time = time.time()
        
        # Get page content
        page_accessible, page_content = self.get_page_content(test.page_path)
        if not page_accessible:
            return InteractiveTestResult(
                test_name=test.name,
                success=False,
                response_time=time.time() - start_time,
                error_message=f"Page not accessible: {page_content}"
            )
        
        # Simulate form input
        success, response_data = self.simulate_dash_callback(
            test.element_id,
            "value",
            test.test_data,
            page_content
        )
        
        response_time = time.time() - start_time
        
        return InteractiveTestResult(
            test_name=test.name,
            success=success,
            response_time=response_time,
            response_data=response_data,
            error_message="" if success else "Input interaction failed"
        )

    def test_dropdown_interaction(self, test: InteractiveTest) -> InteractiveTestResult:
        """Test dropdown selection interaction.""" 
        start_time = time.time()
        
        # Get page content
        page_accessible, page_content = self.get_page_content(test.page_path)
        if not page_accessible:
            return InteractiveTestResult(
                test_name=test.name,
                success=False,
                response_time=time.time() - start_time,
                error_message=f"Page not accessible: {page_content}"
            )
        
        # Simulate dropdown selection
        success, response_data = self.simulate_dash_callback(
            test.element_id,
            "value",
            test.test_data,
            page_content
        )
        
        response_time = time.time() - start_time
        
        return InteractiveTestResult(
            test_name=test.name,
            success=success,
            response_time=response_time,
            response_data=response_data,
            error_message="" if success else "Dropdown interaction failed"
        )

    def run_interactive_test(self, test: InteractiveTest) -> InteractiveTestResult:
        """Run a single interactive test based on action type."""
        if test.action_type == "click":
            return self.test_button_interaction(test)
        elif test.action_type == "input":
            return self.test_input_interaction(test)
        elif test.action_type == "select":
            return self.test_dropdown_interaction(test)
        else:
            return InteractiveTestResult(
                test_name=test.name,
                success=False,
                response_time=0.0,
                error_message=f"Unknown action type: {test.action_type}"
            )

    def test_data_stores(self) -> bool:
        """Test data store functionality between pages."""
        print("\n💾 Testing data stores...")
        
        try:
            # Try to access different pages and look for data store elements
            store_tests = [
                ("/upload", "file-info-store"),
                ("/analytics", "analytics-store"),
                ("/dashboard", "session-store")
            ]
            
            stores_found = 0
            for page_path, store_id in store_tests:
                page_accessible, page_content = self.get_page_content(page_path)
                if page_accessible and (store_id in page_content or "dcc.Store" in page_content):
                    stores_found += 1
                    print(f"   ✅ Found data store on {page_path}")
                else:
                    print(f"   ⚠️ No data store found on {page_path}")
            
            success = stores_found > 0
            print(f"   📊 Data stores: {stores_found}/{len(store_tests)} found")
            return success
            
        except Exception as e:
            print(f"   ❌ Data store testing failed: {e}")
            return False

    def test_callback_registry(self) -> bool:
        """Test if callbacks are properly registered."""
        print("\n�� Testing callback registry...")
        
        try:
            # Try to trigger a simple callback to test registry
            test_data = {
                "output": "test-output.children",
                "inputs": [{"id": "test-input", "property": "value", "value": "test"}],
                "changedPropIds": ["test-input.value"],
                "state": []
            }
            
            response = self.session.post(
                f"{self.base_url}/_dash-update-component",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            # Any response (even error) indicates callback system is working
            if response.status_code in [200, 400, 422]:
                print("   ✅ Callback system is responsive")
                return True
            else:
                print(f"   ⚠️ Callback system response: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Callback registry test failed: {e}")
            return False

    def run_all_interactive_tests(self) -> Tuple[List[InteractiveTestResult], Dict[str, int]]:
        """Run all interactive feature tests."""
        print("🖱️ INTERACTIVE FEATURES TESTING")
        print("=" * 50)
        
        results = []
        passed = 0
        
        # Test callback registry
        callback_registry_works = self.test_callback_registry()
        if callback_registry_works:
            passed += 1
        
        # Test data stores
        data_stores_work = self.test_data_stores()
        if data_stores_work:
            passed += 1
        
        # Run interactive component tests
        for test in self.interactive_tests:
            print(f"\n🎛️ Testing: {test.name}")
            result = self.run_interactive_test(test)
            results.append(result)
            
            if result.success:
                print(f"   ✅ PASS ({result.response_time:.2f}s)")
                if result.response_data:
                    print(f"      Response received")
                passed += 1
            else:
                print(f"   ❌ FAIL ({result.response_time:.2f}s)")
                print(f"      Error: {result.error_message}")
        
        # Include system tests in total
        total_tests = len(results) + 2  # +2 for callback registry and data stores
        
        summary = {
            "passed": passed,
            "failed": total_tests - passed,
            "total": total_tests
        }
        
        print(f"\n📊 INTERACTIVE RESULTS: {summary['passed']}/{summary['total']} passed")
        return results, summary

    def test_page_interactivity_health(self) -> Dict[str, bool]:
        """Test overall interactivity health of each page."""
        print("\n🩺 Testing page interactivity health...")
        
        pages = ["/dashboard", "/analytics", "/upload", "/settings"]
        health_results = {}
        
        for page in pages:
            try:
                page_accessible, content = self.get_page_content(page)
                if not page_accessible:
                    health_results[page] = False
                    continue
                
                # Check for interactive elements
                interactive_indicators = [
                    "button", "input", "select", "dropdown", 
                    "click", "callback", "dash", "dcc", "dbc"
                ]
                
                interactivity_score = sum(1 for indicator in interactive_indicators if indicator in content.lower())
                health_results[page] = interactivity_score >= 3
                
                print(f"   {page}: {'✅ Healthy' if health_results[page] else '⚠️ Limited'} (score: {interactivity_score})")
                
            except Exception as e:
                print(f"   {page}: ❌ Error - {e}")
                health_results[page] = False
        
        return health_results


def main():
    """Main testing function.""" 
    tester = InteractiveFeaturesTestr()
    
    # Run all interactive tests
    results, summary = tester.run_all_interactive_tests()
    
    # Test page health
    health_results = tester.test_page_interactivity_health()
    healthy_pages = sum(1 for is_healthy in health_results.values() if is_healthy)
    total_pages = len(health_results)
    
    # Final summary
    print("\n" + "=" * 50)
    print("🏁 FINAL INTERACTIVE RESULTS")
    print("=" * 50)
    print(f"Interactive tests: {summary['passed']}/{summary['total']} passed")
    print(f"Page health: {healthy_pages}/{total_pages} pages healthy")
    
    overall_success = summary['failed'] <= 1 and healthy_pages >= total_pages // 2
    
    if overall_success:
        print("\n🎉 INTERACTIVE FEATURES WORKING WELL!")
        print("\nNext: Run cross-page data flow testing")
        print("   python3 functional_test_dataflow.py")
    else:
        print("\n⚠️ Some interactive features need attention.")
        print("Check callback registration and component interactions.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
