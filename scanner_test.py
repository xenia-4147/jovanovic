#!/usr/bin/env python3
"""
Business Card Scanner Workflow Test - CRITICAL FIX VALIDATION
Tests the complete scanner workflow with corrected API configuration
"""

import requests
import json
import uuid
from datetime import datetime
import base64

# Use the external URL for testing
BACKEND_URL = "https://netlink-3.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class ScannerWorkflowTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message="", response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response"] = response_data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()
    
    def test_api_connectivity(self):
        """Test 1: API Connectivity - Verify frontend can reach backend APIs"""
        try:
            response = requests.get(f"{API_BASE}/")
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "version" in data and "status" in data:
                    self.log_result("API Connectivity Test", True, f"Backend API accessible - {data['message']} v{data['version']}")
                    return True
                else:
                    self.log_result("API Connectivity Test", False, "Missing required fields in response", data)
                    return False
            else:
                self.log_result("API Connectivity Test", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("API Connectivity Test", False, f"Connection error: {str(e)}")
            return False
    
    def test_authentication_setup(self):
        """Setup authentication for testing"""
        try:
            # Register a test user
            test_email = f"scanner_test_{uuid.uuid4().hex[:8]}@example.com"
            
            user_data = {
                "email": test_email,
                "password": "ScannerTest123!",
                "first_name": "Scanner",
                "last_name": "Tester",
                "gdpr_consent": True,
                "privacy_consent": True,
                "marketing_consent": False
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.log_result("Authentication Setup", True, f"Test user registered: {test_email}")
                return True
            else:
                self.log_result("Authentication Setup", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Error: {str(e)}")
            return False
    
    def test_get_cards_endpoint(self):
        """Test 2: GET /api/cards endpoint accessibility"""
        if not self.access_token:
            self.log_result("GET Cards Endpoint", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/cards", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("GET Cards Endpoint", True, f"Cards endpoint accessible - returned {len(data)} cards")
                    return True
                else:
                    self.log_result("GET Cards Endpoint", False, "Response is not a list", data)
                    return False
            else:
                self.log_result("GET Cards Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("GET Cards Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_create_business_card(self):
        """Create a business card for scanner testing"""
        if not self.access_token:
            self.log_result("Create Test Business Card", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            card_data = {
                "name": "Dr. Maria Schmidt",
                "company": "Innovation Labs GmbH",
                "position": "Chief Technology Officer",
                "description": "Leading digital transformation and AI initiatives in healthcare",
                "phones": [
                    {
                        "label": "work",
                        "number": "+49-30-555-7890",
                        "is_primary": True
                    },
                    {
                        "label": "mobile",
                        "number": "+49-172-555-7890",
                        "is_primary": False
                    }
                ],
                "emails": [
                    {
                        "label": "work",
                        "address": "maria.schmidt@innovationlabs.de",
                        "is_primary": True
                    }
                ],
                "website": "https://innovationlabs.de",
                "is_public": True,
                "background_color": "#ffffff",
                "text_color": "#1f2937",
                "accent_color": "#3b82f6"
            }
            
            response = requests.post(f"{API_BASE}/cards", json=card_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.card_id = data["id"]
                self.log_result("Create Test Business Card", True, f"Test card created: {data['name']}")
                return True
            else:
                self.log_result("Create Test Business Card", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Test Business Card", False, f"Error: {str(e)}")
            return False
    
    def test_scanner_upload_endpoint(self):
        """Test 3: Scanner upload endpoint"""
        if not self.access_token:
            self.log_result("Scanner Upload Endpoint", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create a simple test image (1x1 pixel PNG)
            test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            scan_request = {
                "image_data": test_image_b64,
                "scan_method": "camera"
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "scan_id" in data:
                    self.scan_id = data["scan_id"]
                    self.log_result("Scanner Upload Endpoint", True, f"Scanner upload successful - scan_id: {self.scan_id}")
                    return True
                else:
                    self.log_result("Scanner Upload Endpoint", False, "Missing scan_id in response", data)
                    return False
            else:
                self.log_result("Scanner Upload Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Scanner Upload Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_scanner_conversion_workflow(self):
        """Test 4: Complete Scanner Workflow - Upload → Convert → Contact List"""
        if not self.access_token or not hasattr(self, 'scan_id'):
            self.log_result("Scanner Conversion Workflow", False, "No access token or scan_id available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Step 1: Check scan results
            response = requests.get(f"{API_BASE}/scanner/scan/{self.scan_id}", headers=headers)
            
            if response.status_code != 200:
                self.log_result("Scanner Conversion Workflow - Get Results", False, f"HTTP {response.status_code}", response.text)
                return False
            
            scan_data = response.json()
            self.log_result("Scanner Conversion Workflow - Get Results", True, f"Scan results retrieved: {scan_data.get('status', 'unknown')}")
            
            # Step 2: Convert scan to business card
            convert_request = {
                "name": "Scanned Contact",
                "company": "Scanned Company",
                "position": "Scanned Position",
                "phones": [
                    {
                        "label": "work",
                        "number": "+49-30-123-4567",
                        "is_primary": True
                    }
                ],
                "emails": [
                    {
                        "label": "work",
                        "address": "scanned@example.com",
                        "is_primary": True
                    }
                ],
                "is_public": True
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan/{self.scan_id}/convert", json=convert_request, headers=headers)
            
            if response.status_code == 200:
                converted_card = response.json()
                self.converted_card_id = converted_card["id"]
                self.log_result("Scanner Conversion Workflow - Convert", True, f"Scan converted to card: {converted_card['name']}")
                
                # Step 3: Verify card appears in contact list
                response = requests.get(f"{API_BASE}/cards", headers=headers)
                
                if response.status_code == 200:
                    cards = response.json()
                    converted_card_found = any(card["id"] == self.converted_card_id for card in cards)
                    
                    if converted_card_found:
                        self.log_result("Scanner Conversion Workflow - Contact List Integration", True, f"Converted card appears in contact list ({len(cards)} total cards)")
                        return True
                    else:
                        self.log_result("Scanner Conversion Workflow - Contact List Integration", False, f"Converted card NOT found in contact list (searched {len(cards)} cards)")
                        return False
                else:
                    self.log_result("Scanner Conversion Workflow - Contact List Integration", False, f"Failed to get cards: HTTP {response.status_code}")
                    return False
            else:
                self.log_result("Scanner Conversion Workflow - Convert", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Scanner Conversion Workflow", False, f"Error: {str(e)}")
            return False
    
    def test_scanner_list_endpoint(self):
        """Test 5: Scanner list endpoint"""
        if not self.access_token:
            self.log_result("Scanner List Endpoint", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{API_BASE}/scanner/scans", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "scans" in data:
                    scans = data["scans"]
                    self.log_result("Scanner List Endpoint", True, f"Scanner list accessible - {len(scans)} scans found")
                    return True
                else:
                    self.log_result("Scanner List Endpoint", False, "Missing 'scans' field in response", data)
                    return False
            else:
                self.log_result("Scanner List Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Scanner List Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_end_to_end_user_workflow(self):
        """Test 6: Complete end-to-end user workflow"""
        if not self.access_token:
            self.log_result("End-to-End User Workflow", False, "No access token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Simulate complete user workflow:
            # 1. User takes photo of business card
            # 2. Upload for OCR processing
            # 3. Review and convert to digital card
            # 4. Card appears in their contact list
            # 5. User can view and edit the card
            
            # Step 1 & 2: Upload business card image
            test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            scan_request = {
                "image_data": test_image_b64,
                "scan_method": "camera"
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan", json=scan_request, headers=headers)
            
            if response.status_code != 200:
                self.log_result("End-to-End User Workflow - Upload", False, f"Upload failed: HTTP {response.status_code}")
                return False
            
            scan_data = response.json()
            workflow_scan_id = scan_data["scan_id"]
            
            # Step 3: Convert to digital card with realistic data
            convert_request = {
                "name": "Alexander Müller",
                "company": "TechStart Berlin GmbH",
                "position": "Senior Software Engineer",
                "description": "Full-stack developer specializing in React and Node.js",
                "phones": [
                    {
                        "label": "work",
                        "number": "+49-30-987-6543",
                        "is_primary": True
                    },
                    {
                        "label": "mobile", 
                        "number": "+49-172-987-6543",
                        "is_primary": False
                    }
                ],
                "emails": [
                    {
                        "label": "work",
                        "address": "alexander.mueller@techstart-berlin.de",
                        "is_primary": True
                    }
                ],
                "website": "https://techstart-berlin.de",
                "is_public": True,
                "background_color": "#f8fafc",
                "text_color": "#1e293b",
                "accent_color": "#0ea5e9"
            }
            
            response = requests.post(f"{API_BASE}/scanner/scan/{workflow_scan_id}/convert", json=convert_request, headers=headers)
            
            if response.status_code != 200:
                self.log_result("End-to-End User Workflow - Convert", False, f"Convert failed: HTTP {response.status_code}")
                return False
            
            converted_card = response.json()
            workflow_card_id = converted_card["id"]
            
            # Step 4: Verify card appears in contact list
            response = requests.get(f"{API_BASE}/cards", headers=headers)
            
            if response.status_code != 200:
                self.log_result("End-to-End User Workflow - Contact List", False, f"Get cards failed: HTTP {response.status_code}")
                return False
            
            cards = response.json()
            card_found = any(card["id"] == workflow_card_id for card in cards)
            
            if not card_found:
                self.log_result("End-to-End User Workflow - Contact List", False, "Scanned card not found in contact list")
                return False
            
            # Step 5: Verify user can view the card
            response = requests.get(f"{API_BASE}/cards/{workflow_card_id}", headers=headers)
            
            if response.status_code != 200:
                self.log_result("End-to-End User Workflow - View Card", False, f"View card failed: HTTP {response.status_code}")
                return False
            
            card_details = response.json()
            
            # Verify all data is preserved
            if (card_details.get("name") == convert_request["name"] and 
                card_details.get("company") == convert_request["company"] and
                len(card_details.get("phones", [])) == 2 and
                len(card_details.get("emails", [])) == 1):
                
                self.log_result("End-to-End User Workflow", True, f"Complete workflow successful: {card_details['name']} from {card_details['company']}")
                return True
            else:
                self.log_result("End-to-End User Workflow - Data Integrity", False, "Card data not properly preserved")
                return False
                
        except Exception as e:
            self.log_result("End-to-End User Workflow", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all scanner workflow tests"""
        print("=" * 80)
        print("🔍 BUSINESS CARD SCANNER WORKFLOW TEST - CRITICAL FIX VALIDATION")
        print("=" * 80)
        print(f"Testing API at: {API_BASE}")
        print("🎯 PRIORITY: Verify complete scanner workflow with corrected API configuration")
        print()
        
        tests = [
            self.test_api_connectivity,
            self.test_authentication_setup,
            self.test_get_cards_endpoint,
            self.test_create_business_card,
            self.test_scanner_upload_endpoint,
            self.test_scanner_conversion_workflow,
            self.test_scanner_list_endpoint,
            self.test_end_to_end_user_workflow
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED - Scanner workflow is working correctly!")
        else:
            print(f"\n⚠️  {total - passed} tests failed - Issues need to be addressed")
        
        return passed == total

if __name__ == "__main__":
    tester = ScannerWorkflowTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)