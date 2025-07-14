#!/usr/bin/env python3
"""
Upload Functionality Testing Module
Tests file upload, drag-drop interface, and error handling.
"""

import requests
import tempfile
import pandas as pd
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import base64
import io


@dataclass
class UploadTestFile:
    """Test file for upload testing."""
    name: str
    content: bytes
    mime_type: str
    should_pass: bool
    expected_error: Optional[str] = None


@dataclass
class UploadTestResult:
    """Upload test result."""
    test_name: str
    success: bool
    response_time: float
    status_code: Optional[int] = None
    error_message: str = ""
    response_data: Optional[Dict] = None


class UploadFunctionalityTester:
    """Comprehensive upload functionality tester."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8052"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_files_dir = Path.cwd() / "test_upload_files"
        
    def setup_test_files(self) -> Dict[str, UploadTestFile]:
        """Create test files for upload testing."""
        print("📁 Creating test files...")
        
        self.test_files_dir.mkdir(exist_ok=True)
        
        # Create valid CSV file
        valid_csv_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=50, freq='1H'),
            'user_id': range(1, 51),
            'access_granted': [True, False] * 25,
            'door_id': ['DOOR_' + str(i % 5) for i in range(50)],
            'facility': ['Building_A', 'Building_B'] * 25
        })
        
        csv_buffer = io.StringIO()
        valid_csv_data.to_csv(csv_buffer, index=False)
        valid_csv_bytes = csv_buffer.getvalue().encode('utf-8')
        
        # Create valid JSON file
        valid_json_data = {
            'events': [
                {
                    'timestamp': '2024-01-01T10:00:00Z',
                    'user_id': 123,
                    'event_type': 'access_granted',
                    'location': 'main_entrance'
                },
                {
                    'timestamp': '2024-01-01T10:05:00Z', 
                    'user_id': 456,
                    'event_type': 'access_denied',
                    'location': 'server_room'
                }
            ]
        }
        valid_json_bytes = json.dumps(valid_json_data, indent=2).encode('utf-8')
        
        # Create invalid files
        invalid_csv_bytes = b"invalid,csv,format\nno,matching,headers\n"
        large_file_bytes = b"x" * (60 * 1024 * 1024)  # 60MB file
        
        # Unicode test file
        unicode_test_data = pd.DataFrame({
            'name': ['User1', 'User2', 'Test🚀'],
            'location': ['Building A', 'Building B', 'Café'],
            'notes': ['Normal text', 'Special chars: àáâãäå', 'Emoji test: 🔒🚪']
        })
        unicode_buffer = io.StringIO()
        unicode_test_data.to_csv(unicode_buffer, index=False)
        unicode_bytes = unicode_buffer.getvalue().encode('utf-8', errors='replace')
        
        test_files = {
            'valid_csv': UploadTestFile(
                name="valid_data.csv",
                content=valid_csv_bytes,
                mime_type="text/csv",
                should_pass=True
            ),
            'valid_json': UploadTestFile(
                name="valid_data.json", 
                content=valid_json_bytes,
                mime_type="application/json",
                should_pass=True
            ),
            'unicode_csv': UploadTestFile(
                name="unicode_test.csv",
                content=unicode_bytes,
                mime_type="text/csv", 
                should_pass=True
            ),
            'invalid_csv': UploadTestFile(
                name="invalid.csv",
                content=invalid_csv_bytes,
                mime_type="text/csv",
                should_pass=False,
                expected_error="validation"
            ),
            'large_file': UploadTestFile(
                name="large_file.csv",
                content=large_file_bytes,
                mime_type="text/csv",
                should_pass=False,
                expected_error="size limit"
            ),
            'wrong_extension': UploadTestFile(
                name="data.txt",
                content=valid_csv_bytes,
                mime_type="text/plain",
                should_pass=False,
                expected_error="file type"
            )
        }
        
        print(f"   ✅ Created {len(test_files)} test files")
        return test_files

    def test_upload_page_availability(self) -> bool:
        """Test if upload page is accessible."""
        try:
            response = self.session.get(f"{self.base_url}/upload")
            if response.status_code != 200:
                print(f"❌ Upload page not accessible: {response.status_code}")
                return False
                
            content = response.text.lower()
            required_elements = ['drag-drop-upload', 'upload', 'file']
            
            missing = [elem for elem in required_elements if elem not in content]
            if missing:
                print(f"❌ Upload page missing elements: {missing}")
                return False
                
            print("✅ Upload page accessible and contains required elements")
            return True
            
        except Exception as e:
            print(f"❌ Failed to access upload page: {e}")
            return False

    def simulate_file_upload(self, test_file: UploadTestFile) -> UploadTestResult:
        """Simulate file upload via HTTP POST."""
        start_time = time.time()
        
        try:
            # Encode file as base64 (like Dash does)
            encoded_content = base64.b64encode(test_file.content).decode('utf-8')
            data_url = f"data:{test_file.mime_type};base64,{encoded_content}"
            
            # Simulate Dash callback payload
            callback_data = {
                'inputs': [
                    {
                        'id': 'drag-drop-upload',
                        'property': 'contents',
                        'value': [data_url]
                    },
                    {
                        'id': 'drag-drop-upload',
                        'property': 'filename', 
                        'value': [test_file.name]
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}/_dash-update-component",
                json=callback_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response_time = time.time() - start_time
            success = self._evaluate_upload_response(response, test_file)
            
            return UploadTestResult(
                test_name=test_file.name,
                success=success,
                response_time=response_time,
                status_code=response.status_code,
                response_data=self._safe_json_parse(response.text)
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return UploadTestResult(
                test_name=test_file.name,
                success=False,
                response_time=response_time,
                error_message=f"Upload simulation failed: {str(e)}"
            )

    def _evaluate_upload_response(self, response: requests.Response, test_file: UploadTestFile) -> bool:
        """Evaluate if upload response matches expectations."""
        if test_file.should_pass:
            # Should succeed
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"   Expected success but got status {response.status_code}")
                return False
        else:
            # Should fail
            if response.status_code in [400, 413, 422]:
                return True
            elif response.status_code == 200:
                # Check response content for error indicators
                content = response.text.lower()
                error_indicators = ['error', 'failed', 'invalid', 'rejected']
                return any(indicator in content for indicator in error_indicators)
            else:
                print(f"   Expected failure but got unexpected status {response.status_code}")
                return False

    def _safe_json_parse(self, text: str) -> Optional[Dict]:
        """Safely parse JSON response."""
        try:
            return json.loads(text)
        except:
            return None

    def test_upload_interface_elements(self) -> bool:
        """Test upload interface has required elements."""
        try:
            response = self.session.get(f"{self.base_url}/upload")
            content = response.text
            
            required_elements = [
                'drag-drop-upload',
                'upload-button',
                'file-preview',
                'upload-progress'
            ]
            
            found_elements = []
            missing_elements = []
            
            for element in required_elements:
                if element in content or element.replace('-', '_') in content:
                    found_elements.append(element)
                else:
                    missing_elements.append(element)
            
            print(f"   Found UI elements: {found_elements}")
            if missing_elements:
                print(f"   Missing UI elements: {missing_elements}")
                
            return len(missing_elements) <= 1  # Allow 1 missing element
            
        except Exception as e:
            print(f"   ❌ Failed to test UI elements: {e}")
            return False

    def run_all_upload_tests(self) -> Tuple[List[UploadTestResult], Dict[str, int]]:
        """Run all upload tests."""
        print("📤 UPLOAD FUNCTIONALITY TESTING")
        print("=" * 50)
        
        # Test upload page availability
        if not self.test_upload_page_availability():
            return [], {"passed": 0, "failed": 1, "total": 1}
        
        # Test UI elements
        ui_test_passed = self.test_upload_interface_elements()
        print(f"🎨 Upload UI Elements: {'✅ PASS' if ui_test_passed else '⚠️ PARTIAL'}")
        
        # Create test files
        test_files = self.setup_test_files()
        
        # Run upload tests
        results = []
        passed = 0
        
        for file_key, test_file in test_files.items():
            print(f"\n📁 Testing: {test_file.name}")
            result = self.simulate_file_upload(test_file)
            results.append(result)
            
            if result.success:
                print(f"   ✅ PASS ({result.response_time:.2f}s)")
                if test_file.should_pass:
                    print("      File uploaded successfully")
                else:
                    print("      File correctly rejected")
                passed += 1
            else:
                print(f"   ❌ FAIL ({result.response_time:.2f}s)")
                print(f"      Error: {result.error_message}")
                if result.status_code:
                    print(f"      Status: {result.status_code}")
        
        # Include UI test in summary
        if ui_test_passed:
            passed += 1
        total_tests = len(results) + 1
        
        summary = {
            "passed": passed,
            "failed": total_tests - passed,
            "total": total_tests
        }
        
        print(f"\n📊 UPLOAD RESULTS: {summary['passed']}/{summary['total']} passed")
        return results, summary

    def cleanup_test_files(self):
        """Clean up created test files."""
        try:
            if self.test_files_dir.exists():
                import shutil
                shutil.rmtree(self.test_files_dir)
                print("🧹 Cleaned up test files")
        except Exception as e:
            print(f"⚠️ Failed to cleanup test files: {e}")


def main():
    """Main testing function."""
    tester = UploadFunctionalityTester()
    
    try:
        # Run all upload tests
        results, summary = tester.run_all_upload_tests()
        
        # Final summary
        print("\n" + "=" * 50)
        print("🏁 FINAL UPLOAD RESULTS")
        print("=" * 50)
        print(f"Upload tests: {summary['passed']}/{summary['total']} passed")
        
        overall_success = summary['failed'] == 0
        
        if overall_success:
            print("\n🎉 ALL UPLOAD TESTS PASSED!")
            print("\nNext: Run interactive features testing")
            print("   python3 functional_test_interactive.py")
        else:
            print("\n⚠️ Some upload tests failed.")
            print("Check upload functionality and file validation.")
        
        return overall_success
        
    finally:
        tester.cleanup_test_files()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
