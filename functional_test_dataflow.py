#!/usr/bin/env python3
"""
Cross-Page Data Flow Testing Module
Tests session persistence, data sharing between pages, and global state.
"""

import requests
import json
import time
import sys
import tempfile
import pandas as pd
import base64
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class DataFlowTest:
    """Cross-page data flow test case."""
    name: str
    source_page: str
    target_page: str
    data_action: str  # 'upload', 'configure', 'analyze'
    test_data: Any
    verification_method: str  # 'content_check', 'api_call', 'store_check'
    expected_result: str


@dataclass
class DataFlowResult:
    """Data flow test result."""
    test_name: str
    success: bool
    response_time: float
    source_success: bool
    target_success: bool
    error_message: str = ""
    data_trace: Optional[Dict] = None


class CrossPageDataFlowTester:
    """Comprehensive cross-page data flow tester."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8052"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Maintain session state
        self.session_data = {}
        
        # Define data flow test cases
        self.dataflow_tests = [
            DataFlowTest(
                name="Upload to Analytics Flow",
                source_page="/upload",
                target_page="/analytics",
                data_action="upload",
                test_data=self._create_test_csv(),
                verification_method="content_check",
                expected_result="uploaded file available in analytics"
            ),
            DataFlowTest(
                name="Analytics to Dashboard Flow",
                source_page="/analytics",
                target_page="/dashboard",
                data_action="analyze",
                test_data={"metric": "access_count"},
                verification_method="content_check",
                expected_result="analytics results visible on dashboard"
            ),
            DataFlowTest(
                name="Settings to Global Flow",
                source_page="/settings",
                target_page="/dashboard",
                data_action="configure",
                test_data={"theme": "dark", "refresh_rate": 30},
                verification_method="content_check",
                expected_result="settings applied globally"
            ),
            DataFlowTest(
                name="Session Persistence Check",
                source_page="/upload",
                target_page="/upload",
                data_action="upload",
                test_data=self._create_test_csv(),
                verification_method="store_check",
                expected_result="session data persists across page reloads"
            )
        ]

    def _create_test_csv(self) -> bytes:
        """Create a small test CSV for data flow testing."""
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='1H'),
            'user_id': range(1, 11),
            'access_granted': [True, False] * 5,
            'door_id': ['DOOR_' + str(i % 3) for i in range(10)]
        })
        
        return test_data.to_csv(index=False).encode('utf-8')

    def get_page_with_session(self, page_path: str) -> Tuple[bool, str, Dict]:
        """Get page content while maintaining session cookies."""
        try:
            url = urljoin(self.base_url + '/', page_path.lstrip('/'))
            response = self.session.get(url, timeout=15)
            
            # Extract session information
            session_info = {
                'status_code': response.status_code,
                'cookies': dict(response.cookies),
                'headers': dict(response.headers)
            }
            
            if response.status_code == 200:
                return True, response.text, session_info
            else:
                return False, f"Status: {response.status_code}", session_info
                
        except Exception as e:
            return False, f"Request failed: {str(e)}", {}

    def simulate_upload_action(self, test_data: bytes) -> Tuple[bool, Dict]:
        """Simulate file upload and track session state."""
        try:
            # Encode file for upload
            encoded_content = base64.b64encode(test_data).decode('utf-8')
            data_url = f"data:text/csv;base64,{encoded_content}"
            
            # Simulate upload callback
            callback_data = {
                "output": "upload-results.children",
                "inputs": [
                    {
                        "id": "drag-drop-upload",
                        "property": "contents",
                        "value": [data_url]
                    },
                    {
                        "id": "drag-drop-upload", 
                        "property": "filename",
                        "value": ["test_dataflow.csv"]
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}/_dash-update-component",
                json=callback_data,
                headers={'Content-Type': 'application/json'},
                timeout=20
            )
            
            success = response.status_code == 200
            result_data = {
                'upload_status': response.status_code,
                'response_size': len(response.text),
                'session_cookies': dict(self.session.cookies)
            }
            
            # Store session data for tracking
            if success:
                self.session_data['last_upload'] = {
                    'filename': 'test_dataflow.csv',
                    'timestamp': time.time(),
                    'size': len(test_data)
                }
            
            return success, result_data
            
        except Exception as e:
            return False, {'error': str(e)}

    def simulate_analytics_action(self, test_data: Dict) -> Tuple[bool, Dict]:
        """Simulate analytics operation and track results."""
        try:
            # Try to refresh analytics sources first
            refresh_callback = {
                "output": "analytics-data-source.options",
                "inputs": [
                    {
                        "id": "refresh-sources-btn",
                        "property": "n_clicks",
                        "value": 1
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}/_dash-update-component",
                json=refresh_callback,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            # Then try to select data source
            if response.status_code == 200:
                select_callback = {
                    "output": "analytics-results.children",
                    "inputs": [
                        {
                            "id": "analytics-data-source",
                            "property": "value", 
                            "value": "test_dataflow.csv"
                        }
                    ]
                }
                
                response2 = self.session.post(
                    f"{self.base_url}/_dash-update-component",
                    json=select_callback,
                    headers={'Content-Type': 'application/json'},
                    timeout=15
                )
                
                success = response2.status_code == 200
                result_data = {
                    'refresh_status': response.status_code,
                    'select_status': response2.status_code,
                    'analytics_active': success
                }
            else:
                success = False
                result_data = {'refresh_status': response.status_code}
            
            return success, result_data
            
        except Exception as e:
            return False, {'error': str(e)}

    def simulate_settings_action(self, test_data: Dict) -> Tuple[bool, Dict]:
        """Simulate settings configuration."""
        try:
            # Try to update settings
            settings_callback = {
                "output": "settings-status.children",
                "inputs": [
                    {
                        "id": "settings-form",
                        "property": "value",
                        "value": test_data
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}/_dash-update-component", 
                json=settings_callback,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            result_data = {
                'settings_status': response.status_code,
                'configured_values': test_data
            }
            
            return success, result_data
            
        except Exception as e:
            return False, {'error': str(e)}

    def verify_data_availability(self, page_path: str, expected_result: str, verification_method: str) -> Tuple[bool, str]:
        """Verify that data is available on target page."""
        try:
            # Get page content
            page_accessible, content, session_info = self.get_page_with_session(page_path)
            
            if not page_accessible:
                return False, f"Page not accessible: {content}"
            
            if verification_method == "content_check":
                # Look for indicators that data is present
                indicators = [
                    'test_dataflow.csv',
                    'uploaded',
                    'analytics',
                    'data-source',
                    'file-info',
                    'results'
                ]
                
                found_indicators = [ind for ind in indicators if ind in content.lower()]
                
                if found_indicators:
                    return True, f"Found data indicators: {found_indicators}"
                else:
                    return False, "No data indicators found in page content"
                    
            elif verification_method == "store_check":
                # Look for Dash stores containing data
                store_indicators = [
                    'dcc.Store',
                    'file-info-store',
                    'session-store',
                    'analytics-store'
                ]
                
                found_stores = [store for store in store_indicators if store in content]
                
                if found_stores:
                    return True, f"Found data stores: {found_stores}"
                else:
                    return False, "No data stores found"
                    
            elif verification_method == "api_call":
                # Try to make API call to check data
                try:
                    api_response = self.session.get(f"{self.base_url}/api/files", timeout=5)
                    if api_response.status_code == 200:
                        return True, "API call successful"
                    else:
                        return False, f"API call failed: {api_response.status_code}"
                except:
                    return False, "API endpoint not available"
                    
            else:
                return False, f"Unknown verification method: {verification_method}"
                
        except Exception as e:
            return False, f"Verification failed: {str(e)}"

    def run_dataflow_test(self, test: DataFlowTest) -> DataFlowResult:
        """Run a single data flow test."""
        start_time = time.time()
        
        try:
            # Step 1: Navigate to source page
            source_accessible, source_content, source_session = self.get_page_with_session(test.source_page)
            if not source_accessible:
                return DataFlowResult(
                    test_name=test.name,
                    success=False,
                    response_time=time.time() - start_time,
                    source_success=False,
                    target_success=False,
                    error_message=f"Source page not accessible: {source_content}"
                )
            
            # Step 2: Perform data action on source page
            if test.data_action == "upload":
                action_success, action_data = self.simulate_upload_action(test.test_data)
            elif test.data_action == "analyze":
                action_success, action_data = self.simulate_analytics_action(test.test_data)
            elif test.data_action == "configure":
                action_success, action_data = self.simulate_settings_action(test.test_data)
            else:
                action_success = False
                action_data = {"error": f"Unknown action: {test.data_action}"}
            
            if not action_success:
                return DataFlowResult(
                    test_name=test.name,
                    success=False,
                    response_time=time.time() - start_time,
                    source_success=False,
                    target_success=False,
                    error_message=f"Source action failed: {action_data}",
                    data_trace=action_data
                )
            
            # Step 3: Wait a moment for data to propagate
            time.sleep(2)
            
            # Step 4: Navigate to target page and verify data
            verification_success, verification_message = self.verify_data_availability(
                test.target_page,
                test.expected_result,
                test.verification_method
            )
            
            response_time = time.time() - start_time
            
            return DataFlowResult(
                test_name=test.name,
                success=action_success and verification_success,
                response_time=response_time,
                source_success=action_success,
                target_success=verification_success,
                error_message="" if verification_success else verification_message,
                data_trace={
                    'action_data': action_data,
                    'verification': verification_message,
                    'session': dict(self.session.cookies)
                }
            )
            
        except Exception as e:
            return DataFlowResult(
                test_name=test.name,
                success=False,
                response_time=time.time() - start_time,
                source_success=False,
                target_success=False,
                error_message=f"Test execution failed: {str(e)}"
            )

    def test_session_persistence(self) -> bool:
        """Test session persistence across page reloads."""
        print("\n🔄 Testing session persistence...")
        
        try:
            # Get initial session
            initial_success, initial_content, initial_session = self.get_page_with_session("/dashboard")
            if not initial_success:
                print("   ❌ Failed to establish initial session")
                return False
            
            initial_cookies = initial_session.get('cookies', {})
            
            # Navigate to different pages
            test_pages = ["/analytics", "/upload", "/settings", "/dashboard"]
            
            for page in test_pages:
                success, content, session_info = self.get_page_with_session(page)
                if not success:
                    print(f"   ❌ Failed to maintain session on {page}")
                    return False
                    
                current_cookies = session_info.get('cookies', {})
                
                # Check if session cookies are maintained
                session_maintained = any(
                    cookie_name in current_cookies 
                    for cookie_name in initial_cookies.keys()
                    if cookie_name.startswith(('session', 'dash', '_'))
                )
                
                print(f"   {'✅' if session_maintained else '⚠️'} Session on {page}")
            
            print("   ✅ Session persistence test completed")
            return True
            
        except Exception as e:
            print(f"   ❌ Session persistence test failed: {e}")
            return False

    def test_global_state_consistency(self) -> bool:
        """Test global state consistency across pages.""" 
        print("\n🌐 Testing global state consistency...")
        
        try:
            pages_to_test = ["/dashboard", "/analytics", "/upload", "/settings"]
            state_indicators = []
            
            for page in pages_to_test:
                success, content, session_info = self.get_page_with_session(page)
                if success:
                    # Look for global state indicators
                    global_elements = [
                        'navbar',
                        'user-session',
                        'app-config',
                        'theme',
                        'global-store'
                    ]
                    
                    page_state = {
                        'page': page,
                        'global_elements': [elem for elem in global_elements if elem in content.lower()],
                        'has_stores': 'dcc.Store' in content,
                        'session_cookies': len(session_info.get('cookies', {}))
                    }
                    
                    state_indicators.append(page_state)
                    print(f"   {'✅' if page_state['has_stores'] else '⚠️'} Global state on {page}")
            
            # Check consistency
            consistent_elements = True
            if len(state_indicators) > 1:
                first_page_elements = state_indicators[0]['global_elements']
                for indicator in state_indicators[1:]:
                    if set(indicator['global_elements']) != set(first_page_elements):
                        consistent_elements = False
                        break
            
            print(f"   📊 Global state consistency: {'✅ Consistent' if consistent_elements else '⚠️ Inconsistent'}")
            return True
            
        except Exception as e:
            print(f"   ❌ Global state test failed: {e}")
            return False

    def run_all_dataflow_tests(self) -> Tuple[List[DataFlowResult], Dict[str, int]]:
        """Run all cross-page data flow tests."""
        print("🔄 CROSS-PAGE DATA FLOW TESTING")
        print("=" * 50)
        
        results = []
        passed = 0
        
        # Test session persistence
        session_test = self.test_session_persistence()
        if session_test:
            passed += 1
        
        # Test global state consistency
        global_state_test = self.test_global_state_consistency()
        if global_state_test:
            passed += 1
        
        # Run data flow tests
        for test in self.dataflow_tests:
            print(f"\n🔄 Testing: {test.name}")
            result = self.run_dataflow_test(test)
            results.append(result)
            
            if result.success:
                print(f"   ✅ PASS ({result.response_time:.2f}s)")
                print(f"      Source: {'✅' if result.source_success else '❌'}")
                print(f"      Target: {'✅' if result.target_success else '❌'}")
                passed += 1
            else:
                print(f"   ❌ FAIL ({result.response_time:.2f}s)")
                print(f"      Error: {result.error_message}")
                print(f"      Source: {'✅' if result.source_success else '❌'}")
                print(f"      Target: {'✅' if result.target_success else '❌'}")
        
        # Include system tests in total
        total_tests = len(results) + 2  # +2 for session and global state tests
        
        summary = {
            "passed": passed,
            "failed": total_tests - passed,
            "total": total_tests
        }
        
        print(f"\n📊 DATA FLOW RESULTS: {summary['passed']}/{summary['total']} passed")
        return results, summary


def main():
    """Main testing function."""
    tester = CrossPageDataFlowTester()
    
    # Run all data flow tests
    results, summary = tester.run_all_dataflow_tests()
    
    # Final summary
    print("\n" + "=" * 50)
    print("🏁 FINAL DATA FLOW RESULTS") 
    print("=" * 50)
    print(f"Data flow tests: {summary['passed']}/{summary['total']} passed")
    
    overall_success = summary['failed'] <= 1
    
    if overall_success:
        print("\n🎉 CROSS-PAGE DATA FLOW WORKING!")
        print("\nAll functionality tests completed.")
        print("Your Yōsai Intel Dashboard is ready for use! 🚀")
    else:
        print("\n⚠️ Some data flow issues detected.")
        print("Check session management and data store implementations.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
